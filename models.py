#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from google.appengine.ext import ndb

NORMAL = 1
DROPDOWN = 2

pagination_choice = ["jumbo", "right", "left", "jumbo_left", "white", "slides"]
block_choice = ["no-pic", "pic-left", "pic-right", "widget", "widget-right", "video", "full-video", "map", "price-pic-left", "price-pic-right", "heads-up", "slides", "full-pic", "parallax"]
kind_choice = ["nav", "nav-button", "footer"]

# class SubMenu(ndb.Model):
# 	order = ndb.IntegerProperty()	

class Menu(ndb.Model):
	order = ndb.IntegerProperty()
	parent = ndb.KeyProperty(kind='Menu')
	submenus = ndb.KeyProperty(kind='Menu', repeated=True)
	kind = ndb.StringProperty(default="nav", choices=kind_choice)
	

class Locale(ndb.Model):
	name = ndb.StringProperty()

class Picture(ndb.Model):
	size_max = ndb.BlobKeyProperty(required=True)
	size_med = ndb.BlobKeyProperty()
	size_thumb = ndb.BlobKeyProperty()
	caption = ndb.StringProperty(default="")
	etag = ndb.StringProperty(default="")
	name = ndb.StringProperty()

class Price(ndb.Model):
	nb_guests = ndb.IntegerProperty()
	price = ndb.StringProperty()

class HeadsUp(ndb.Model):
	title = ndb.StringProperty()
	content  = ndb.StringProperty()
	menu = ndb.KeyProperty(Menu, required=True)
	picture = ndb.KeyProperty(Picture)

class Block(ndb.Model):
	title = ndb.StringProperty()
	subtitle = ndb.StringProperty()
	pagination = ndb.StringProperty(default="no-pic", choices=block_choice)
	content = ndb.TextProperty()
	picture = ndb.KeyProperty(Picture)
	widget = ndb.TextProperty(default="")
	widget_script = ndb.TextProperty(default="")
	prices = ndb.KeyProperty(Price, repeated=True)
	backgrounds = ndb.KeyProperty(kind='Picture', repeated=True)
	headsUps = ndb.KeyProperty(HeadsUp, repeated=True)

class Page(ndb.Model):
	locale = ndb.KeyProperty(Locale, required=True)
	name = ndb.StringProperty(required=True)
	title = ndb.StringProperty()
	menu = ndb.KeyProperty(Menu, required=True)
	backgrounds = ndb.KeyProperty(kind='Picture', repeated=True)
	blocks = ndb.KeyProperty(Block, repeated=True)
	description = ndb.StringProperty(default="")
	creation_date = ndb.DateTimeProperty(auto_now_add=True)
	creation_author = ndb.UserProperty()
	modification_date = ndb.DateTimeProperty(auto_now =True)
	modification_author = ndb.UserProperty()


class LocaleDict(ndb.Model):
	locale = ndb.KeyProperty(Locale, required=True)
	name = ndb.StringProperty(required=True)
	value = ndb.StringProperty(required=True)




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

