# coding: utf-8
from google.appengine.ext import ndb

NORMAL = 1
DROPDOWN = 2

class Menu(ndb.Model):
	pass

class Locale(ndb.Model):
	pass


class Page(ndb.Model):
	locale_id = ndb.KeyProperty(Locale, required=True)
	name = ndb.StringProperty(required=True)
	lead = ndb.StringProperty()
	menu = ndb.KeyProperty(Menu, required=True)
	content = ndb.TextProperty()




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

