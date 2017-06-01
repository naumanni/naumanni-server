# -*- coding:utf-8 -*-
"""
TINY PORT of https://github.com/paularmstrong/normalizr
"""


class Schema(object):
    def normalize(self, value, parent, key, schema, addEntity, visit):
        assert 0, 'not implemented'


class ArraySchema(object):
    def __init__(self, entity):
        self.entity = entity

    def normalize(self, value, parent, key, schema, addEntity, visit):
        result = []
        for v in value:
            result.append(
                visit(v, parent, key, self.entity, addEntity)
            )
        return result


class Entity(Schema):
    def __init__(self, key, definition=None):
        self.key = key
        self.schema = definition or {}

    def getId(self, value):
        return value['id']

    def normalize(self, value, parent, key, schema, addEntity, visit):
        for subkey, subschema in self.schema.items():
            value[subkey] = visit(value[subkey], value, subkey, subschema, addEntity)

        valueId = self.getId(value)
        addEntity(schema, self.getId(value), value)
        return valueId


def normalize(inputData, schema):
    entities = {}

    def addEntity(schema, valueId, value):
        entities.setdefault(schema.key, {})[valueId] = value

    return entities, visit(inputData, None, None, schema, addEntity)


def visit(value, parent, key, schema, addEntity):
    if not hasattr(schema, 'normalize'):
        if isinstance(schema, list):
            assert len(schema) == 1
            schema = ArraySchema(schema[0])
    return schema.normalize(value, parent, key, schema, addEntity, visit)
