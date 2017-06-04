#!/usr/bin/env python
import logging

from celery import Celery
from celery._state import connect_on_app_finalize

from naumanni.core import NaumanniApp


logger = logging.getLogger(__name__)


class NaumanniCelery(Celery):
    def __init__(self):
        super().__init__('naumanni')
        self.config_from_object('config')


@connect_on_app_finalize
def add_plugin_tasks(celeryapp):
    # TODO: debugはceleryappからとりたい
    celeryapp.naumanni_app = NaumanniApp(debug=True)
