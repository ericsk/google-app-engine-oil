#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" GAEO Router module. 

Classes:
    RoutingRule
    Router
"""

from copy import copy
import operator
import re
import logging


class RoutingRule(object):
    """
    Represents a routing rule.
    """

    def __init__(self, pattern='', *matches, **args):
        """Initializer.

        Args:
            pattern: [string] the pattern for the rule.
            matches: TODO: document this arg.
            args: TODO: document this arg.
        """
        self._pattern = pattern[:-1] if pattern.endswith('/') else pattern
        self._regex = self._pattern
        self._args = args
        self.__inlines = re.findall(':([^/.]+)', self._pattern)

        self._matches = []
        for i in xrange(len(matches)):
            self._matches.append((i+1, matches[i]))

        # transform the pattern to a valid RegEx
        for i in range(len(self.__inlines)):
            param = self.__inlines[i]
            self._matches.append((self._pattern.find(':' + param), param))
            self._regex = self._regex.replace(':' + self.__inlines[i],
                                              '([^/.]+)')
        self._matches = sorted(self._matches, key=operator.itemgetter(0))

        # normalize the RegEx
        if not self._regex.startswith('^'):
            self._regex = '^' + self._regex

        if not self._regex.endswith('$'):
            self._regex = self._regex + '$'

    def match_url(self, uri):
        """Check if the URL is mapped to this rule. 

        Args:
            uri: The full URL of the request.

        Returns:
            TODO: document the return value.
        """
        url = uri[:-1] if uri.endswith('/') else uri
        matches = re.findall(self._regex, url)
        params = None
        if matches:
            params = copy(self._args)
            match = matches[0]
            if isinstance(match, basestring):
                if self._matches:
                    params[self._matches[0][1]] = match
            else:
                for i in range(len(match)):
                    params[self._matches[i][1]] = match[i]
                    
        return params
    
    def __str__(self):
        return self._pattern
    
    def __eq__(self, other):
        return self._regex == other._regex


class Router(object):
    """
    The request router class.
    """
    __rules = []

    def __init__(self):
        """Initializer."""
        pass

    def add(self, rule):
        """Adds the routing rule into the Router.

        The rule is ignored if the same rule is already in the Router.

        Args:
            rule: a RoutingRule object.
        """
        if rule not in (x[0] for x in self.__rules):
            self.__rules.append((rule, None))

    def remove(self, rule):
        """Removes the routing rule from the Router.

        This method is a no op if the input rule is not in the Router.

        Args:
            rule: a RoutingRule object.
        """
        for r in self.__rules:
            if r[0] == rule:
                self.__rules.remove(rule)
                break

    def resolve(self, uri):
        """Finds the rule that matches to the URL.

        Args:
            uri: The full URL of the request.

        Returns:
            TODO: document the return value.   
        """
        for rule in self.__rules:
            params = rule[0].match_url(uri)
            if params:
                return (params, rule[1])
            
        return None

    def restful(self, rule, **args):
        """Add a RESTful service routing.

        TODO: document this method.

        Args:
            rule:

        Returns:
        """
        # default RESTful routing
        restful_routing = {
            'get': 'show',
            'post': 'create',
            'put': 'update',
            'delete': 'destroy'
        }
        if rule not in self.__rules:
            for key, val in args.iteritems():
                if key in restful_routing.keys():
                    restful_routing[key] = val

            self.__rules.append((rule, restful_routing))
