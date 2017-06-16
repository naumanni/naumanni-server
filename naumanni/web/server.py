# -*- coding: utf-8 -*-
import asyncio
import collections
import logging
import functools
import json
import multiprocessing
import os
import signal
import socket
import time

import psutil
from tornado import gen, ioloop, iostream, routing, web
from tornado.httpserver import HTTPServer
from tornado.wsgi import WSGIContainer
import tornado.netutil
import tornado.process
from tornado.platform.asyncio import AsyncIOMainLoop

from .base import NaumanniRequestHandlerMixIn
from .proxy import APIProxyHandler
from .websocket import WebsocketProxyHandler


logger = logging.getLogger(__name__)
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 5
REDIS_SERVER_STATUS_KEY = 'naumanni:server_status'
ChildProc = collections.namedtuple('ChildProc', ['proc', 'pipe_reader', 'pipe_writer'])
DELIMITER = b'\x00'


class NaumanniWebApplication(web.Application):
    def add_plugin_handlers(self, plugin_id, handlers):
        """plugin apiを追加する"""

        # plugin apiのprefixをURLに追加する
        path_prefix = '/plugins/{}/'.format(plugin_id)
        replaced_handlers = []
        for rule in handlers:
            if isinstance(rule, (tuple, list)):
                if isinstance(rule[0], str):
                    if not rule[0].startswith('/'):
                        raise ValueError('invalid plugin url path, must be startswith \'/\'')
                    rule = (path_prefix + rule[0][1:], *rule[1:])
                else:
                    assert 0, 'not implemented'
            else:
                assert 0, 'not implemented'

            replaced_handlers.append(rule)

        # 登録
        self.wildcard_router.add_rules(
            [(path_prefix + '.*$', web._ApplicationRouter(self, replaced_handlers))]
        )


class WebServerBase(object):
    def __init__(self, naumanni_app, listen):
        self.naumanni_app = naumanni_app
        self.listen = listen

        self.init()

    def init(self):
        handlers = [
            (r'/proxy/(?P<request_url>.+)', APIProxyHandler),
            (r'/ws/(?P<request_url>.+)', WebsocketProxyHandler),
            (r'/status', StatusAPIHandler),
            (r'/ping', PingAPIHandler),
        ]
        self.application = NaumanniWebApplication(
            handlers,
            compress_response=True,
            debug=self.naumanni_app.debug,
            autoreload=False,
            websocket_ping_interval=3,
            naumanni_app=self.naumanni_app,
        )
        self.naumanni_app.emit('after-initialize-webserver', webserver=self)

    def _run_server(self, task_id):
        assert AsyncIOMainLoop().initialized()

        # run self.naumanni_app.setup(task_id) synchronusly
        io_loop = ioloop.IOLoop.current()
        io_loop.run_sync(functools.partial(self.naumanni_app.setup, task_id))

        self.http_server = HTTPServer(self.application)
        self.http_server.add_sockets(self.sockets)

        # install signal handlers for child proc
        install_child_signal_handlers(self)

        # run ioloop
        ioloop.IOLoop.current().start()

    async def save_server_status(self, status):
        """statusをredisに保存する"""
        async with self.naumanni_app.get_async_redis() as redis:
            status['date'] = time.time()
            await redis.set(REDIS_SERVER_STATUS_KEY, json.dumps(status))

    async def collect_server_status(self):
        raise NotImplementedError()


class DebugWebServer(WebServerBase):
    def start(self):
        self.sockets = tornado.netutil.bind_sockets(*self.naumanni_app.config.listen)
        # debugなのでautoreloadする
        AsyncIOMainLoop().install()
        from tornado import autoreload
        autoreload.start()

        self._run_server(None)


class ForkedWebServer(WebServerBase):
    def start(self):
        self.sockets = tornado.netutil.bind_sockets(*self.naumanni_app.config.listen)
        children = self.fork(0)

        # こっからはMasterの世界
        # use asyncio for ioloop
        AsyncIOMainLoop().install()
        self.children = [ChildProc(
            proc,
            iostream.PipeIOStream(fdr),
            iostream.PipeIOStream(fdw),
        ) for proc, fdr, fdw in children]

        # run self.naumanni_app.setup(None) synchronusly
        io_loop = ioloop.IOLoop.current()
        io_loop.run_sync(functools.partial(self.naumanni_app.setup, None))

        # master run loop
        io_loop.start()

        for task_id, child in enumerate(self.children):
            child.proc.join()

    def is_master(self):
        return getattr(self.naumanni_app, 'task_id', None) is None

    def fork(self, num_processes):
        # install signal handlers for master proc
        install_master_signal_handlers(self)

        if num_processes == 0:
            num_processes = multiprocessing.cpu_count()

        children = []
        for task_id in range(num_processes):
            # scoketpair使えば良い気がする
            fdr, fdw = os.pipe()
            fdr2, fdw2 = os.pipe()
            proc = multiprocessing.Process(target=self._run_child, args=(task_id, fdr, fdw2))
            children.append((proc, fdr2, fdw))

            proc.start()

        return children

    def _run_child(self, task_id, pipe_reader, pipe_writer):
        logger.info('Child process PID:%s', os.getpid())

        # use asyncio for ioloop
        AsyncIOMainLoop().install()

        # listen pipe
        self.pipe_reader = iostream.PipeIOStream(pipe_reader)
        self.pipe_writer = iostream.PipeIOStream(pipe_writer)
        tornado.process._reseed_random()
        self._run_server(task_id)

    def on_master_pipe_can_read(self, child):
        """child -> masterのpipeに何か書き込みがあれば呼ばれる"""
        async def _process_child_request(f):
            self.unwait_child_commands()

            try:
                request = json.loads(f.result()[:-len(DELIMITER)])
                logger.info('on_master_pipe_can_read %s %r', child.proc.pid, request)

                if request.get('request') == STATUS_REQUEST:
                    status = await self.collect_server_status()
                    await child.pipe_writer.write(
                        json.dumps(status).encode('latin1') + DELIMITER
                    )
            finally:
                self.wait_child_commands()

        ioloop.IOLoop.instance().add_future(
            child.pipe_reader.read_until(DELIMITER),
            _process_child_request
        )

    # server status
    async def collect_server_status(self):
        if not self.is_master():
            return await self.get_status_from_master()

        for child in self.children:
            os.kill(child.proc.pid, signal.SIGUSR1)

        keys = ['io_loop.handlers', 'io_loop.selector.fds', 'process.uss', 'process.rss']
        status = {'process': {}}

        for idx, child in enumerate(self.children):
            child_status = await child.pipe_reader.read_until(DELIMITER)
            child_status = json.loads(child_status[:-len(DELIMITER)])
            status['process'][idx] = child_status

            for key in keys:
                status[key] = status.get(key, 0) + child_status[key]

        master_status = _collect_status()
        status['process']['master'] = master_status
        for key in keys:
            status[key] = status.get(key, 0) + master_status[key]

        return status


# utility page
class StatusAPIHandler(web.RequestHandler, NaumanniRequestHandlerMixIn):
    async def get(self):
        last_status = await self._get_status()
        last_time = last_status['date'] if last_status else None

        # sind signal
        os.kill(os.getppid(), signal.SIGUSR1)

        while True:
            status = await self._get_status()
            if status and status['date'] != last_time:
                break

            await gen.sleep(0.5)

        self.write(status)
        await self.flush()

    async def _get_status(self):
        async with self.naumanni_app.get_async_redis() as redis:
            data = await redis.get(REDIS_SERVER_STATUS_KEY)
            return json.loads(data) if data else None


class PingAPIHandler(web.RequestHandler):
    async def get(self):
        self.write('pong')
        await self.flush()


# signal handling
def install_master_signal_handlers(webserver):
    # SIGTERMされてもちゃんと終了するように
    def stop_handler(webserver, sig, frame):
        io_loop = ioloop.IOLoop.current()
        try:
            for child in webserver.children:
                try:
                    os.kill(child.proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            io_loop.add_callback_from_signal(io_loop.stop)
        except Exception as exc:
            logger.exception(exc)

    handler = functools.partial(stop_handler, webserver)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGQUIT, handler)
    signal.signal(signal.SIGTERM, handler)

    # status情報収集用ハンドラ
    def status_handler(webserver, sig, frame):
        async def show_server_status(webserver):
            status = await webserver.collect_server_status()
            await webserver.save_server_status(status)
            logger.info('Server status: %r', status)
        ioloop.IOLoop.instance().add_callback_from_signal(show_server_status, webserver)

    signal.signal(signal.SIGUSR1, functools.partial(status_handler, webserver))


def install_child_signal_handlers(webserver):
    """子プロセスがgracefulに死ぬように"""
    def stop_handler(webserver, sig, frame):
        io_loop = ioloop.IOLoop.instance()

        def stop_loop(deadline):
            now = time.time()
            if now < deadline and has_ioloop_tasks(io_loop):
                logger.info('Waiting for next tick...')
                io_loop.add_timeout(now + 1, stop_loop, deadline)
            else:
                io_loop.stop()
                logger.info('Shutdown finally')

        def shutdown():
            logger.info('Stopping http server')
            webserver.naumanni_app.emit('before-stop-server')
            webserver.http_server.stop()
            logger.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
            stop_loop(time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)

        io_loop.add_callback_from_signal(shutdown)

    handler = functools.partial(stop_handler, webserver)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGQUIT, handler)
    signal.signal(signal.SIGTERM, handler)

    def status_handler(webserver, sig, frame):
        io_loop = ioloop.IOLoop.instance()

        async def _send_status(webserver):
            status = _collect_status()
            await webserver.pipe_writer.write(json.dumps(status).encode('latin1') + DELIMITER)

        io_loop.add_callback_from_signal(_send_status, webserver)

    signal.signal(signal.SIGUSR1, functools.partial(status_handler, webserver))


def _collect_status():
    io_loop = ioloop.IOLoop.instance()
    selector = io_loop.asyncio_loop._selector

    proc = psutil.Process()
    with proc.oneshot():
        mem = proc.memory_full_info()

        status = {
            'io_loop.handlers': len(io_loop.handlers),
            'io_loop.selector.fds': len(selector._fd_to_key),
            'process.uss': mem.uss / 1024.0 / 1024.0,
            'process.rss': mem.rss / 1024.0 / 1024.0,
        }
    return status


def has_ioloop_tasks(io_loop):
    if hasattr(io_loop, '_callbacks'):
        return io_loop._callbacks or io_loop._timeouts
    elif hasattr(io_loop, 'handlers'):
        return len(io_loop.handlers)
    return False
