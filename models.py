#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from google.appengine.ext import ndb

NORMAL = 1
DROPDOWN = 2

pagination_choice = ["jumbo", "right", "left", "jumbo_left", "white", "slides"]

# class SubMenu(ndb.Model):
# 	order = ndb.IntegerProperty()	

class Menu(ndb.Model):
	order = ndb.IntegerProperty()
	parent = ndb.KeyProperty(kind='Menu')
	submenus = ndb.KeyProperty(kind='Menu', repeated=True)
	backgrounds = ndb.KeyProperty(kind='Picture', repeated=True)

class Locale(ndb.Model):
	name = ndb.StringProperty()

class Picture(ndb.Model):
	size_max = ndb.BlobKeyProperty(required=True)
	size_med = ndb.BlobKeyProperty()
	size_thumb = ndb.BlobKeyProperty()
	caption = ndb.StringProperty(default="")
	etag = ndb.StringProperty(default="")


class Page(ndb.Model):
	locale = ndb.KeyProperty(Locale, required=True)
	name = ndb.StringProperty(required=True)
	title = ndb.StringProperty()
	lead = ndb.StringProperty()
	menu = ndb.KeyProperty(Menu, required=True)
	content = ndb.TextProperty()
	room_price = ndb.IntegerProperty(default=0)
	room_price_detail = ndb.StringProperty(default="per room per night, for 2 person")
	pagination = ndb.StringProperty(default="jumbo", choices=pagination_choice)
	widget = ndb.TextProperty(default="")
	widget_script = ndb.TextProperty(default="")


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

