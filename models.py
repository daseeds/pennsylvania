# coding: utf-8
from google.appengine.ext import ndb

NORMAL = 1
DROPDOWN = 2

# class SubMenu(ndb.Model):
# 	order = ndb.IntegerProperty()	

class Menu(ndb.Model):
	order = ndb.IntegerProperty()
	parent = ndb.KeyProperty(kind='Menu')
	submenus = ndb.KeyProperty(kind='Menu', repeated=True)

class Locale(ndb.Model):
	name = ndb.StringProperty()

class Page(ndb.Model):
	locale = ndb.KeyProperty(Locale, required=True)
	name = ndb.StringProperty(required=True)
	lead = ndb.StringProperty()
	menu = ndb.KeyProperty(Menu, required=True)
	content = ndb.TextProperty()
	backgrounds = ndb.BlobKeyProperty(repeated=True)



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

