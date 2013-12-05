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
	def handle_exception(self, exception, debug):
		# Log the error.
		logging.exception(exception)
		# Set a custom message.
		response.write("An error occurred.")
		# If the exception is a HTTPException, use its error code.
		# Otherwise use a generic 500 error code.
		if isinstance(exception, webapp2.HTTPException):
			response.set_status(exception.code)
		else:
			response.set_status(500)


class MainPage(BaseHandler):
	def get(self):
		self.render_response('index.html')

class LaTour(webapp2.RequestHandler):
	def get(self):
		self.render_response('latour.html')

class ModelViewer(BaseHandler):
    def get(self, locale_id, page_id):
        logging.info("locale: %s page: %s", locale_id, page_id)
        self.render_response('index.html')


application = webapp2.WSGIApplication([
    webapp2.Route(r'/admin', AdminMain),
    webapp2.Route(r'/admin/locale/new', AdminNewLocale),
	webapp2.Route(r'/admin/menu/new', AdminNewMenu),
    webapp2.Route(r'/admin/<locale_id:([^/]+)?>', AdminViewLocale),
    webapp2.Route(r'/admin/<locale_id:([^/]+)?>/new', AdminNewPage),
    webapp2.Route(r'/admin/<locale_id:([^/]+)?>/<page_id:([^/]+)?>', AdminViewPage),
    webapp2.Route(r'/admin/<locale_id:([^/]+)?>/<page_id:([^/]+)?>/update', AdminUpdatePage),
    webapp2.Route(r'/', MainPage),
	webapp2.Route(r'/latour', LaTour),
    webapp2.Route(r'/<locale_id:([^/]+)?>/<page_id:([^/]+)?>', ModelViewer),

	], debug=True)