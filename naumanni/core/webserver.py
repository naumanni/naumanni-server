# -*- coding: utf-8 -*-


from tornado.httpserver import HTTPServer
from tornado.web import Application, FallbackHandler
from tornado.wsgi import WSGIContainer

from ..web import create_webapp


class WebServer(object):
    def __init__(self, naumanni, listen):
        self.naumanni = naumanni
        self.listen = listen

        self.flask_app = create_webapp(self.naumanni)

    def start(self):
        handlers = []

        # websocket handler
        # TODO:

        # web handler
        handlers.append(
            (r'.*', FallbackHandler, {'fallback': WSGIContainer(self.flask_app)})
        )

        application = Application(handlers)
        server = HTTPServer(application)
        server.listen(*self.listen)
