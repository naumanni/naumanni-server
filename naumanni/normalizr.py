# -*- coding:utf-8 -*-
"""
TINY PORT of https://github.com/paularmstrong/normalizr
"""


class Schema(object):
    def normalize(self, value, parent, key, schema, addEntity, visit):
        assert 0, 'not implemented'

    def denormalize(self, inputData, unvisit):
        assert 0, 'not implemented'


class ArraySchema(object):
    def __init__(self, entity):
        self.entity = entity

    def normalize(self, inputData, parent, key, schema, addEntity, visit):
        assert isinstance(inputData, (list, tuple))

        result = []
        for v in inputData:
            result.append(
                visit(v, parent, key, self.entity, addEntity)
            )
        return result

    def denormalize(self, inputData, unvisit):
        assert isinstance(inputData, (list, tuple))

        result = []
        for value in inputData:
            result.append(
                unvisit(value, self.entity)
            )
        return result


class Entity(Schema):
    def __init__(self, key, klass, definition=None):
        self.key = key
        self.klass = klass
        self.schema = definition or {}

    def getId(self, inputData):
        return inputData['id']

    def normalize(self, inputData, parent, key, schema, addEntity, visit):
        assert isinstance(inputData, dict) or inputData is None

        if inputData is None:
            return None

        inputData = inputData.copy()

        for subkey, subschema in self.schema.items():
            if subkey in inputData:
                inputData[subkey] = visit(inputData[subkey], inputData, subkey, subschema, addEntity)

        valueId = self.getId(inputData)
        addEntity(schema, self.getId(inputData), self.klass(**inputData))
        return valueId

    def denormalize(self, inputData, unvisit):
        assert isinstance(inputData, dict)

        for subkey, subschema in self.schema.items():
            inputData[subkey] = unvisit(inputData[subkey], subschema)

        return inputData


def normalize(inputData, schema):
    entities = {}

    def addEntity(schema, valueId, value):
        entities.setdefault(schema.key, {})[valueId] = value

    return entities, visit(inputData, None, None, schema, addEntity)


def denormalize(inputData, schema, entities):
    def _univist(inputData, schema):
        schema = schemaize(schema)

        if isinstance(schema, Entity):
            if inputData is None:
                return None
            entity = entities[schema.key][inputData].to_dict()
            return schema.denormalize(entity, _univist)
        else:
            return schema.denormalize(inputData, _univist)

    return _univist(inputData, schema)


def visit(value, parent, key, schema, addEntity):
    schema = schemaize(schema)
    return schema.normalize(value, parent, key, schema, addEntity, visit)


def schemaize(schema):
    if not hasattr(schema, 'normalize'):
        if isinstance(schema, list):
            assert len(schema) == 1
            schema = ArraySchema(schema[0])
    return schema
