import os
import urllib
import logging
import webapp2

from webapp2_extras.routes import RedirectRoute
from webapp2_extras import jinja2

from models import Locale, Page, Menu
from admin import *
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.api import memcache

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


class MainPage(BaseHandler):
	def get(self):
		page = Page.query(Page.locale==ndb.Key(Locale, "en"), Page.menu==ndb.Key(Menu, "the-manor")).fetch()
		self.redirect('/{0}/{1}'.format("en", page[0].key.id()))

class LocaleViewer(BaseHandler):
	def get(self, locale_id):
		page = Page.query(Page.locale==ndb.Key(Locale, locale_id), Page.menu==ndb.Key(Menu, "the-manor")).fetch()
		self.redirect('/{0}/{1}'.format(locale_id, page[0].key.id()))

class ModelViewer(BaseHandler):
	def get(self, locale_id, page_id):

		menus = self.get_menus()
		for menu in menus:
			localized_page = Page.query(Page.locale==ndb.Key(Locale, locale_id), Page.menu==ndb.Key(Menu, menu.key.id())).fetch()
			menu.page = localized_page[0]
			if (menu.submenus):
				menu.submenus_enhanced = []
				for submenu in menu.submenus:
					localized_page = Page.query(Page.locale==ndb.Key(Locale, locale_id), Page.menu==submenu).fetch()
					my_dict = dict()
					my_dict['id'] =  localized_page[0].key.id()
					my_dict['name'] =  localized_page[0].name
					menu.submenus_enhanced.append(my_dict)

		page = self.get_page_by_id(page_id)

		pages = self.get_pages(locale_id)
		locales = self.get_locales()

		# enriched locales with each localized page id for smooth transfert
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
		}	
		return self.render_response('page.html', **template_values)

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
		if menus is None:
			locales = Locale.query().fetch()
			memcache.set(key="locales", value=locales)
		return locales

class MailSender(BaseHandler):
	def post(self, locale_id, page_id):
		if not mail.is_email_valid(self.request.get('email')):
			return self.redirect('/{0}/{1}#myModal'.format(locale_id, page_id))

		mail.send_mail(sender="Manoir De Juganville <manoirjuganville@gmail.com>",
              to="Manoir De Juganville <cyril.jean@gmail.com>",
              subject="Booking from juganville.com",
              cc=self.request.get('email'),
              body="""
mail from: {3}
{2}

locale: {0}
page: {1}
				""".format(locale_id, page_id, self.request.get('message'), self.request.get('email')))
		self.redirect('/{0}/{1}'.format(locale_id, page_id))

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, resource):
		try:
			logging.info("ServeHandler resource: %s", resource)
			resource = str(urllib.unquote(resource))
			blob_info = blobstore.BlobInfo.get(resource)
			self.response.headers['Cache-Control'] = 'public,max-age=86400'
			self.response.headers['Pragma'] = 'Public'
			self.send_blob(blob_info)
		except (ValueError, TypeError):
			self.response.out.write("bug")


application = webapp2.WSGIApplication([
	webapp2.Route(r'/serve/<:([^/]+)?>', ServeHandler, name='ServeHandler'),
    webapp2.Route(r'/admin', AdminMain),
    webapp2.Route(r'/admin/locale/new', AdminNewLocale),
	webapp2.Route(r'/admin/menu/new', AdminNewMenu),
	webapp2.Route(r'/admin/submenu/new', AdminNewSubMenu),
	webapp2.Route(r'/admin/page/new', AdminNewPage),
	webapp2.Route(r'/admin/page/<page_id:([^/]+)?>', AdminViewPage),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/update', AdminUpdatePage),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/delete', AdminPageDelete),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/<blobstore_key:([^/]+)?>/delete', AdminPageDeleteBackground),
    webapp2.Route(r'/admin/<locale_id:([^/]+)?>', AdminViewLocale),
	webapp2.Route(r'/upload', AdminUploadHandler),
    webapp2.Route(r'/', MainPage),
    webapp2.Route(r'/<locale_id:([^/]+)?>/<page_id:([^/]+)?>', ModelViewer),
    webapp2.Route(r'/<locale_id:([^/]+)?>', LocaleViewer),
	webapp2.Route(r'/<locale_id:([^/]+)?>/<page_id:([^/]+)?>/email', MailSender),

	], debug=True)