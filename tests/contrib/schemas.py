from datetime import timezone

from marshmallow import fields
from marshmallow import validate

from src.db_first.schemas import BaseSchema


class IdSchema(BaseSchema):
    id = fields.UUID(required=True)


class FatherSchema(IdSchema):
    first = fields.String(required=True)
    second = fields.String()
    created_at = fields.DateTime()


class ChildSchema(IdSchema):
    first = fields.String(required=True)
    second = fields.String()
    parent_id = fields.UUID()


class ParentSchema(IdSchema):
    first = fields.String(required=True)
    second = fields.String(allow_none=False)
    father_id = fields.UUID()
    created_at = fields.AwareDateTime(default_timezone=timezone.utc)
    father = fields.Nested(FatherSchema)
    children = fields.Nested(ChildSchema, many=True)


class ParentSchemaParametersOfPaginate(BaseSchema):
    id = fields.UUID()
    ids = fields.List(fields.UUID())
    page = fields.Integer(validate=validate.Range(min=0))
    max_per_page = fields.Integer(validate=validate.Range(min=0))
    per_page = fields.Integer(validate=validate.Range(min=0))
    sort_created_at = fields.String(validate=validate.OneOf(['asc', 'desc']))
    search_first = fields.String()
    first = fields.String()
    start_created_at = fields.DateTime()
    end_created_at = fields.DateTime()
    include_metadata = fields.Boolean(validate=validate.OneOf([True]))
    fields = fields.List(fields.String())


class Paginate(BaseSchema):
    page = fields.Integer(allow_none=False)
    per_page = fields.Integer(allow_none=False)
    pages = fields.Integer(allow_none=False)
    total = fields.Integer(allow_none=False)


class MetadataSchema(BaseSchema):
    pagination = fields.Nested(Paginate)


class ParentSchemaOfPaginate(BaseSchema):
    __skipped_keys__ = ('items',)

    _metadata = fields.Nested(MetadataSchema)
    items = fields.Nested(ParentSchema, many=True)
