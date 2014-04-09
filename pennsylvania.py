#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import urllib
import logging
import webapp2
import datetime

from webapp2_extras.routes import RedirectRoute
from webapp2_extras import jinja2

from models import Locale, Page, Menu, Picture
from admin import *
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.api import memcache

HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"

def jinja2_factory(app):
	j = jinja2.Jinja2(app)
	j.environment.filters.update({
        #'naturaldelta':naturaldelta,
        })
	j.environment.globals.update({
        # 'Post': Post,
        #'ndb': ndb, # could be used for ndb.OR in templates
        })
	return j

class BaseHandler(webapp2.RequestHandler):
	@webapp2.cached_property
	def jinja2(self):
	# Returns a Jinja2 renderer cached in the app registry.
		return jinja2.get_jinja2(factory=jinja2_factory)

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
	def render_error(self, message):
		logging.exception("Error 500: {0}".format(message))
		self.response.write("Error 500: {0}".format(message))
		return self.response.set_status(500)		



class MainPage(BaseHandler):
	def get(self):
		page = Page.query(Page.locale==ndb.Key(Locale, "fr"), Page.menu==ndb.Key(Menu, "the-manor")).fetch()
		self.redirect('/{0}/{1}'.format("fr", page[0].key.id()))

class LocaleViewer(BaseHandler):
	def get(self, locale_id):
		page = Page.query(Page.locale==ndb.Key(Locale, locale_id), Page.menu==ndb.Key(Menu, "the-manor")).fetch()
		self.redirect('/{0}/{1}'.format(locale_id, page[0].key.id()))

class ModelViewer(BaseHandler):
	def get(self, locale_id, page_id):

		## Menus
		menus = self.get_menus()
		for menu in menus:
			localized_page = Page.query(Page.locale==ndb.Key(Locale, locale_id), Page.menu==ndb.Key(Menu, menu.key.id())).fetch()
			if len(localized_page) == 0:
				return self.render_error("locale \"{0}\" is not available for menu \"{1}\"".format(locale_id, menu.key.id()))

			# enhance with submenu id and name, easier to render
			menu.page = localized_page[0]
			if (menu.submenus):
				menu.submenus_enhanced = []
				for submenu in menu.submenus:
					localized_page = Page.query(Page.locale==ndb.Key(Locale, locale_id), Page.menu==submenu).fetch()
					my_dict = dict()
					my_dict['id'] =  localized_page[0].key.id()
					my_dict['name'] =  localized_page[0].name
					menu.submenus_enhanced.append(my_dict)

		## Dict for current locale
		localedicts = self.get_dict(locale_id)
		dictionary = dict()
		for localedict in localedicts:
			dictionary[localedict.name] = localedict.value

		## Page
		page = self.get_page_by_id(page_id)

		if page is None:
			return self.render_error("\"{0}\" returned None object".format(page_id))

		pages = self.get_pages(locale_id)
		if not pages:
			return self.render_error("Error 500: cannot build pages List")

		## Locale
		locales = self.get_locales()

		# enhance locales object with each localized page id for smooth transfert
		for locale in locales:
			this_locale = ndb.Key(Locale, locale.key.id())
			this_menu = ndb.Key(Menu, page.menu.id())
			localized_page = Page.query(Page.locale==this_locale, Page.menu==this_menu).fetch()
			if len(localized_page):
				locale.page = localized_page[0]
			else: #else default to english
				this_locale = ndb.Key(Locale, "en")
				localized_page = Page.query(Page.locale==this_locale, Page.menu==this_menu).fetch()
				locale.page = localized_page[0]

		template_values = {
			'page': page,
			'locale_id': locale_id,
			'menus': menus,
			'pages': pages,
			'locales': locales,
			'dictionary' : dictionary,
		}	
		return self.render_response('page.html', **template_values)

	def get_dict(self, locale_id):
		localedict = memcache.get('localedict {0}'.format(locale_id))
		if localedict is None:
			localedict = LocaleDict.query(LocaleDict.locale==ndb.Key(Locale, locale_id)).fetch()
			memcache.set(key='localedict {0}'.format(locale_id), value=localedict)
		return localedict

	def get_menus(self):
		menus = memcache.get('menus')
		if menus is None:
			menus = Menu.query().order(Menu.order).fetch()
			memcache.set(key="menus", value=menus)
		return menus

	def get_pages(self, locale_id):
		pages = memcache.get("pages {0}".format(locale_id))
		if pages is None:
			pages = Page.query(Page.locale==ndb.Key(Locale, locale_id)).fetch()
			if not pages:
				return None
			memcache.set(key="pages {0}".format(locale_id), value=pages)
		return pages					
		
	def get_page_by_id(self, page_id):
		page = memcache.get("{0}".format(page_id))
		if page is None:
			page = Page.get_by_id(page_id)
			memcache.set(key="{0}".format(page_id), value=page)
		return page				
	
	def get_locales(self):
		locales = memcache.get('locales')
		if locales is None:
			locales = Locale.query().fetch()
			memcache.set(key="locales", value=locales)
		return locales

class MailSender(BaseHandler):
	def post(self, locale_id, page_id):
		if not mail.is_email_valid(self.request.get('email')):
			return self.redirect('/{0}/{1}#myModal'.format(locale_id, page_id))

		mail.send_mail(sender="Manoir De Juganville <manoirjuganville@gmail.com>",
              to="Manoir De Juganville <manoirjuganville@gmail.com>",
              subject="Booking from juganville.com",
              cc=self.request.get('email'),
              body="""
email from: {3}
{2}

locale: {0}
page: {1}
				""".format(locale_id, page_id, self.request.get('message'), self.request.get('email')))
		self.redirect('/{0}/{1}'.format(locale_id, page_id))

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def output(self, resource, serve):
		try:

			logging.debug("ServeHandler resource: %s", resource)
			resource = str(urllib.unquote(resource))
			blob_info = blobstore.BlobInfo.get(resource)
			self.response.headers['Cache-Control'] = 'public,max-age=31104000'
			self.response.headers['Last-Modified'] = 'Thu, 15 Apr 2013 20:00:00 GMT'
			self.response.headers['Expires'] = 'Thu, 15 Apr 2015 20:00:00 GMT'
			self.response.headers['Pragma'] = 'Public'
			self.response.md5_etag()
			if serve:
				self.send_blob(blob_info)
			else:
				self.response.set_status(304)
		except (ValueError, TypeError):
			self.response.out.write("bug")
	def get(self, resource):
		serve = True
		if 'If-Modified-Since' in self.request.headers:
			# last_seen = datetime.datetime.strptime(self.request.headers['If-Modified-Since'], HTTP_DATE_FMT)
			# if last_seen >= content.last_modified.replace(microsecond=0):
			serve = False
		if 'If-None-Match' in self.request.headers:
			# etags = [x.strip('" ')
			# for x in self.request.headers['If-None-Match'].split(',')]
			# if content.etag in etags:
			serve = False
		self.output(resource, serve)



application = webapp2.WSGIApplication([
	webapp2.Route(r'/serve/<:([^/]+)?>', ServeHandler, name='ServeHandler'),
    webapp2.Route(r'/admin', AdminMain),
    webapp2.Route(r'/admin/locale/new', AdminNewLocale),
	webapp2.Route(r'/admin/menu/new', AdminNewMenu),
	webapp2.Route(r'/admin/submenu/new', AdminNewSubMenu),
	webapp2.Route(r'/admin/localedict/new', AdminNewLocaleDict),
	webapp2.Route(r'/admin/localedict/<localedict_id:([^/]+)?>/update', AdminUpdateLocaleDict),
	webapp2.Route(r'/admin/localedict/<localedict_id:([^/]+)?>/delete', AdminDeleteLocaleDict),
	webapp2.Route(r'/admin/page/new', AdminNewPage),
	webapp2.Route(r'/admin/page/<page_id:([^/]+)?>', AdminViewPage),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/update', AdminUpdatePage),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/delete', AdminPageDelete),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/add_block', AdminPageAddBlock),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/<block_id:([^/]+)?>/moveup', AdminBlockMoveUp),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/<block_id:([^/]+)?>/delete', AdminBlockDelete),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/block/<block_id:([^/]+)?>/price/new', AdminBlockPriceNew),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/block/<block_id:([^/]+)?>/price/<price_id:([^/]+)?>/delete', AdminBlockPriceDelete),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/block/<block_id:([^/]+)?>/price/<price_id:([^/]+)?>/moveup', AdminBlockPriceMoveUp),
    webapp2.Route(r'/admin/picture/<picture_id:([^/]+)?>/delete', AdminPictureDelete),
    webapp2.Route(r'/admin/picture/<picture_id:([^/]+)?>/update', AdminPictureUpdate),
    webapp2.Route(r'/admin/block/<block_id:([^/]+)?>/update', AdminBlockUpdate),
    webapp2.Route(r'/admin/block/<block_id:([^/]+)?>/picture/<picture_id:([^/]+)?>/delete', AdminBlockPictureDelete),
    webapp2.Route(r'/admin/<locale_id:([^/]+)?>', AdminViewLocale),
	webapp2.Route(r'/upload', AdminUploadHandler),
    webapp2.Route(r'/', MainPage),
    webapp2.Route(r'/<locale_id:([^/]+)?>/<page_id:([^/]+)?>', ModelViewer),
    webapp2.Route(r'/<locale_id:([^/]+)?>', LocaleViewer),
	webapp2.Route(r'/<locale_id:([^/]+)?>/<page_id:([^/]+)?>/email', MailSender),

	], debug=True)