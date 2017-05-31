# -*- coding: utf-8 -*-
import logging
import json
import re
import time
from urllib.parse import urlparse

from tornado import gen, httpclient
from tornado.websocket import WebSocketHandler, websocket_connect, WebSocketClientConnection, WebSocketError

logger = logging.getLogger(__name__)
https_prefix_rex = re.compile('^wss?://?')


class WebsocketProxyHandler(WebSocketHandler):
    """proxyる

    :param UUID slave_uuid:
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.peer = None  # 相手先MastodonのWS
        self.closed = False

    @gen.coroutine
    def open(self, request_url):
        # TODO: 最近のアクセス状況をみて、無制限に接続されないように
        if self.request.query:
            request_url += '?' + self.request.query
        mo = https_prefix_rex.match(request_url)
        if not mo.group(0).endswith('//'):
            request_url = '{}/{}'.format(mo.group(0), request_url[mo.end():])

        logger.info('peer ws: %s', request_url)
        request = httpclient.HTTPRequest(request_url)
        try:
            self.peer = yield websocket_connect(request, ping_interval=self.ping_interval)
        except Exception as e:
            logger.error('peer connect failed: %r', e)
            raise
        self.listen_peer()

    # WebsocketHandler overrides
    @gen.coroutine
    def on_message(self, plain_msg):
        message = json.loads(plain_msg)
        logger.debug('client: %r' % message)

    def on_close(self):
        """センサーとの接続が切れた際に呼ばれる."""
        logger.debug('connection closed: %s', self)
        self.closed = True

    def check_origin(self, origin):
        """nginxの内側にいるので、check_originに細工が必要"""
        parsed_origin = urlparse(origin)
        origin = parsed_origin.netloc
        origin = origin.lower()

        key = 'X-Forwarded-Server' if 'X-Forwarded-Server' in self.request.headers else 'Host'
        host = self.request.headers.get(key)

        return origin == host

    # original
    @gen.coroutine
    def listen_peer(self):
        """閉じられるまで、server側wsのメッセージをlistenする"""
        logger.debug('listen peer')
        while not self.closed:
            raw = yield self.peer.read_message()
            if raw is None:
                # connetion was closed
                logger.info('server conncetion closed')
                self.closed = True
                self.close()

            self.on_new_message_from_server(json.loads(raw))

    def pinger(self):
        data = str(time.time()).encode('utf8')
        logger.debug('pinger: %r', data)
        self.ping(data)

    def on_new_message_from_server(self, message):
        """Mastodonサーバから新しいメッセージが来た"""
        logger.debug('server: %r...', repr(message)[:40])

        # clientにpass
        self.write_message(message)
