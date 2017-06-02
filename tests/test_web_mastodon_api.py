# -*- coding:utf-8 -*-
from naumanni.web.mastodon_api import (
    normalize_mastodon_response
)


def test_normalize_mastodon_response():
    entities, result = normalize_mastodon_response(
        '/accounts/verify_credentials',
        {'id': 123, 'acct': 'shn@oppai.tokyo'}
    )
    assert len(entities['accounts']) == 1
    assert result == 123
