#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import urllib
import logging
import webapp2

from webapp2_extras.routes import RedirectRoute
from webapp2_extras import jinja2
from functools import wraps
from models import Locale, Page, Menu, pagination_choice, Picture, block_choice, Block, LocaleDict

from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import memcache

def jinja2_factory(app):
	j = jinja2.Jinja2(app)
	j.environment.filters.update({
        #'naturaldelta':naturaldelta,
        })
	j.environment.globals.update({
        'Locale': Locale,
        #'ndb': ndb, # could be used for ndb.OR in templates
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
	# 	# Log the error.
	# 	logging.exception(exception)
	# 	# Set a custom message.
	# 	self.response.write("An error occurred.")
	# 	# If the exception is a HTTPException, use its error code.
	# 	# Otherwise use a generic 500 error code.
	# 	if isinstance(exception, webapp2.HTTPException):
	# 		self.response.set_status(exception.code)
	# 	else:
	# 		self.response.set_status(500)
	def picture_delete(self, picture_id):
		pic = ndb.Key(Picture, int(picture_id))
		blob_info = blobstore.BlobInfo.get(pic.get().size_max)
		blob_info.delete()
		pic.delete()

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

		template_values = {
			'url': users.create_logout_url(self.request.uri),
			'url_linktext': 'Logout',
			'user': users.get_current_user(),
			'locales': locales,
			'menus': menus,
			'pages': pages,
			'menu_list': menu_list,
			'localedicts' : localedicts,
			'locale_list': locale_list,
		}	
		return self.render_response('admin_main.html', **template_values)

class AdminNewLocaleDict(AdminBaseHandler):
	def post(self):
		localedict = LocaleDict(locale=ndb.Key(Locale, self.request.get('locale_id')),
								name=self.request.get('name'),
								value=self.request.get('value'))
		localedict.put()
		memcache.flush_all()
		return self.redirect('/admin')


class AdminUpdateLocaleDict(AdminBaseHandler):
	def post(self, localedict_id):
		localedict = LocaleDict.get_by_id(int(localedict_id))
		localedict.name = self.request.get('name')
		localedict.value = self.request.get('value')
		localedict.put()
		memcache.flush_all()
		return self.redirect('/admin')

class AdminDeleteLocaleDict(AdminBaseHandler):
	def get(self, localedict_id):
		ndb.Key(LocaleDict, int(localedict_id)).delete()
		memcache.flush_all()
		return self.redirect('/admin')

class AdminNewLocale(AdminBaseHandler):
	def post(self):
		locale = Locale(id=self.request.get('locale_id'),
						name=self.request.get('name'))
		locale.put()
		return self.redirect('/admin')

class AdminNewMenu(AdminBaseHandler):
	def post(self):
		menu = Menu(id=self.request.get('menu_id'))
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

class AdminNewPage(AdminBaseHandler):
	def get(self):
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
			'action': '/admin/page/new',
			'action_label': 'New',
			'pagination_choice': pagination_choice,
		}	
		return self.render_response('admin_page_new.html', **template_values)

	def post(self):
		logging.info(self.request.get('locale_id'))
		logging.info(self.request.get('menu_id'))
		logging.info(self.request.get('page_id'))
		logging.info(self.request.get('name'))
		page = Page(id=self.request.get('page_id'), 
					name = self.request.get('name'),
					locale = ndb.Key(Locale, self.request.get('locale_id')),
					menu = ndb.Key(Menu, self.request.get('menu_id')),
					creation_author = users.get_current_user())
		page.put()
		return self.redirect('/admin')

class AdminUpdatePage(AdminBaseHandler):
	def post(self, page_id):

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

class AdminPageDelete(AdminBaseHandler):
	def get(self, page_id):
		ndb.Key(Page, page_id).delete()
		memcache.flush_all()
		return self.redirect('/admin')

class AdminPageAddBlock(AdminBaseHandler):
	def get(self, page_id):
		block = Block()
		block.put()
		page = Page.get_by_id(page_id)
		#del page.blocks[0:len(page.blocks)]
		page.blocks.append(ndb.Key(Block, block.key.id()))
		page.modification_author = users.get_current_user()
		page.put()
		memcache.flush_all()
		return self.redirect('/admin/page/{0}'.format(unicode(page_id)))

class AdminBlockMoveUp(AdminBaseHandler):
	def get(self, page_id, block_id):

		page = Page.get_by_id(page_id)

		logging.info(page.blocks)


		a = page.blocks.index(ndb.Key(Block, int(block_id)))

		page.blocks[a-1], page.blocks[a] =  page.blocks[a],  page.blocks[a-1]
		logging.info( page.blocks)

		page.modification_author = users.get_current_user()
		page.put()
		memcache.flush_all()
		return self.redirect('/admin/page/{0}'.format(unicode(page_id)))
		

class AdminBlockUpdate(AdminBaseHandler):
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

class AdminBlockDelete(AdminBaseHandler):
	def get(self, page_id, block_id):
		block = ndb.Key(Block, int(block_id))
		page = Page.get_by_id(page_id)
		page.blocks.remove(block)
		page.put()
		block.delete()
		memcache.flush_all()
		return self.redirect('/admin/page/{0}'.format(unicode(page_id)))


class AdminBlockPictureDelete(AdminBaseHandler):
	def get(self, block_id, picture_id):
		block = Block.get_by_id(int(block_id))
		
		block.picture = None
		block.put()

		self.picture_delete(picture_id)
		memcache.flush_all()
		return self.redirect(self.request.get('return-to'))


class AdminPictureDelete(AdminBaseHandler):
	def get(self, picture_id):
		page = Page.get_by_id(self.request.get('page_id'))
		pic = ndb.Key(Picture, int(picture_id))
		page.backgrounds.remove(pic)
		page.modification_author = users.get_current_user()
		page.put()
		self.picture_delete(picture_id)
		memcache.flush_all()
		return self.redirect('/admin/page/{0}'.format(self.request.get('page_id')))

class AdminPictureUpdate(AdminBaseHandler):
	def post(self, picture_id):
		pic = Picture.get_by_id(int(picture_id))
		pic.caption = self.request.get('caption')
		pic.put()

		page = Page.get_by_id(unicode(self.request.get('page_id')))
		page.modification_author = users.get_current_user()
		page.put()

		memcache.flush_all()
		return self.redirect('/admin/page/{0}'.format(self.request.get('page_id')))


class AdminViewLocale(AdminBaseHandler):
	def get(self, locale_id):

		page_query = Page.query(Page.locale==ndb.Key(Locale, locale_id))
		pages = page_query.fetch()

		template_values = {
			'url': users.create_logout_url(self.request.uri),
			'url_linktext': 'Logout',
			'user': users.get_current_user(),
			'pages': pages,
			'locale': locale_id,
		}	
		return self.render_response('admin_view_pages.html', **template_values)

class AdminViewPage(AdminBaseHandler):
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
			'action': '/admin/page/{0}/update'.format(page_id),
			'action_label': 'Update',
			'upload_url': blobstore.create_upload_url('/upload'),
			'pagination_choice': pagination_choice,
			'block_choice': block_choice,
		}	
		return self.render_response('admin_page_new.html', **template_values)



class AdminUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	@admin_protect
	def post(self):



		upload_files = self.get_uploads('picture')
		blob_info = upload_files[0]

		pic = Picture(size_max=blob_info.key())
		pic.put()

		if (self.request.get('page_id')):
			page = Page.get_by_id(self.request.get('page_id'))
			page.backgrounds.append(ndb.Key(Picture, pic.key.id()))
			page.put()
		if (self.request.get('block_id')):
			block = Block.get_by_id(int(self.request.get('block_id')))
			block.picture = ndb.Key(Picture, pic.key.id())
			block.put()

		memcache.flush_all()

		self.redirect(self.request.get('return-to'))


