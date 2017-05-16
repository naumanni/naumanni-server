# -*- coding: utf-8 -*-

"""CLI Main."""

from itertools import groupby
import logging
import os
import re
import sys

# community module
import click
from click.core import Context

from naumanni.core import NaumanniApp


# project module
logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', is_flag=True)
@click.pass_context
def cli_main(ctx, debug):
    """`crcr`の起点.

    :param Context ctx: Context
    """
    # initialize console logging
    _init_logging(debug)

    ctx.obj = NaumanniApp(debug=debug)


def _init_logging(debug=False):
    if sys.stderr.isatty():
        # if we are attached to tty, use colorful.
        fh = logging.StreamHandler(sys.stderr)
        try:
            from ..logger import NiceColoredFormatter
            # 色指示子で9charsとる
            fh.setFormatter(NiceColoredFormatter(
                '%(nice_levelname)-14s %(nice_name)-33s: %(message)s',
            ))
        except ImportError:
            fh.setFormatter(logging.Formatter(
                '%(levelname)-5s %(name)-24s: %(message)s',
            ))

        root_logger = logging.getLogger()
        root_logger.addHandler(fh)
        root_logger.setLevel(logging.DEBUG if debug else logging.INFO)


@cli_main.command('run')
@click.pass_context
def cli_main_run(ctx):
    """CircleCoreの起動."""
    # ctx.obj.ipc_socket = 'ipc://' + ipc_socket
    app = ctx.obj

    logger.info('Master process PID:%s', os.getpid())

    # run hub
    app.run()
