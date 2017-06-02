# -*- coding: utf-8 -*-
from weakref import ref as weakref


class Plugin(object):
    def __init__(self, app, plugin_id):
        self._app = weakref(app)
        self._id = plugin_id

    @property
    def app(self):
        rv = self._app()
        if not rv:
            raise RuntimeError('Application went away')
        return rv

    @property
    def id(self):
        return self._id
