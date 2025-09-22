from db_first import BaseCRUD
from db_first.base_model import ModelMixin
from db_first.decorators import Validation
from db_first.mixins import CreateMixin
from db_first.mixins import DeleteMixin
from db_first.mixins import ReadMixin
from db_first.mixins import UpdateMixin
from marshmallow import fields
from marshmallow import Schema
from sqlalchemy import create_engine
from sqlalchemy import Result
from sqlalchemy.exc import NoResultFound
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


class IdSchema(Schema):
    id = fields.UUID()


class SchemaOfCreate(Schema):
    data = fields.String()


class SchemaOfUpdate(IdSchema, SchemaOfCreate):
    """Update item schema."""


class OutputSchema(SchemaOfUpdate):
    created_at = fields.DateTime()


class ItemController(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
    class Meta:
        session = session
        model = Items
        sortable = ['created_at']

    @Validation.input(SchemaOfCreate)
    @Validation.output(OutputSchema, serialize=True)
    def create(self, **data) -> Result:
        return super().create_object(**data)

    @Validation.input(IdSchema, keys=['id'])
    @Validation.output(OutputSchema, serialize=True)
    def read(self, **data) -> Result:
        return super().read_object(data['id'])

    @Validation.input(SchemaOfUpdate)
    @Validation.output(OutputSchema, serialize=True)
    def update(self, **data) -> Result:
        return super().update_object(**data)

    @Validation.input(IdSchema, keys=['id'])
    def delete(self, **data) -> None:
        super().delete_object(**data)


if __name__ == '__main__':
    item_controller = ItemController()

    new_item = item_controller.create(data='first')
    print('Item as dict:', new_item)

    item = item_controller.read(id=new_item['id'])
    print('Item as dict:', item)

    updated_item = item_controller.update(id=new_item['id'], data='updated_first')
    print('Item as dict:', updated_item)

    item_controller.delete(id=new_item['id'])
    try:
        item = item_controller.read(id=new_item['id'])
    except NoResultFound:
        print('Item deleted:', item)
