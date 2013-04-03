#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" The GAEO app package. 

Classes:
    GaeoApp: A WSGI-compatible application class. See PEP-333
    
Functions:
    start_app: A shortcut to start gaeoapp.
"""

# Python stdlib imports
import os
import sys
import cgi
import logging
import urllib
import wsgiref.headers
import wsgiref.util
from Cookie import BaseCookie
import StringIO
import webob
import yaml

# gaeo imports
import router

# App imports
import settings


def _trans_http_header_key(key):
    """ Translate the environment variable into http header's name. """
    
    ret = None
    
    if key == 'CONTENT_TYPE':
        ret = 'Content-Type'
    elif key == 'CONTENT_LENGTH':
        ret = 'Content-Length'
    elif key.startswith('HTTP_'):
        ret = key[5:].replace('_', '-').title()

    return ret

class GaeoRequest(webob.Request):
    """Represents an HTTP request.

    This is an extension of webob.Request. It lifts the size limit imposed on
    the request body and provides 4 additional APIs:
        arguments(): get a list of argument names provided in the query string
            and/or POST.
        get_all(name): get a list of argument values associated with the given
            name.
        uri(): get the full URL of this request.
        query(): get the query string.
    """
    request_body_tempfile_limit = 0

    uri = property(lambda self: self.url)
    query = property(lambda self: self.query_string)
    
    def __init__(self, environ=None, charset='UTF-8'):
        """ Create the request instance.
        
        Args:
            environ: the environment dict.
            charset: the character set used to encode/decode the strings in
                the request.
        """
        super(GaeoRequest, self).__init__(environ, charset=charset,
                                          unicode_errors='ignore', decode_param_names=True)

    def get_all(self, argument_name):
        """Returns a list of query or POST arguments with the given name.
    
        We parse the query string and POST payload lazily, so this will be a
        slower operation on the first call.
    
        Args:
            argument_name: the name of the query or POST argument
    
        Returns:
            A (possibly empty) list of values.
        """
        if self.charset:
            argument_name = argument_name.encode(self.charset)
    
        param_value = self.params.getall(argument_name)
    
        for i in xrange(len(param_value)):
            if isinstance(param_value[i], cgi.FieldStorage):
                param_value[i] = param_value[i].value
    
        return param_value
    
    def arguments(self):
        """Gets a list of argument names provided in either the query string or
        POST body.
    
        Returns:
            A list of strings for the argument names.
        """
        return list(set(self.params.keys()))


class GaeoResponse(object):
    """Represents an HTTP response.

    Public API:
        set_status(status_code, message): sets the status code and message to
            be sent to the client.
        clear(): empties the output buffer for HTTP response body string.
        wsgi_write(start_response): write out the HTTP response.

    Public data:
        headers: A wsgiref.headers.Headers object for holding HTTP headers to
            be sent out.
        cookies: The dict of cookie key-value pairs.
    """
    
    def __init__(self, body=None, charset='utf-8'):
        self._charset = charset
        self._wsgi_headers = []
        self.headers = wsgiref.headers.Headers(self._wsgi_headers)
        self.headers['Content-Type'] = 'text/html; charset=%s' % charset
        self.headers['Cache-Control'] = 'no-cache'
        self.cookies = {}
        self.status = (200, 'OK')
        self.out = StringIO.StringIO() # the output buffer.
        
    def set_status(self, status_code, message):
        """Sets the status code and message to be used in output later.

        Args:
            status_code: the HTTP response code per RFC 2616, must be an
                integer or an object that can be converted to an integer.
            message: the message associated with the status code per
                RFC 2616.
        """
        self.status = (int(status_code), message)

    def clear(self):
        """Clears the output buffer."""
        self.out.seek(0)
        self.out.truncate(0)

    def wsgi_write(self, start_response):
        """Flush the output buffer to the client.
        
        Args:
            start_response: the callback for WSGI app per PEP-333. It will be
                called with status string and header list as arguments.
        """
        body = self.out.getvalue()
        if isinstance(body, unicode):
            body = body.encode('utf-8')
        elif self.headers.get('Content-Type', '').endswith('; charset=utf-8'):
            try:
                body.decode('utf-8')
            except UnicodeError, e:
                logging.warning('Response written is not UTF-8: %s', e)

        self.headers['Content-Length'] = str(len(body))
        write = start_response('%s %s' % self.status, self._wsgi_headers)
        write(body)
        self.out.close()


class GaeoApp(object):
    """
    The WSGI-compatible application class of GAEO.
    """

    __instance = None

    def __init__(self):
        """ Initialize the application."""
        self.__instance = self
        self.__router = self._init_router()
        
    def __call__(self, environ, start_response):
        """Handles the call by a WSGI server.
        
        Args:
            environ: a dict that contains CGI-style environment varialbes.
            start_response: a callable that writes HTTP response headers and
                returns a callable for writing out HTTP response body.
            
        Returns:
            ['']. Note that the WSGI spec dictates that the app returns an
            interable of strings. The framework would send each string to the
            client unbuffered before getting the next string from the iterator.
        """
        self.request = GaeoRequest(environ)
        self.response = GaeoResponse()
        
        self._dispatch()
        
        if self.response.cookies:
            for key, value in self.response.cookies.iteritems():
                cookie = ['%s=%s' % (key, value), 
                          'path=%s' % settings.SESSION_COOKIE_PATH]
                domain_tokens = self.request.host.split('.')
                domain = ''
                if len(domain_tokens) == 1:
                    if domain_tokens[0] != 'localhost':
                        domain = domain_tokens[0]
                else:
                    domain = self.request.host
                cookie.append('domain=%s' % domain)
                self.response.headers.add_header('Set-Cookie', ';'.join(cookie))
            
        self.response.wsgi_write(start_response)
        return ['']

    def _dispatch(self):
        """Dispatch the request according to the request URI.

        This method identifies the controller and action from the URL path,
        creates the controller object with the right class, and calls the
        right action method of it. The controller's bootstrap(),
        before_action(), after_action() and complete() methods are called
        at appropriate times.

        If the controller class does not have the action specified in URL path
        and settings.HANDLE_MISSING_ACTION is True, the template named as
        {controller}/{action}.html is used for output.

        Sets HTTP status code:
         - 404: if the URL path doesn't match any routing rules or the
                template for missing action doesn't exist.
         - 500: if an exception occurred while importing the controller
                class or the bootstrap module.

        Raises:
            Any exception that's raised and is not ImportError if
            settings.DEBUG is True.
        """
        routing = self.__router.resolve(self.request.path)
        if routing is None or routing[0] is None:
            self.response.set_status(404, "Not Found")
            return

        route = routing[0]
        
        # check if RESTful
        if routing[1] is not None:
            method = self.request.method
            route['action'] = routing[1].get(method, 'index')
            
        if 'action' not in route:
            route['action'] = 'index'
        
        params = {}
        for key, value in self.request.params.iteritems():
            params[key] = value
        
        params.update(route)
        action_controller = None
        try:
            module_name = '%s.controllers.%s' % \
                (settings.APP_DIR.split('/')[-1], route['controller'])
            controller_name = route['controller'].title().replace('-', '')
            module = __import__(module_name,
                                globals(),
                                locals(),
                                controller_name,
                                -1)
            action_controller = module.__dict__.get(controller_name)
        except ImportError, e:
            logging.error('Cannot import the controller: %s', e)
            self.response.set_status(500, 'Internal Server Error')
        except Exception, e:
            if settings.DEBUG:
                raise
            self.response.set_status(500, 'Internal Server Error')
        else:
            try:
                # create the controller instance
                ctrl = action_controller(self.request, self.response, params=params)
                
                # apply the global init
                application_module = \
                    __import__('%s.controllers.bootstrap' % settings.APP_DIR,
                               globals(),
                               locals(),
                               'Bootstrap',
                               -1)
                bootstrap_clz = application_module.__dict__.get('Bootstrap')
                if bootstrap_clz not in action_controller.__bases__:
                    action_controller.__bases__ += (bootstrap_clz, )
                ctrl.bootstrap()
                
                # invokes the action
                action = getattr(ctrl, route['action'], None)
                if action:
                    if ctrl.before_action() is not False:
                        action()
                        ctrl.after_action()
                        ctrl.complete()
                else:
                    # check if there is an appropriate template file
                    error404 = True
                    if settings.HANDLE_MISSING_ACTION:
                        template_path = os.path.join(settings.TEMPLATE_PATH, route['controller'].lower(), route['action'].lower() + '.html')
                        error404 = not ctrl.no_action(template_path, {})
                
                    if error404:
                        self.response.set_status(404, 'Not Found')
            except Exception, e:
                if settings.DEBUG:
                    raise
                self.response.set_status(500, 'Internal Server Error')

    @property
    def router(self):
        """Gets the router instance.""" 
        return self.__router

    def _init_router(self):      
        """Initializes the router's routing rules."""
        the_router = router.Router()
        route_config = yaml.safe_load(file(os.path.join(settings.ROOT_PATH, 'routes.yaml')))
        for route in route_config.get('routes', []):
            pattern = route.get('rule', '')
            matches = route.get('regex', [])
            params = route.get('parameters', {})
            the_router.add(router.RoutingRule(pattern, *matches, **params))
        return the_router


def _start_response(status, headers, exc_info=None):
    """The default start_response callback of GAEO per WSGI spec (PEP-333).

    This callable is used to begin the HTTP response and return a
    write(body_string) callable.

    Args:
        status: status string of the form "200 OK".
        headers: a list of (header name, header value) tuples for HTTP header
            to be written out.
        exc_info: [optional] exception information 3-tuple, should be supplied
            only if called by an error handler.

    Returns:
        A callable that takes a HTTP response body string as the sole argument.
    """
    if exc_info:
        raise exc_info[0], exc_info[1], exc_info[2]
    
    print 'Status: %s' % status
    for key, value in headers:
        print '%s: %s' % (key, value)
    print
    return sys.stdout.write


def start_app(app):
    """Starts the given GaeoApp instance.

    Design pattern: facade.

    This function hides the procedure of the following work while providing
    a simple API.
     1. preparing environment for the application,
     2. starting up the application,
     3. writing strings obtained from the application to client.

    Args:
        app: the GaeoApp instance to be started.
    """
    env = dict(os.environ)
    env["wsgi.input"] = sys.stdin
    env["wsgi.errors"] = sys.stderr
    env["wsgi.version"] = (1, 0)
    env["wsgi.run_once"] = True
    env["wsgi.url_scheme"] = wsgiref.util.guess_scheme(env)
    env["wsgi.multithread"] = False
    env["wsgi.multiprocess"] = False
    
    response_data = app(env, _start_response)
    if response_data:
        for data in response_data:
            sys.stdout.write(data)
    
    
