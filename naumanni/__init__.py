#!/usr/bin/env python
from tornado.httpclient import AsyncHTTPClient
from tornado.platform.asyncio import AsyncIOMainLoop

from .celeryapp import NaumanniCelery

# configure tornado
AsyncIOMainLoop().install()
AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')


# celery
celery = NaumanniCelery()
