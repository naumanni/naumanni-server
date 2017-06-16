# -*- coding: utf-8 -*-
import asyncio
import logging
import functools
import os
import signal
import time

import psutil
from tornado import ioloop, routing, web
from tornado.httpserver import HTTPServer
from tornado.wsgi import WSGIContainer
import tornado.netutil
import tornado.process
from tornado.platform.asyncio import AsyncIOMainLoop

from .proxy import APIProxyHandler
from .websocket import WebsocketProxyHandler


logger = logging.getLogger(__name__)
master_pid = psutil.Process(os.getpid())
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 5


class NaumanniWebApplication(web.Application):
    def add_plugin_handlers(self, plugin_id, handlers):
        """plugin apiを追加する"""

        # plugin apiのprefixをURLに追加する
        path_prefix = '/plugins/{}/'.format(plugin_id)
        replaced_handlers = []
        for rule in handlers:
            if isinstance(rule, (tuple, list)):
                if isinstance(rule[0], str):
                    if not rule[0].startswith('/'):
                        raise ValueError('invalid plugin url path, must be startswith \'/\'')
                    rule = (path_prefix + rule[0][1:], *rule[1:])
                else:
                    assert 0, 'not implemented'
            else:
                assert 0, 'not implemented'

            replaced_handlers.append(rule)

        # 登録
        self.wildcard_router.add_rules(
            [(path_prefix + '.*$', web._ApplicationRouter(self, replaced_handlers))]
        )


class WebServer(object):
    def __init__(self, naumanni_app, listen):
        self.naumanni_app = naumanni_app
        self.listen = listen

        self.init()

    def init(self):
        handlers = [
            (r'/proxy/(?P<request_url>.+)', APIProxyHandler),
            (r'/ws/(?P<request_url>.+)', WebsocketProxyHandler),
        ]
        self.application = NaumanniWebApplication(
            handlers,
            compress_response=True,
            debug=self.naumanni_app.debug,
            autoreload=False,
            websocket_ping_interval=3,
            naumanni_app=self.naumanni_app,
        )
        self.naumanni_app.emit('after-initialize-webserver', webserver=self)

    def start(self):
        # install signal handlers for master proc
        install_master_signal_handlers()

        sockets = tornado.netutil.bind_sockets(*self.naumanni_app.config.listen)
        if not self.naumanni_app.debug:
            # debugじゃなければforkする
            task_id = tornado.process.fork_processes(0)
            # use asyncio for ioloop
            AsyncIOMainLoop().install()
        else:
            # debugなのでautoreloadする
            AsyncIOMainLoop().install()
            from tornado import autoreload
            autoreload.start()
            task_id = None

        if not task_id:
            # forkしてたら0, してなければNoneがくる  1st-processなのでtimer系をここにinstall
            self.naumanni_app.emit('after-start-first-process')

        self.server = HTTPServer(self.application)
        self.server.add_sockets(sockets)

        if task_id is not None:
            # install signal handlers for child proc
            install_child_signal_handlers(self.naumanni_app, self.server)

        # run ioloop
        try:
            asyncio.get_event_loop().run_forever()
        finally:
            pass


def install_master_signal_handlers():
    """SIGTERMされてもちゃんと終了するように"""
    def stop_handler(sig, frame):
        logger.warning('master caught signal: %s', sig)
        io_loop = ioloop.IOLoop.current()

        try:
            for children_pid in master_pid.children():
                children_pid.send_signal(signal.SIGTERM)

            io_loop.add_callback_from_signal(io_loop.stop)
        except Exception as exc:
            logger.exception(exc)

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGQUIT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)


def install_child_signal_handlers(naumanni_app, server):
    """子プロセスがgracefulに死ぬように"""
    def stop_handler(naumanni_app, server, sig, frame):
        io_loop = tornado.ioloop.IOLoop.instance()

        def stop_loop(deadline):
            now = time.time()
            if now < deadline and has_ioloop_tasks(io_loop):
                logger.info('Waiting for next tick')
                io_loop.add_timeout(now + 1, stop_loop, deadline)
            else:
                io_loop.stop()
                logger.info('Shutdown finally')

        def shutdown():
            logger.info('Stopping http server')
            naumanni_app.emit('before-stop-server')
            server.stop()
            logger.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
            stop_loop(time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)

        logger.warning('child caught signal: %s', sig)
        print(io_loop)
        io_loop.add_callback_from_signal(shutdown)

    handler = functools.partial(stop_handler, naumanni_app, server)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGQUIT, handler)
    signal.signal(signal.SIGTERM, handler)


def has_ioloop_tasks(io_loop):
    if hasattr(io_loop, '_callbacks'):
        return io_loop._callbacks or io_loop._timeouts
    elif hasattr(io_loop, 'handlers'):
        return len(io_loop.handlers)
    return False
