import os
import urllib
import logging
import webapp2

from webapp2_extras.routes import RedirectRoute
from webapp2_extras import jinja2

from models import Locale, Page, Menu

from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb

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

class AdminBaseHandler(webapp2.RequestHandler):
	@webapp2.cached_property
	def jinja2(self):
	# Returns a Jinja2 renderer cached in the app registry.
		return jinja2.get_jinja2(factory=jinja2_factory)

	def render_response(self, _template, **context):
		# Renders a template and writes the result to the response.
		rv = self.jinja2.render_template(_template, **context)
		self.response.write(rv)
	def handle_exception(self, exception, debug):
		# Log the error.
		logging.exception(exception)
		# Set a custom message.
		self.response.write("An error occurred.")
		# If the exception is a HTTPException, use its error code.
		# Otherwise use a generic 500 error code.
		if isinstance(exception, webapp2.HTTPException):
			self.response.set_status(exception.code)
		else:
			self.response.set_status(500)

class AdminMain(AdminBaseHandler):
	def get(self):

		locale_query = Locale.query()
		locales = locale_query.fetch()

		menu_query = Menu.query()
		menus = menu_query.fetch()

		pages = Page.query().fetch()

		template_values = {
			'url': users.create_logout_url(self.request.uri),
			'url_linktext': 'Logout',
			'user': users.get_current_user(),
			'locales': locales,
			'menus': menus,
			'pages': pages,
		}	
		return self.render_response('admin_view_locales.html', **template_values)

class AdminNewLocale(AdminBaseHandler):
	def post(self):
		locale = Locale(id=self.request.get('locale_id'))
		locale.put()
		return self.redirect('/admin')

class AdminNewMenu(AdminBaseHandler):
	def post(self):
		menu = Menu(id=self.request.get('menu_id'))
		menu.put()
		return self.redirect('/admin')


class AdminNewPage(AdminBaseHandler):
	def post(self, locale_id):
		page = Page(id=self.request.get('page_id'), 
					name = self.request.get('name'),
					locale_id = locale_id)
		page.put()
		return self.redirect('/admin/%s' % locale_id)

class AdminUpdatePage(AdminBaseHandler):
	def post(self, locale_id, page_id):

		page = Page.get_by_id(page_id)

		return self.redirect('/admin/{0}/{1}'.format(unicode(locale_id), unicode(page_id)))

class AdminViewLocale(AdminBaseHandler):
	def get(self, locale_id):

		page_query = Page.query(Page.locale_id==ndb.Key(Locale, locale_id))
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
	def get(self, locale_id, page_id):

		page = Page.get_by_id(page_id)

		template_values = {
			'url': users.create_logout_url(self.request.uri),
			'url_linktext': 'Logout',
			'user': users.get_current_user(),
			'page': page,
			'locale': locale_id,
		}	
		return self.render_response('admin_view_page.html', **template_values)


