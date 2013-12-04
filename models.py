# coding: utf-8
from google.appengine.ext import ndb

class Page(ndb.Model):
	locale_id = ndb.StringProperty(required=True)
	name = ndb.StringProperty(required=True)
	lead = ndb.StringProperty()

class Locale(ndb.Model):
	pages = ndb.StructuredProperty(Page, repeated=True)


# test = Locale(
# 	url = 'en',
# 	name = 'English',
# 	pages = [Page(
# 			url = 'bed-and-breakfeast-manor-in-normandy',
# 			name = 'The Manor',
# 			lead = 'XVI CENTURY MANOR HOUSE'),
# 			Page(
# 			url = 'bed-and-breakfeast-manor-rooms',
# 			name = 'Rooms',
# 			lead = '')])

# test.put()

