# -*- coding: utf-8 -*-
"""WebUI."""
from datetime import datetime
import os
import time
import urllib.parse
import uuid

from flask import Flask, request


class NaumanniWebApp(Flask):
    """NaumanniのAPI受け付け
    """
    def __init__(self, naumanni):
        """init.

        :param NaumanniApp naumanni: NaumanniApp
        """
        super(NaumanniWebApp, self).__init__(__name__)

        self.config.from_object('config')

        self.uptime = time.time()
        self.naumanni = naumanni

        @self.route('/')
        def index():
            return 'hello naumanni'

        @self.route('/status')
        def status():
            from .utils import api_jsonify

            from tornado.ioloop import IOLoop
            io_loop = IOLoop.current()
            selector = io_loop.asyncio_loop._selector

            return api_jsonify({
                'io_loop.handlers': len(io_loop.handlers),
                'io_loop.selector.fds': len(selector._fd_to_key),
            })

        @self.route('/plugin_scripts')
        def plugin_scripts():
            callback = request.args['callback']
            print(callback)
            raise abort(404)

        from .proxy import blueprint as proxy
        self.register_blueprint(proxy, url_prefix='/proxy')

    def register_plugin_blueprint(self, plugin_id, blueprint):
        self.register_blueprint(blueprint, url_prefix='/plugins/{}'.format(plugin_id))
