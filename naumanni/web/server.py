# -*- coding: utf-8 -*-
import asyncio

from tornado import routing, web
from tornado.httpserver import HTTPServer
from tornado.wsgi import WSGIContainer
import tornado.netutil
import tornado.process
from tornado.platform.asyncio import AsyncIOMainLoop

from .proxy import APIProxyHandler
from .websocket import WebsocketProxyHandler


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
        sockets = tornado.netutil.bind_sockets(8888)
        if not self.naumanni_app.debug:
            # debugじゃなければforkする
            tornado.process.fork_processes(0)
            # use asyncio for ioloop
            AsyncIOMainLoop().install()
        else:
            # debugなのでautoreloadする
            AsyncIOMainLoop().install()
            from tornado import autoreload
            autoreload.start()

        if not tornado.process.task_id():
            # forkしてたら0, してなければNoneがくる  1st-processなのでtimer系をここにinstall
            self.naumanni_app.emit('after-start-first-process')


        # set celery as nonblock
        # import tcelery
        # tcelery.setup_nonblocking_producer()

        self.server = HTTPServer(self.application)
        self.server.add_sockets(sockets)

        # run ioloop
        try:
            asyncio.get_event_loop().run_forever()
        finally:
            pass
