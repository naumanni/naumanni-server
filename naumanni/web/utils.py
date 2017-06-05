# -*- coding: utf-8 -*-
import json

from flask import current_app, request


def api_jsonify(*args, **kwargs):
    """flask.json.jsonify"""
    indent = None
    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
        indent = 2
    return current_app.response_class(
        json.dumps(dict(*args, **kwargs), indent=indent),
        mimetype='application/json; charset=utf-8')
