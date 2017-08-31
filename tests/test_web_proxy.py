# -*- coding:utf-8 -*-
import ssl

import tornado.httpclient
import tornado.web
from tornado.testing import AsyncHTTPTestCase

from naumanni.web.proxy import (
    https_prefix_rex, mastodon_api_rex,
)
from naumanni.web.proxy import APIProxyHandler


def test_rex():
    """使っている正規表現のテスト"""
    mo = https_prefix_rex.match('http://')
    assert mo
    mo = https_prefix_rex.match('https://')
    assert mo
    mo = https_prefix_rex.match('http:/')
    assert mo
    mo = https_prefix_rex.match('https:/')
    assert mo

    mo = mastodon_api_rex.match('https://friends.nico/api/v1/accounts/verify_credentials')
    assert mo.groups() == ('friends.nico', '/accounts/verify_credentials')

    mo = mastodon_api_rex.match('https://friends.nico/api/v1/accounts/verify_credentials?hogehoge')
    assert mo.groups() == ('friends.nico', '/accounts/verify_credentials')


class MockAPIProxyHandler(APIProxyHandler):
    def is_need_authorization(self):
        return False


class TestProxyHandlerCaseBase(AsyncHTTPTestCase):
    def setUp(self):
        self.path = '/proxy/https://friends.nico/api/v1/accounts/verify_credentials'
        super().setUp()

    def get_app(self):
        class _TestApplication(tornado.web.Application):
            def __init__(self, handler):
                handlers = [
                    (r'/proxy/(?P<request_url>.+)', handler),
                ]
                super().__init__(handlers)
        handler = self._get_mock_handler()
        return _TestApplication(handler)

    def _get_mock_handler(self):
        raise NotImplementedError


class ServerErrorProxyTestCase1(TestProxyHandlerCaseBase):
    def test_error(self):
        response = self.fetch(self.path)
        assert response.code == 400

    def _get_mock_handler(self):
        class _MockAPIProxyHandler(MockAPIProxyHandler):
            async def _pass_request(self, request_url):
                raise tornado.httpclient.HTTPError(503)
        return _MockAPIProxyHandler


class ServerErrorProxyTestCase2(TestProxyHandlerCaseBase):
    def test_error(self):
        response = self.fetch(self.path)
        assert response.code == 404

    def _get_mock_handler(self):
        class _MockAPIProxyHandler(MockAPIProxyHandler):
            async def _pass_request(self, request_url):
                raise tornado.httpclient.HTTPError(404)
        return _MockAPIProxyHandler


class SSLErrorProxyTestCase(TestProxyHandlerCaseBase):
    def test_error(self):
        response = self.fetch(self.path)
        assert response.code == 400

    def _get_mock_handler(self):
        class _MockAPIProxyHandler(MockAPIProxyHandler):
            async def _pass_request(self, request_url):
                raise ssl.SSLError()
        return _MockAPIProxyHandler
