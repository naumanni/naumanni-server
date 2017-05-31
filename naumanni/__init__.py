from tornado.httpclient import AsyncHTTPClient
from tornado.platform.asyncio import AsyncIOMainLoop


# configure tornado
AsyncIOMainLoop().install()
AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
