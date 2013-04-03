#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Session module. 

Classes:
    Session: A gaeo session interface.
    MemcacheSession: The memcache-based session storage.
"""

# python std imports
import hashlib
import random
import time
from string import digits, letters
import pickle
import urllib
import logging

# google app engine imports
from google.appengine.api import memcache

# App imports
import settings

POOL = digits + letters


class Session(dict):
    """The base session class."""
    __key = None
    __destroyed = False
    
    __controller = None
    
    def __new__(cls, key=None, auto_create=False, controller=None):
        """Constructor.
        
        If the key argument is passed in, try to fetch the stored
        session first. Otherwise, create a new one.

        Args:
            key:
            auto_create:
            controller:
        """
        session = None
        cls.__controller = controller
        
        if key is None:
            key = Session.generate_session_key()
        else:
            data = memcache.get(key)
            if data is not None:
                session = pickle.loads(data)
        
        if not session:
            session = dict.__new__(cls, {})
            session.__key = key
            session['started'] = time.time()
            cookie_value = urllib.quote_plus(key)
            cls.__controller.set_cookie(settings.SESSION_COOKIE_NAME, 
                                        cookie_value,
                                        settings.SESSION_COOKIE_TIMEOUT)
        
        return session
    
    def __init__(self, *args, **kwds):
        pass
    
    def __del__(self):
        self._put()
    
    def __setitem__(self, key, value):
        super(Session, self).__setitem__(key, value)
        self._put()
        
    def __getitem__(self, key):
        try:
            return super(Session, self).__getitem__(key)
        except KeyError:
            return None
        
    def __delitem__(self, key):
        super(Session, self).__delitem__(key)
        self._put()

    
    @property
    def key(self):
        return self.__key
    
    def destroy(self):
        logging.info('session destroyed.')
        self.__destroyed = True
        memcache.delete(self.__key)
        self.__controller.set_cookie(settings.SESSION_COOKIE_NAME,
                                     '',
                                     -time.time())
        
    def _put(self):
        if not self.__destroyed:
            memcache.set(self.key, pickle.dumps(self), 
                         time=settings.SESSION_COOKIE_TIMEOUT)

    @staticmethod    
    def generate_session_key():
        """ Generate a random key. """
        while True:
            key = ''.join([random.choice(POOL) for i in range(settings.SESSION_COOKIE_NAME_LENGTH)])
            seed = 'session|%s|%s' % (key, time.time())
            session_key = hashlib.sha1(seed).hexdigest()
            if not Session.exists_key(session_key):
                return session_key

    @staticmethod
    def exists_key(key):
        return memcache.get(key) is not None
            
