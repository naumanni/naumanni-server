# -*- coding: utf-8 -*-
import json
import os
import pkg_resources
from weakref import ref as weakref


class Plugin(object):
    def __init__(self, app, module_name, plugin_id):
        self._app = weakref(app)
        self._module_name = module_name
        self._id = plugin_id

    @classmethod
    def from_ep(kls, app, ep):
        plugin_id = ep.name
        plugin_class = ep.load()

        return plugin_class(app, ep.module_name, plugin_id)

    @property
    def app_ref(self):
        return self._app

    @property
    def app(self):
        rv = self._app()
        if not rv:
            raise RuntimeError('Application went away')
        return rv

    @property
    def id(self):
        return self._id

    @property
    def js_package_name(self):
        package_json = pkg_resources.resource_string(self._module_name, 'package.json')
        if not package_json:
            return None
        package_json = json.loads(package_json)
        return package_json.get('name')

    @property
    def css_file_path(self):
        fn = pkg_resources.resource_filename(self._module_name, 'css/index.css')
        return fn if os.path.exists(fn) else None
