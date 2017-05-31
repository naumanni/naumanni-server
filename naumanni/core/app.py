# -*- coding: utf-8 -*-

"""Naumanni Core."""

import asyncio

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
            asyncio.get_event_loop().run_forever()
        finally:
            pass
