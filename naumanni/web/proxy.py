# -*- coding: utf-8 -*-
import logging
import json
import re

from flask import abort, Blueprint, current_app, request
from tornado import httpclient
from werkzeug.exceptions import NotFound

from .mastodon_api import normalize_mastodon_response, denormalize_mastodon_response


blueprint = Blueprint('proxy', __name__)
logger = logging.getLogger(__name__)
https_prefix_rex = re.compile('^https?://?')
mastodon_api_rex = re.compile(r'^https?://(?P<host>[^/]+)/api/v1(?P<api>/.*?)(?:\?.*)?$')


PASS_REQUEST_HEADERS = [
    'Accept', 'Accept-Language', 'Authorization', 'Content-Type', 'Referer', 'User-Agent'
]
PASS_RESPONSE_HEADERS = [
    'Content-Type', 'Date'
]


@blueprint.route('/<path:request_url>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def proxy(request_url):
    if request.query_string:
        request_url += '?' + request.query_string.decode('utf8')

    # fix url
    mo = https_prefix_rex.match(request_url)
    if not mo.group(0).endswith('//'):
        request_url = '{}/{}'.format(mo.group(0), request_url[mo.end():])

    # parse api
    mo = mastodon_api_rex.match(request_url)
    host, api = mo.groups() if mo else (None, None)

    # apps作る以外は、認証なければNGにしておく
    if (api == '/apps' and request.method == 'POST'):
        pass
    elif 'Authorization' not in request.headers:
        raise abort(401)

    # build header
    # user-agentをpassしていいのかは分からんな...
    headers = _filter_dict(request.headers, PASS_REQUEST_HEADERS)

    try:
        response_body, response_headers = _request_and_filter(request_url, request, headers)
    except httpclient.HTTPError as exc:
        return current_app.response_class(
            exc.response.body,
            mimetype=exc.response.headers['Content-Type'],
            status='{} {}'.format(exc.code, exc.message),
        )

    return current_app.response_class(
        response_body, headers=_filter_dict(response_headers, PASS_RESPONSE_HEADERS)
    )


def _filter_dict(src, keys):
    dst = {}
    for key in keys:
        if key in src:
            dst[key] = src[key]
    return dst


def _request_and_filter(url, request, headers):
    http_client = httpclient.HTTPClient()
    response = http_client.fetch(
        url,
        headers=headers,
        method=request.method,
        body=request.stream.read() if request.method not in ('HEAD', 'GET') else None
    )

    body = _filter_response(url, response)

    return body, response.headers


def _filter_response(url, response):
    mo = mastodon_api_rex.match(url)
    host, api = mo.groups() if mo else (None, None)
    content_type = response.headers['Content-Type']
    if ';' in content_type:
        content_type = content_type.split(';')[0].lower()

    # API responseじゃなかったらlogして返す
    if not (api and content_type == 'application/json'):
        logger.warning('unknown request: %s %s', api, content_type)
        return response.body

    try:
        responseBody = json.loads(response.body)
        entities, result = normalize_mastodon_response(api, responseBody)
        # TODO: _filter_entitiesをどっかにまとめる
        from .proxy import _filter_entities
        _filter_entities(entities)
        denormalized = denormalize_mastodon_response(api, result, entities)
        return json.dumps(denormalized)
    except NotFound:
        return response.body


def _filter_entities(entities):
    for key in entities.keys():
        def _result_hook(result, kwargs):
            kwargs['objects'] = entities[key] = result
            return kwargs

        current_app.naumanni.emit(
            'filter-{}'.format(key),
            objects=entities[key], entities=entities,
            _result_hook=_result_hook)
