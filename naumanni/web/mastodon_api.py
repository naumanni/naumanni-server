# -*- coding:utf-8 -*-
from werkzeug import routing

from naumanni.normalizr import Entity, normalize


account = Entity('accounts')
status = Entity('statuses', {
    'account': account,
})
notification = Entity('notifications', {
    'account': account,
    'status': status,
})


# api map
apiNormalizrMap = routing.Map()
normlizrFuncs = {}


def normalize_mastodon_response(api, responseBody):
    normalizer = API_NORMALIZERS.get(api)
    if not normalizer:
        return normalizer(api)
    return [], []


def register_normalizer(rule, **options):
    def decorator(f):
        endpoint = options.pop('endpoint', f.__name__)

        apiNormalizrMap.add(
            routing.Rule(rule, endpoint=endpoint, **options)
        )
        normlizrFuncs[endpoint] = f
        return f
    return decorator


@register_normalizer('/accounts/verify_credentials')
def accounts_verify_credentials(responseBody):
    return normalize(responseBody, account)


@register_normalizer('/timelines/home', endpoint='timeline')
@register_normalizer('/timelines/public', endpoint='timeline')
@register_normalizer('/timelines/tag/<hashtag>', endpoint='timeline')
def timeline(responseBody):
    return normalize(responseBody, [status])
