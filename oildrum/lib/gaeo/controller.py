#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The gaeo controller module. 

Classes:
    Controller:
"""

import logging
from email.Utils import formatdate
import time
import urllib

# GAEO imports
from gaeo.session import Session

# App imports
import settings

class Controller(object):
    """
    The GAEO Controller class.
    
    """
    _rendered = False

    def __init__(self, request, response, params={}):
        '''Initializes a Controller object.

        Args:
            request: a GaeoRequest object.
            response: a GaeoResponse object.
            params: a dict of request parameters and routing parameters.
        '''
        self.request = request
        self.response = response
        self.params = params
        
        # normalize the parameters
        for k in self.request.arguments():
            self.params[k] = self.request.get_all(k)
            if len(self.params[k]) == 1:
                self.params[k] = self.params[k][0]
        
        # store the requested parameters (both GET/POST)
        self.params = self.__nested_params(self.params)
        # shorthand to (read-only) cookies object
        self.cookies = request.cookies
        # get/create the session object
        self.session = self._get_session()
        # check if the request is a AJAX call
        self.is_xhr = 'X_REQUESTED_WITH' in self.request.headers and \
            self.request.headers['X_REQUESTED_WITH'] == 'XMLHttpRequest'
        
        # initial the view instance
        try:
            module = __import__('gaeo.view',
                                globals(),
                                locals(),
                                settings.VIEW_CLASS,
                                -1)
            clz = module.__dict__.get(settings.VIEW_CLASS)
            self.view = clz(self)
        except ImportError, e:
            logging.error('Cannot initialize the view instance: %s', e)
            raise
    
        self.view.session = self.session

    def before_action(self):
        """Performs work needed before the action method is called.
        
        This is the template method pattern. Subclasses should provide
        an implementation.
        """
        pass

    def after_action(self):
        """Performs work needed after the action method returns.
        
        This is the template method pattern. Subclasses should provide
        an implementation.
        """
        pass

    def redirect(self, url, permanently=False):
        """Sets HTTP headers to redirect the client.

        Args:
            url: the URL to redirect to.
            permanantly: True if the redirect should be permanent.

        Side effect:
            Marks this request as rendered.
        """
        if permanently:
            self.response.set_status(301, 'Move Permanently')
        else:
            self.response.set_status(302, 'Found')
        self.response.headers['Location'] = url
        self.response.clear()
        self._rendered = True

    def output(self, *html):
        """Writes data to client.

        Args:
            html: a list of data items to be written out.

        Side effect:
            Marks this request as rendered.
        """
        for h in html:
            self.response.out.write(h)
        self._rendered = True

    def set_no_render(self):
        """Marks this request as rendered."""
        self._rendered = True

    def json_output(self, json_data={}):
        """Writes data to client in JSON format.

        Args:
            json_data: data object to be jsonized and written out.

        Side effect:
            Marks this request as rendered.
        """
        from django.utils import simplejson
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(json_data))
        self._rendered = True

    def complete(self):
        """Completes the rendering.
        
        Asks the view to render itself if the request isn't marked as rendered.
        """
        if not self._rendered:
            self.view.render()

    def no_action(self, template_path='', params={}):
        """Handles the request when no action method is found.

        Feeds the params to the template at template_path for rendering and
        writes the result to the client.
        
        Args:
            template_path: the path of the template to use, bypass rendering
                if it is ''.
            params: the parameters to feed to the template.

        Returns:
            True if rendering is done, False otherwise.
        """
        if template_path:
            import os
            from google.appengine.ext.webapp import template
            try:
                content = template.render(template_path, params)
                self.response.out.write(content)
                return True
            except:
                pass
        return False

    def set_cookie(self, name, value, max_age=None):
        """Sets a cookie in the HTTP header.

        Args:
            name: the name of the cookie.
            value: the value of the cookie.
            max_age: [optional] the maximum age of the cookie before it expires.
        """
        cookie_data = [
            '%s=%s' % (name, value),
            'path=%s' % settings.SESSION_COOKIE_PATH
        ]
        if max_age is not None:
            rfcdate = formatdate(time.time() + max_age)
            expires = '%s-%s-%s GMT' % (rfcdate[:7], rfcdate[8:11], rfcdate[12:25])
            cookie_data.extend([
                'max_age=%s' % max_age,
                'expires=%s' % expires
            ])

        cookie_str = '; '.join(cookie_data)
        self.response.headers.add_header('Set-Cookie', cookie_str)
        logging.debug("Set-Cookie: %s" % cookie_str)

    def _get_session(self):
        """Returns the session object for this request.

        1. If the session cookie is present in HTTP header, return the session
           associated with the cookie.
        2. Otherwise return a newly created session object with its cookie
           inserted into the HTTP header.
        """
        session = None
        session_key = settings.SESSION_COOKIE_NAME
        if session_key in self.cookies:
            session = Session(key=self.cookies[session_key], 
                              controller=self)
        
        if session is None:
            session = Session(controller=self)
        
        return session

    def __appender(self, dict, arr, value):
        """Sets dict[arr[0]][arr[1]]...[arr[N-1]] = value.

        Args:
            dict: the dict object to insert value into.
            arr: the list of keys to map to the value.
            value: the value to be inserted.
        """
        if len(arr) > 1:
            try:
                dict[arr[0]]
            except KeyError:
                dict[arr[0]] = {}
            return {arr[0]: self.__appender(dict[arr[0]], arr[1:], value)}
        else:
            dict[arr[0]] = value
            return

    def __nested_params(self, params):
        """Converts a flat dict into a nested dict.

        A flat dict of key -> value with key in the form of
        'key0[key1][key2]...[keyN]' is converted to a nested dict 
        like key0['key1']['key2']...['keyN'] -> value.

        If key0 contains dashes ('-'), it is split into multiple keys.

        Args:
            params: a flat dict.
        
        Returns:
            The nested dict.
        """
        result = {}
        for key in params:
            parray = key.replace(']', '').split('[')
            if len(parray) == 1:
                parray = parray[0].split('-')
            self.__appender(result, parray, params[key])
        return result
