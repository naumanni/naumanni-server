# -*- coding: utf-8 -*-


class JSONBasedModel(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    def to_dict(self):
        return self.__dict__


class Account(JSONBasedModel):
    pass


class Status(JSONBasedModel):
    pass


class Notification(JSONBasedModel):
    pass
