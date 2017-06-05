# -*- coding: utf-8 -*-
"""Naumanni Core."""
import asyncio
import logging
import os
import pkg_resources

import redis

import naumanni
from .webserver import WebServer

try:
    import config
except:
    config = {}


logger = logging.getLogger(__name__)


class NaumanniApp(object):
    __instance = None

    def __new__(cls, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        else:
            logger.warning('application initialized twice')
        return cls.__instance

    def __init__(self, debug=False):
        self.debug = debug
        self.root_path = os.path.abspath(os.path.join(naumanni.__file__, os.path.pardir, os.path.pardir))
        self.webserver = WebServer(self, getattr(config, 'listen', (8888, '0.0.0.0')))
        self.plugins = self.load_plugins()
        self.redis = redis.StrictRedis.from_url(config.redis_url)

        from celery import current_app as current_celery
        current_celery.naumanni_app = self

    def run(self):
        """Naumanniのwebの方を起動する."""
        if self.debug:
            from tornado import autoreload
            autoreload.start()

        self.webserver.start()

        try:
            asyncio.get_event_loop().run_forever()
        finally:
            pass

    def load_plugins(self):
        assert not hasattr(self, 'plugins')
        plugins = {}
        for ep in pkg_resources.iter_entry_points('naumanni.plugins'):
            plugin_id = ep.name
            plugin_class = ep.load()
            plugins[plugin_id] = plugin_class(self, plugin_id)

            logger.info('Load plugin: %s', plugin_id)
        return plugins

    def emit(self, event, **kwargs):
        rv = {}
        _result_hook = kwargs.pop('_result_hook', None)
        funcname = 'on_' + event.replace('-', '_')
        for plugin in self.plugins.values():
            handler = getattr(plugin, funcname, None)
            if handler is not None:
                rv[plugin.id] = handler(**kwargs)

                if _result_hook:
                    kwargs = _result_hook(rv[plugin.id], kwargs)

        return rv
