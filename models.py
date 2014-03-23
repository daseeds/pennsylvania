#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from google.appengine.ext import ndb

NORMAL = 1
DROPDOWN = 2

pagination_choice = ["jumbo", "right", "left", "jumbo_left", "white", "slides"]
block_choice = ["no-pic", "pic-left", "pic-right", "widget", "video", "full-video", "map"]

# class SubMenu(ndb.Model):
# 	order = ndb.IntegerProperty()	

class Menu(ndb.Model):
	order = ndb.IntegerProperty()
	parent = ndb.KeyProperty(kind='Menu')
	submenus = ndb.KeyProperty(kind='Menu', repeated=True)
	

class Locale(ndb.Model):
	name = ndb.StringProperty()

class Picture(ndb.Model):
	size_max = ndb.BlobKeyProperty(required=True)
	size_med = ndb.BlobKeyProperty()
	size_thumb = ndb.BlobKeyProperty()
	caption = ndb.StringProperty(default="")
	etag = ndb.StringProperty(default="")

class Block(ndb.Model):
	title = ndb.StringProperty()
	subtitle = ndb.StringProperty()
	pagination = ndb.StringProperty(default="no-pic", choices=block_choice)
	content = ndb.TextProperty()
	picture = ndb.KeyProperty(Picture)
	widget = ndb.TextProperty(default="")
	widget_script = ndb.TextProperty(default="")

class Page(ndb.Model):
	locale = ndb.KeyProperty(Locale, required=True)
	name = ndb.StringProperty(required=True)
	title = ndb.StringProperty()
	menu = ndb.KeyProperty(Menu, required=True)
	backgrounds = ndb.KeyProperty(kind='Picture', repeated=True)
	blocks = ndb.KeyProperty(Block, repeated=True)
	description = ndb.StringProperty(default="")

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

