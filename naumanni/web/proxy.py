# -*- coding: utf-8 -*-
import logging
import re

from flask import abort, Blueprint, current_app, request
from tornado import httpclient


blueprint = Blueprint('proxy', __name__)
logger = logging.getLogger(__name__)
https_prefix_rex = re.compile('^https?://?')

PASS_REQUEST_HEADERS = [
    'User-Agent', 'Authorization', 'Referer', 'Accept-Language',
]
PASS_RESPONSE_HEADERS = [
    'Content-Type', 'Date'
]


@blueprint.route('/<path:request_url>')
def proxy(request_url):
    if request.query_string:
        request_url += '?' + request.query_string.decode('utf8')

    if 'Authorization' not in request.headers:
        raise abort(401)

    mo = https_prefix_rex.match(request_url)
    if not mo.group(0).endswith('//'):
        request_url = '{}/{}'.format(mo.group(0), request_url[mo.end():])

    # build header
    # user-agentをpassしていいのかは分からんな...
    headers = _filter_dict(request.headers, PASS_REQUEST_HEADERS)

    try:
        response_body, response_headers = _request_and_filter(request_url, headers)
    except httpclient.HTTPError as exc:
        return current_app.response_class(
            exc.response.body,
            mimetype=exc.response.headers['Content-Type'],
            status='{} {}'.format(exc.code, exc.message),
        )

    print(_filter_dict(response_headers, PASS_RESPONSE_HEADERS))
    return current_app.response_class(
        response_body, headers=_filter_dict(response_headers, PASS_RESPONSE_HEADERS)
    )


def _filter_dict(src, keys):
    dst = {}
    for key in keys:
        if key in src:
            dst[key] = src[key]
    return dst


def _request_and_filter(url, headers):
    http_client = httpclient.HTTPClient()
    response = http_client.fetch(url, headers=headers)

    content_type = response.headers['Content-Type']
    print(content_type)

    return response.body, response.headers
