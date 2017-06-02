# -*- coding: utf-8 -*-
import re

from werkzeug import cached_property, unescape
from ttp import ttp

tag_rex = re.compile('<(/?.*?)(\s+[^>]*)?/?>')


class JSONBasedModel(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


class Account(JSONBasedModel):
    pass


class Status(JSONBasedModel):
    @cached_property
    def plainContent(self):
        # 雑なRemoveTag
        def handle_tag(m):
            tagname = m.group(1).lower()
            if tagname == '\p':
                return '\n\n'
            elif tagname == 'br':
                return '\n'
        return tag_rex.sub(handle_tag, self.content).rstrip()

    @cached_property
    def urls(self):
        parsed = ttp.Parser().parse(self.plainContent)
        return parsed.urls

    @property
    def urls_without_media(self):
        rv = []
        for url in self.urls:
            for media in self.media_attachments:
                if media.get('text_url', None) == url:
                    break
            else:
                rv.append(url)
        return rv


class Notification(JSONBasedModel):
    pass
