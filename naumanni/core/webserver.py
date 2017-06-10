# -*- coding: utf-8 -*-
from tornado.httpserver import HTTPServer
from tornado.web import Application, FallbackHandler
from tornado.wsgi import WSGIContainer

from ..web import create_webapp, WebsocketProxyHandler


class WebServer(object):
    def __init__(self, naumanni, listen):
        self.naumanni = naumanni
        self.listen = listen
        self.flask_app = create_webapp(self.naumanni)

    def start(self):
        handlers = [
            (r'/ws/(?P<request_url>.+)', WebsocketProxyHandler),
            (r'.*', FallbackHandler, {'fallback': WSGIContainer(self.flask_app)})
        ]

        application = Application(
            handlers,
            flask_app=self.flask_app,
            websocket_ping_interval=3,
        )
        server = HTTPServer(application)
        server.listen(*self.listen)

        self.naumanni.emit('after-initialize-webserver', webserver=self)
