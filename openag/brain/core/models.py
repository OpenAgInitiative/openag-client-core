__all__ = [
    'ModuleTypeModel', 'ModuleModel', 'ModuleConnectionModel',
    'EnvironmentModel', 'EnvironmentalDataPointModel'
]

from couchdb.mapping import (
    Document, TextField, FloatField, DictField, BooleanField, ListField
)

class ModuleTypeModel(Document):
    _id = TextField()
    name = TextField()
    description = TextField()
    parameters = DictField()
    inputs = DictField()
    outputs = DictField()
    endpoints = DictField()
    procedures = DictField()

class ModuleModel(Document):
    name = TextField()
    type = TextField()
    parameters = DictField()

class ModuleConnectionModel(Document):
    output_module = TextField()
    output_name = TextField()
    input_module = TextField()
    input_name = TextField()

class EnvironmentModel(Document):
    variables = ListField(TextField())

class EnvironmentalDataPointModel(Document):
    environment = TextField()
    variable = TextField()
    is_desired = BooleanField()
    value = TextField()
    timestamp = FloatField()
