import os
import urllib
import logging
import webapp2

from webapp2_extras.routes import RedirectRoute
from webapp2_extras import jinja2

from models import Locale, Page
from admin import *


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

class LaTour(webapp2.RequestHandler):
	def get(self):
		self.render_response('latour.html')

class ModelViewer(BaseHandler):
	def get(self, locale_id, page_id):

		menus = Menu.query().fetch()
		page = Page.get_by_id(page_id)

		pages = Page.query(Page.locale==ndb.Key(Locale, locale_id)).fetch()
		locales = Locale.query().fetch()

		# enriched locales with each localized page id for smooth transfert
		for locale in locales:
			this_locale = ndb.Key(Locale, locale.key.id())
			this_menu = ndb.Key(Menu, page.menu.id())
			localized_page = Page.query(Page.locale==this_locale, Page.menu==this_menu).fetch()
			locale.page = localized_page[0]

		logging.info("locale: %s page: %s", locale_id, page_id)
		template_values = {
			'page': page,
			'locale_id': locale_id,
			'menus': menus,
			'pages': pages,
			'locales': locales,
		}	
		return self.render_response('page.html', **template_values)

class LocaleViewer(BaseHandler):
	def get(self, locale_id):
		page = Page.query(Page.locale==ndb.Key(Locale, locale_id), Page.menu==ndb.Key(Menu, "the-manor")).fetch()
		self.redirect('/{0}/{1}'.format(locale_id, page[0].key.id()))
		


application = webapp2.WSGIApplication([
    webapp2.Route(r'/admin', AdminMain),
    webapp2.Route(r'/admin/locale/new', AdminNewLocale),
	webapp2.Route(r'/admin/menu/new', AdminNewMenu),
	webapp2.Route(r'/admin/page/new', AdminNewPage),
	webapp2.Route(r'/admin/page/<page_id:([^/]+)?>', AdminViewPage),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/update', AdminUpdatePage),
    webapp2.Route(r'/admin/page/<page_id:([^/]+)?>/delete', AdminPageDelete),
    webapp2.Route(r'/admin/<locale_id:([^/]+)?>', AdminViewLocale),
    webapp2.Route(r'/', MainPage),
	webapp2.Route(r'/latour', LaTour),
    webapp2.Route(r'/<locale_id:([^/]+)?>/<page_id:([^/]+)?>', ModelViewer),
    webapp2.Route(r'/<locale_id:([^/]+)?>', LocaleViewer),

	], debug=True)