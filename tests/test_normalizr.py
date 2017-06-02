# -*- coding: utf-8 -*-
from naumanni.normalizr import Entity, denormalize, normalize


account = Entity('accounts')
status = Entity('statuses', {
    'account': account,
})
notification = Entity('notifications', {
    'account': account,
    'status': status,
})


def test_normalize():
    source = {'id': 1, 'account': 'shn'}
    schema = account

    entities, result = normalize(source, schema)
    assert 'accounts' in entities
    assert entities['accounts'][1]['account'] == 'shn'
    assert result == 1

    denormalized = denormalize(result, schema, entities)
    assert denormalized == source


def test_normalize_list_nested():
    source = [
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
    ]
    schema = [status]

    # test normalize
    entities, result = normalize(source, schema)
    assert 'accounts' in entities
    assert 'statuses' in entities
    assert len(entities['accounts']) == 2
    assert len(entities['statuses']) == 3
    assert entities['accounts'][1]['acct'] == 'shn'
    assert entities['accounts'][2]['acct'] == 'nayu'
    assert entities['statuses'][100]['content'] == 'aaa'
    assert result == [100, 101, 102]

    # test denormalize
    denormalized = denormalize(result, schema, entities)
    print(denormalized)
    assert denormalized == source
