# -*- coding: utf-8 -*-
"""Naumanni Core."""
import asyncio
import inspect
import logging
import os
import pkg_resources

import aioredis
import redis
from tornado import concurrent, gen, httpclient

import naumanni

try:
    import config
except:
    config = {}


logger = logging.getLogger(__name__)
USER_AGENT = 'Naumanni/{}'.format(naumanni.VERSION)


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
        self.config = config
        self.root_path = os.path.abspath(os.path.join(naumanni.__file__, os.path.pardir, os.path.pardir))
        self.plugins = self.load_plugins()
        # TODO: remove strict redis
        self.redis = redis.StrictRedis.from_url(config.redis_url)

    def load_plugins(self):
        assert not hasattr(self, 'plugins')
        plugins = {}
        for ep in pkg_resources.iter_entry_points('naumanni.plugins'):
            plugin_id = ep.name
            plugin_class = ep.load()
            plugins[plugin_id] = plugin_class(self, plugin_id)

            logger.info('Load plugin: %s', plugin_id)
        return plugins

    async def setup(self, task_id):
        """runloop前の最後のセットアップ"""
        self.task_id = task_id
        if not task_id:
            # forkしてたら0, してなければNoneがくる  1st-processなのでtimer系をここにinstall
            self.emit('after-start-first-process')

        _d = self.redis.connection_pool.connection_kwargs
        self._async_redis_pool = await aioredis.create_pool(
            (_d['host'], _d['port']),
            db=_d['db'],
            loop=asyncio.get_event_loop()
        )

    def emit(self, event, **kwargs):
        rv = {}
        _result_hook = kwargs.pop('_result_hook', None)
        funcname = 'on_' + event.replace('-', '_')
        for plugin in self.plugins.values():
            handler = getattr(plugin, funcname, None)
            if handler is not None:
                result = handler(**kwargs)
                assert not inspect.iscoroutinefunction(result)

                rv[plugin.id] = result
                if _result_hook:
                    kwargs = _result_hook(rv[plugin.id], kwargs)

        return rv

    async def emit_async(self, event, **kwargs):
        rv = {}
        _result_hook = kwargs.pop('_result_hook', None)
        funcname = 'on_' + event.replace('-', '_')
        for plugin in self.plugins.values():
            handler = getattr(plugin, funcname, None)
            if handler is not None:
                rv[plugin.id] = await handler(**kwargs)
                if _result_hook:
                    kwargs = _result_hook(rv[plugin.id], kwargs)

        return rv

    # redis
    def get_async_redis(self):
        return self._async_redis_pool.get()

    # utility functions
    async def crawl_url(self, url_or_request):
        """指定されたURLを撮ってきて返す"""
        # TODO: crawler pool的な感じにする
        response = await httpclient.AsyncHTTPClient().fetch(
            url_or_request, follow_redirects=False, raise_error=False, user_agent=USER_AGENT)
        return response


class _AsyncRedisPool(object):
    __slots__ = ('_app', '_conn')

    def __init__(self, app):
        self._app = app
        self._conn = None

    async def __aenter__(self):
        pool = await self._app.async_redis_pool
        self._conn = await pool.acquire()
        return self._conn

    async def __aexit__(self, exc_type, exc_value, tb):
        pool = await self._app.async_redis_pool
        try:
            pool.release(self._conn)
        finally:
            self._app = None
            self._conn = None
