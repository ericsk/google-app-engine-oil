#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# gae imports
from google.appengine.ext import db


class DatastoreModel(db.Model):
    """
    GAEO enhanced model in Datastore implementation
    """

    def before_put(self):
        """The template method called before putting the entity to DataStore.

        This is a template method pattern. It is a hook that self.put() calls
        before actually putting the entity to DataStore.

        Returns:
            False if the entity should NOT be put into DataStore.
        """
        return True

    def after_put(self):
        """The template method called after putting the entity to DataStore.

        This is a template method pattern. It is a hook that self.put() calls
        after the entity is put to DataStore.
        """
        pass

    def put(self, **kwargs):
        """Puts the entity to DataStore.

        Args:
            **kwargs: the keyword arguments to be passed to db.Model.put().

        Returns:
            the key of the entity put into DataStore.
        """
        if self.before_put() is not False:
            if kwargs:
                key = super(DatastoreModel, self).put(**kwargs)
            else:
                key = super(DatastoreModel, self).put()
            self.after_put()
            return key

    # alias
    update = put

    def set_attributes(self, **attrs):
        """TODO: document this method.
        """
        props = self.properties()
        for prop in props.values():
            if prop.name in attrs:
                prop.__set__(self, attrs[prop.name])

    def update_attributes(self, **attrs):
        """TODO: document this method.
        """
        self.set_attributes(**attrs)
        self.update()
