#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import urllib
import logging
import webapp2

from webapp2_extras.routes import RedirectRoute
from webapp2_extras import jinja2
from functools import wraps
from models import Locale, Page, Menu, pagination_choice, Picture, block_choice, Block, LocaleDict, Price, HeadsUp, kind_choice

from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import memcache
from operator import itemgetter


def jinja2_factory(app):
    j = jinja2.Jinja2(app)
    j.environment.filters.update({
        # 'naturaldelta':naturaldelta,
    })
    j.environment.globals.update({
        'Locale': Locale,

        # 'ndb': ndb, # could be used for ndb.OR in templates
    })
    return j


def admin_protect(f):
    @wraps(f)
    def decorated_function(self, *args, **kwargs):
        user = users.get_current_user()
        if not user or not users.is_current_user_admin():
            return self.redirect(users.create_login_url(self.request.uri))
        return f(self, *args, **kwargs)
    return decorated_function


class AdminBaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(factory=jinja2_factory)

    @admin_protect
    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)
    # def handle_exception(self, exception, debug):
    #     # Log the error.
    #     logging.exception(exception)
    #     # Set a custom message.
    #     self.response.write("An error occurred.")
    #     # If the exception is a HTTPException, use its error code.
    #     # Otherwise use a generic 500 error code.
    #     if isinstance(exception, webapp2.HTTPException):
    #         self.response.set_status(exception.code)
    #     else:
    #         self.response.set_status(500)

    def picture_delete(self, picture_id):
        pic = ndb.Key(Picture, int(picture_id))
        blob_info = blobstore.BlobInfo.get(pic.get().size_max)
        blob_info.delete()
        pic.delete()


class PictureEntity():
    def __init__(self, picture_id=None):
        if not picture_id:
            picture = Block()
            picture.put()
            self._picture = picture
            return
        picture = Picture.get_by_id(int(picture_id))
        if not picture:
            raise Exception(404, "Missing picture_id {0}".format(picture_id))
        self._picture = picture

    def key(self):
        return ndb.Key(Picture, int(self._picture.key.id()))

    def delete(self):
        self.key().delete()


class PictureHandler(AdminBaseHandler):
    def delete(self, picture_id):
        logging.info("Delete picture_id {0}".format(picture_id))
        picture = PictureEntity(picture_id)

        blob_info = blobstore.BlobInfo.get(picture.key().get().size_max)
        blob_info.delete()
        picture.delete()

    def update(self, picture_id):
        pic = Picture.get_by_id(int(picture_id))
        if self.request.get('caption'):
            pic.caption = self.request.get('caption')
        if self.request.get('name'):
            pic.name = self.request.get('name')
        pic.put()

        if self.request.get('page_id'):
            page = Page.get_by_id(unicode(self.request.get('page_id')))
            page.modification_author = users.get_current_user()
            page.put()

        memcache.flush_all()
        if self.request.get('page_id'):
            return self.redirect('/admin/page/{0}'.format(self.request.get('page_id')))
        return self.redirect('/admin')


class BlockEntity():
    def __init__(self, block_id=None):
        logging.info("BlockEntity block_id {0}".format(block_id))
        if not block_id:
            block = Block()
            block.put()
            self._block = block
            return
        block = Block.get_by_id(int(block_id))
        if not block:
            raise Exception(404, "Missing block_id {0}".format(block_id))
        self._block = block

    def key(self):
        return ndb.Key(Block, int(self._block.key.id()))

    def delete(self):
        block = self.key().get()
        for background in block.backgrounds:
            self.deleteBackground(background.get().key.id())
        if block.picture:
            self.deletePicture(block.picture.get().key.id())
        self.key().delete()

    def deletePicture(self, picture_id):
        block = self.key().get()
        block.picture = None
        block.put()
        picture = PictureEntity(picture_id)
        picture.delete()

    def deleteBackground(self, picture_id):
        picture = PictureEntity(picture_id)
        block = self.key().get()
        block.backgrounds.remove(picture.key())
        block.put()
        picture.delete()


class BlockHandler(AdminBaseHandler):
    def updateModif(self, page_id):
        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()

    def deletePicture(self, page_id, block_id, picture_id):
        try:
            block = BlockEntity(block_id)
            block.deletePicture(picture_id)
            pass
        except Exception as identifier:
            return self.abort(404, identifier)
            pass

        self.updateModif(page_id)
        memcache.flush_all()
        return self.redirect(self.request.get('return-to'))

    def deleteBackground(self, page_id, block_id, picture_id):
        try:
            block = BlockEntity(block_id)
            block.deleteBackground(picture_id)
            pass
        except Exception as identifier:
            return self.abort(404, identifier)
            pass
        self.updateModif(page_id)
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))

    def post(self, block_id):

        block = Block.get_by_id(int(block_id))
        block.title = self.request.get('title')
        block.subtitle = self.request.get('subtitle')
        block.content = self.request.get('content')
        block.widget = self.request.get('widget')
        block.widget_script = self.request.get('widget_script')
        block.pagination = self.request.get('pagination')
        block.put()

        page = Page.get_by_id(unicode(self.request.get('page_id')))
        page.modification_author = users.get_current_user()
        page.put()

        memcache.flush_all()

        return self.redirect('/admin/page/{0}'.format(unicode(self.request.get('page_id'))))


class PageHandler(AdminBaseHandler):
    def updateModif(selft, page_id):
        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()

    def deleteBlock(self, page_id, block_id):
        page = Page.get_by_id(page_id)
        block = BlockEntity(block_id)
        page.blocks.remove(block.key())
        page.put()

        block.delete()
        self.updateModif(page_id)

        return self.redirect('/admin/page/{0}'.format(unicode(page_id)))

    def moveUpBlock(self, page_id, block_id):
        page = Page.get_by_id(page_id)
        logging.info(page.blocks)
        a = page.blocks.index(ndb.Key(Block, int(block_id)))
        page.blocks[a-1], page.blocks[a] = page.blocks[a],  page.blocks[a-1]
        logging.info(page.blocks)

        page.modification_author = users.get_current_user()
        page.put()
        self.updateModif(page_id)
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(unicode(page_id)))

    def delete(self, page_id):
        page = Page.get_by_id(page_id)
        for block in page.blocks:
            try:
                _block = BlockEntity(block.id())
                _block.delete()
                pass
            except Exception as identifier:
                logging.critical(identifier)
                pass
        page.key.delete()
        memcache.flush_all()
        return self.redirect('/admin')

    def get(self, page_id):

        page = Page.get_by_id(page_id)
        locales = Locale.query().fetch()
        locale_list = []
        for locale in locales:
            locale_list.append(locale.key.id())

        menus = Menu.query().fetch()
        menu_list = []
        for menu in menus:
            menu_list.append(menu.key.id())

        template_values = {
            'url': users.create_logout_url(self.request.uri),
            'url_linktext': 'Logout',
            'user': users.get_current_user(),
            'page': page,
            'locale_list': locale_list,
            'menu_list': menu_list,
            'action': '/admin/page/{0}'.format(page_id),
            'action_label': 'Update',
            'upload_url': blobstore.create_upload_url('/upload'),
            'pagination_choice': pagination_choice,
            'block_choice': block_choice,
            'method': 'post',
        }
        return self.render_response('admin_page_new.html', **template_values)

    def getNew(self):
        locales = Locale.query().fetch()
        locale_list = []
        for locale in locales:
            locale_list.append(locale.key.id())

        menus = Menu.query().fetch()
        menu_list = []
        for menu in menus:
            menu_list.append(menu.key.id())

        template_values = {
            'locale_list': locale_list,
            'menu_list': menu_list,
            'action': '/admin/page',
            'action_label': 'New',
            'pagination_choice': pagination_choice,
            'method': 'post',
        }
        return self.render_response('admin_page_new.html', **template_values)

    def post(self):
        logging.info(self.request.get('locale_id'))
        logging.info(self.request.get('menu_id'))
        logging.info(self.request.get('page_id'))
        logging.info(self.request.get('name'))
        s = self.request.get('page_id')
        logging.info(type(s))
        s.encode('utf-8')
        logging.info(type(s))
        # logging.info(self.request.get('page_id').encode('ascii').decode('utf-8'))
        page = Page(id=self.request.get('page_id'),
                    name=self.request.get('name'),
                    locale=ndb.Key(Locale, self.request.get('locale_id')),
                    menu=ndb.Key(Menu, self.request.get('menu_id')),
                    creation_author=users.get_current_user())
        page.modification_author = users.get_current_user()
        page.put()
        return self.redirect('/admin')

    def put(self, page_id):

        page = Page.get_by_id(page_id)
        page.id = self.request.get('page_id')
        page.menu = ndb.Key(Menu, self.request.get('menu_id'))
        page.name = self.request.get('name')
        page.locale = ndb.Key(Locale, self.request.get('locale_id'))
        page.title = self.request.get('title')
        page.description = self.request.get('description')
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(unicode(page_id)))

    def addBlock(self, page_id):
        block = BlockEntity()

        page = Page.get_by_id(page_id)
        page.blocks.append(block.key())
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(unicode(page_id)))


class AdminMain(AdminBaseHandler):
    def get(self):

        locale_query = Locale.query()
        locales = locale_query.fetch()
        locale_list = []
        for locale in locales:
            locale_list.append(locale.key.id())

        menu_query = Menu.query()
        menus = menu_query.fetch()

        menu_list = []
        for menu in menus:
            menu_list.append(menu.key.id())

        localedicts = LocaleDict.query().fetch()

        pages = Page.query().fetch()
        pages = sorted(pages, key=lambda k: "{0}{1}".format(k.menu, k.locale))

        for page in pages:
            logging.info(page.key.id())
            logging.info(page.key.urlsafe())
            logging.info(page.key.app())
            logging.info(type(page.key.id()))
            logging.info(type(page.key.string_id()))
            logging.info(page.name)
            logging.info(type(page.name))

        pictures = Picture.query().fetch()

        template_values = {
            'url': users.create_logout_url(self.request.uri),
            'url_linktext': 'Logout',
            'user': users.get_current_user(),
            'locales': locales,
            'menus': menus,
            'pages': pages,
            'menu_list': menu_list,
            'localedicts': localedicts,
            'locale_list': locale_list,
            'kind_choice': kind_choice,
            'pictures': pictures,
        }
        return self.render_response('admin_main.html', **template_values)


class LocaleDictHandler(AdminBaseHandler):
    def create(self):
        localedict = LocaleDict(locale=ndb.Key(Locale, self.request.get('locale_id')),
                                name=self.request.get('name'),
                                value=self.request.get('value'))
        localedict.put()
        memcache.flush_all()
        return self.redirect('/admin')

    def update(self, localedict_id):
        localedict = LocaleDict.get_by_id(int(localedict_id))
        localedict.name = self.request.get('name')
        localedict.value = self.request.get('value')
        localedict.put()
        memcache.flush_all()
        return self.redirect('/admin')

    def delete(self, localedict_id):
        ndb.Key(LocaleDict, int(localedict_id)).delete()
        memcache.flush_all()
        return self.redirect('/admin')


class LocaleHandler(AdminBaseHandler):
    def create(self):
        locale = Locale(id=self.request.get('locale_id'),
                        name=self.request.get('name'))
        locale.put()
        return self.redirect('/admin')

    def delete(self, locale_id):
        pages = Page.query().fetch()

        for page in pages:
            if page.locale == ndb.Key(Locale, locale_id):
                for block in page.blocks:
                    try:
                        _block = BlockEntity(block.id())
                        _block.delete()
                        pass
                    except Exception as identifier:
                        logging.critical(identifier)
                        pass
                page.key.delete()

        ndb.Key(Locale, locale_id).delete()
        memcache.flush_all()
        return self.redirect('/admin')

    def get(self, locale_id):

        page_query = Page.query(Page.locale == ndb.Key(Locale, locale_id))
        pages = page_query.fetch()

        template_values = {
            'url': users.create_logout_url(self.request.uri),
            'url_linktext': 'Logout',
            'user': users.get_current_user(),
            'pages': pages,
            'locale': locale_id,
        }
        return self.render_response('admin_view_pages.html', **template_values)


class AdminNewMenu(AdminBaseHandler):
    def post(self):
        menu = Menu(id=self.request.get('menu_id'))
        menu.kind = self.request.get('kind')
        menu.order = 1
        menu.put()
        return self.redirect('/admin')


class AdminNewSubMenu(AdminBaseHandler):
    def post(self):
        submenu = Menu(id=self.request.get('submenu_id'))
        submenu.order = 1
        submenu.parent = ndb.Key('Menu', self.request.get('menu_id'))
        submenu.put()
        menu = ndb.Key('Menu', self.request.get('menu_id')).get()
        menu.submenus.append(ndb.Key(Menu, self.request.get('submenu_id')))
        menu.put()
        return self.redirect('/admin')


class AdminBlockPriceNew(AdminBaseHandler):
    def post(self, page_id, block_id):
        price = Price()
        price.nb_guests = int(self.request.get('nb_guests'))
        price.price = self.request.get('price')
        price.put()

        block = Block.get_by_id(int(block_id))
        block.prices.append(ndb.Key(Price, price.key.id()))
        block.put()

        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))


class AdminBlockPriceDelete(AdminBaseHandler):
    def get(self, page_id, block_id, price_id):
        price_key = ndb.Key(Price, int(price_id))
        block = Block.get_by_id(int(block_id))

        block.prices.remove(price_key)
        block.put()

        price_key.delete()

        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))


class AdminBlockPriceMoveUp(AdminBaseHandler):
    def get(self, page_id, block_id, price_id):
        price = Price.get_by_id(int(price_id))
        block = Block.get_by_id(int(block_id))

        a = block.prices.index(ndb.Key(Price, int(price_id)))

        block.prices[a-1], block.prices[a] = block.prices[a],  block.prices[a-1]
        block.put()

        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))


class AdminBlockHeadsUpNew(AdminBaseHandler):
    def post(self, page_id, block_id):
        headsup = HeadsUp()
        headsup.title = self.request.get('title')
        headsup.content = self.request.get('content')
        headsup.menu = ndb.Key(Menu, self.request.get('menu_id'))
        headsup.put()

        block = Block.get_by_id(int(block_id))
        block.headsUps.append(ndb.Key(HeadsUp, headsup.key.id()))
        block.put()

        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))


class AdminBlockHeadsUpUpdate(AdminBaseHandler):
    def post(self, page_id, block_id, headsup_id):
        headsup = HeadsUp.get_by_id(int(headsup_id))
        headsup.title = self.request.get('title')
        headsup.content = self.request.get('content')
        headsup.menu = ndb.Key(Menu, self.request.get('menu_id'))
        headsup.put()

        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))


class AdminBlockHeadsUpDelete(AdminBaseHandler):
    def get(self, page_id, block_id, headsup_id):
        headsup = HeadsUp.get_by_id(int(headsup_id))
        headsup_key = ndb.Key(HeadsUp, int(headsup_id))
        block = Block.get_by_id(int(block_id))

        if headsup.picture is not None:
            self.picture_delete(headsup.picture.id)

        block.headsUps.remove(headsup_key)
        block.put()

        headsup_key.delete()

        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))


class AdminBlockHeadsUpMoveUp(AdminBaseHandler):
    def get(self, page_id, block_id, headsup_id):
        headsup = HeadsUp.get_by_id(int(headsup_id))
        block = Block.get_by_id(int(block_id))

        a = block.headsUps.index(ndb.Key(HeadsUp, int(headsup_id)))

        block.headsUps[a-1], block.headsUps[a] = block.headsUps[a],  block.headsUps[a-1]
        block.put()

        page = Page.get_by_id(page_id)
        page.modification_author = users.get_current_user()
        page.put()
        memcache.flush_all()
        return self.redirect('/admin/page/{0}'.format(page_id))


class AdminUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    @admin_protect
    def post(self):

        upload_files = self.get_uploads('picture')
        blob_info = upload_files[0]
        logging.info(blob_info.content_type)
        logging.info(blob_info.creation)
        logging.info(blob_info.filename)
        logging.info(blob_info.size)
        logging.info(blob_info.md5_hash)

        pic = Picture(size_max=blob_info.key())
        pic.put()

        if (self.request.get('action') == "PageBackground"):
            page = Page.get_by_id(self.request.get('page_id'))
            page.backgrounds.append(ndb.Key(Picture, pic.key.id()))
            page.put()
        if (self.request.get('action') == "BlockPicture"):
            block = Block.get_by_id(int(self.request.get('block_id')))
            block.picture = ndb.Key(Picture, pic.key.id())
            block.put()
        if (self.request.get('action') == "BlockBackground"):
            block = Block.get_by_id(int(self.request.get('block_id')))
            block.backgrounds.append(ndb.Key(Picture, pic.key.id()))
            block.put()
        if (self.request.get('action') == "HeadsUpPicture"):
            headsup = HeadsUp.get_by_id(int(self.request.get('headsup_id')))
            headsup.picture = ndb.Key(Picture, pic.key.id())
            headsup.put()
        memcache.flush_all()

        self.redirect(self.request.get('return-to'))
