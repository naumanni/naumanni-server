# -*- coding: utf-8 -*-


class NaumanniRequestHandlerMixIn(object):
    @property
    def naumanni_app(self):
        return self.application.settings['naumanni_app']
