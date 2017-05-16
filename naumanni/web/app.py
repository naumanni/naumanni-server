# -*- coding: utf-8 -*-

"""WebUI."""

# system module
from datetime import datetime
import os
import time
import urllib.parse
import uuid

# community module
from flask import Flask

# project module


class NaumanniWebApp(Flask):
    """NaumanniのAPI受け付け
    """
    def __init__(self, naumanni):
        """init.

        :param NaumanniApp naumanni: NaumanniApp
        """
        super(NaumanniWebApp, self).__init__(__name__)

        self.uptime = time.time()
        self.naumanni = naumanni

        @self.route('/')
        def _index():
            return 'hello naumanni'
