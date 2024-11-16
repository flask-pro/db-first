from uuid import UUID

from db_first import BaseCRUD
from db_first.base_model import ModelMixin
from db_first.mixins import CreateMixin
from db_first.mixins import DeleteMixin
from db_first.mixins import PaginationMixin
from db_first.mixins import ReadMixin
from db_first.mixins import UpdateMixin
from marshmallow import fields
from marshmallow import Schema
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Session

engine = create_engine('sqlite://', echo=True, future=True)
session = Session(engine)
Base = declarative_base()


class Items(ModelMixin, Base):
    __tablename__ = 'items'
    data: Mapped[str] = mapped_column(comment='Data of item.')


Base.metadata.create_all(engine)


class InputSchemaOfCreate(Schema):
    data = fields.String()


class InputSchemaOfUpdate(InputSchemaOfCreate):
    id = fields.UUID()


class OutputSchema(InputSchemaOfUpdate):
    created_at = fields.DateTime()


class ItemController(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, PaginationMixin, BaseCRUD):
    class Meta:
        session = session
        model = Items
        input_schema_of_create = InputSchemaOfCreate
        input_schema_of_update = InputSchemaOfUpdate
        output_schema_of_create = OutputSchema
        output_schema_of_read = OutputSchema
        output_schema_of_update = OutputSchema
        schema_of_paginate = OutputSchema
        sortable = ['created_at']


if __name__ == '__main__':
    item = ItemController()

    first_new_item = item.create(data={'data': 'first'})
    print('Item as object:', first_new_item)
    second_new_item = item.create(data={'data': 'second'}, serialize=True)
    print('Item as dict:', second_new_item)

    first_item = item.read(first_new_item.id)
    print('Item as object:', first_item)
    first_item = item.read(first_new_item.id, serialize=True)
    print('Item as dict:', first_item)

    updated_first_item = item.update(data={'id': first_new_item.id, 'data': 'updated_first'})
    print('Item as object:', updated_first_item)
    updated_second_item = item.update(
        data={'id': UUID(second_new_item['id']), 'data': 'updated_second'}, serialize=True
    )
    print('Item as dict:', updated_second_item)

    items = item.paginate(sort_created_at='desc')
    print('Items as objects:', items)
    items = item.paginate(sort_created_at='desc', serialize=True)
    print('Items as dicts:', items)
