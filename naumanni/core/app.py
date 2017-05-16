# -*- coding: utf-8 -*-

"""Naumanni Core."""

from tornado.ioloop import IOLoop

from .webserver import WebServer


class NaumanniApp(object):
    def __init__(self, debug=False):
        self.debug = debug

        self.webserver = WebServer(self, (8888, '0.0.0.0'))

    def run(self):
        """Naumanniのwebの方を起動する."""
        if self.debug:
            from tornado import autoreload
            autoreload.start()

        self.webserver.start()

        try:
            IOLoop.current().start()
        finally:
            pass
