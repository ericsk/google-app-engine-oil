#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" The application settings module. """

import os

# General
DEBUG = True
ROOT_PATH = os.path.dirname(__file__)
APP_DIR = 'application'
APP_PATH = os.path.join(ROOT_PATH, APP_DIR)
TEMPLATE_DIR = 'templates'
TEMPLATE_PATH = os.path.join(ROOT_PATH, APP_DIR, TEMPLATE_DIR)
PLUGIN_DIR = 'plugins'
PLUGIN_FILTERS_DIR = 'filters'
PLUGIN_FILTERS_PATH = os.path.join(ROOT_PATH, PLUGIN_DIR, PLUGIN_FILTERS_DIR)
CACHE_TIMEOUT = 3600

# Session
SESSION_COOKIE_NAME = 'GAEOSSID'
SESSION_COOKIE_NAME_LENGTH = 64
SESSION_COOKIE_TIMEOUT = 21600 # 6 hours
SESSION_COOKIE_PATH = '/'

# Controller
HANDLE_MISSING_ACTION = True

# View
VIEW_CLASS = 'AppengineTemplateView'

