import os
import urllib
import logging
import webapp2

from webapp2_extras.routes import RedirectRoute
from webapp2_extras import jinja2
from functools import wraps
from models import Locale, Page, Menu, SubMenu

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

		menu_list = []
		for menu in menus:
			menu_list.append(menu.key.id())

		submenus = SubMenu.query().fetch()

		pages = Page.query().fetch()

		template_values = {
			'url': users.create_logout_url(self.request.uri),
			'url_linktext': 'Logout',
			'user': users.get_current_user(),
			'locales': locales,
			'menus': menus,
			'pages': pages,
			'submenus': submenus,
			'menu_list': menu_list,
		}	
		return self.render_response('admin_view_locales.html', **template_values)

class AdminNewLocale(AdminBaseHandler):
	def post(self):
		locale = Locale(id=self.request.get('locale_id'),
						name=self.request.get('name'))
		locale.put()
		return self.redirect('/admin')

class AdminNewMenu(AdminBaseHandler):
	def post(self):
		menu = Menu(id=self.request.get('menu_id'))
		menu.put()
		return self.redirect('/admin')

class AdminNewSubMenu(AdminBaseHandler):
	def post(self):
		submenu = SubMenu(id=self.request.get('submenu_id'))
		submenu.put()
		menu = ndb.Key('Menu', self.request.get('menu_id')).get()
		menu.submenus.append(submenu)
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
					menu = ndb.Key(Menu, self.request.get('menu_id')))
		page.put()
		return self.redirect('/admin')

class AdminUpdatePage(AdminBaseHandler):
	def post(self, page_id):

		page = Page.get_by_id(page_id)
		page.id = self.request.get('page_id')
		page.menu = ndb.Key(Menu, self.request.get('menu_id'))
		page.locale = ndb.Key(Locale, self.request.get('locale_id'))
		page.put()

		return self.redirect('/admin/page/{0}'.format(unicode(page_id)))

class AdminPageDelete(AdminBaseHandler):
	def post(self, page_id):
		ndb.Key(Page, page_id).delete()
		return self.redirect('/admin')

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
		}	
		return self.render_response('admin_page_new.html', **template_values)

