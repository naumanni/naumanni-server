# -*- coding: utf-8 -*-
from naumanni.normalizr import Entity, normalize


account = Entity('accounts')
status = Entity('statuses', {
    'account': account,
})
notification = Entity('notifications', {
    'account': account,
    'status': status,
})


def test_normalize():
    entities, result = normalize({'id': 1, 'account': 'shn'}, account)
    assert 'accounts' in entities
    assert entities['accounts'][1]['account'] == 'shn'
    assert result == 1

    entities, result = normalize(
        [
            {
                'id': 100,
                'account': {
                    'id': 1,
                    'acct': 'shn'
                },
                'content': 'aaa',
            },
            {
                'id': 101,
                'account': {
                    'id': 2,
                    'acct': 'nayu'
                },
                'content': 'bbb',
            },
            {
                'id': 102,
                'account': {
                    'id': 1,
                    'acct': 'shn'
                },
                'content': 'ccc',
            },
        ],
        [status]
    )

    assert 'accounts' in entities
    assert 'statuses' in entities
    assert len(entities['accounts']) == 2
    assert len(entities['statuses']) == 3
    assert entities['accounts'][1]['acct'] == 'shn'
    assert entities['accounts'][2]['acct'] == 'nayu'
    assert entities['statuses'][100]['content'] == 'aaa'
    assert result == [100, 101, 102]
