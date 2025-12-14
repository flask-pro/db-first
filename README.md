# DB-First

Web-framework independent CRUD tools for working with database via SQLAlchemy.

<!--TOC-->

- [DB-First](#db-first)
  - [Features](#features)
  - [Installation](#installation)
  - [Examples](#examples)
    - [Full example](#full-example)

<!--TOC-->

## Features

* DBAL - database access layer.
* Actions templates.
* Bulk methods for create, read, update and delete object from database.
* Method of paginating data.
* StatementMaker class for create query 'per-one-model'.
* Marshmallow (https://github.com/marshmallow-code/marshmallow) schemas for serialization input data.
* Marshmallow schemas for deserialization SQLAlchemy result object to `dict`.
* Datetime with UTC timezone validation in `BaseSchema`.

## Installation

Recommended using the latest version of Python. DB-First supports Python 3.12 and newer.

Install and update using `pip`:

```shell
$ pip install -U db_first
```

## Examples

### Full example

```python
from db_first.actions import BaseAction
from db_first.base_model import ModelMixin
from db_first.dbal import SqlaDBAL
from db_first.dbal.exceptions import DBALObjectNotFoundException
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


class ItemsDBAL(SqlaDBAL[Items]):
    """Items DBAL."""


class ItemSchema(Schema):
    id = fields.UUID()
    data = fields.String()
    created_at = fields.DateTime()


class CreateItemAction(BaseAction):
    def validate(self) -> None:
        ItemSchema(exclude=['id', 'created_at']).load(self._data)

    def action(self) -> Items:
        return ItemsDBAL(self._session).create(**self._data)


class ReadItemAction(BaseAction):
    def validate(self) -> None:
        ItemSchema().load(self._data)

    def action(self) -> Items:
        return ItemsDBAL(self._session).read(**self._data)


class UpdateItemAction(BaseAction):
    def validate(self) -> None:
        ItemSchema(only=['id', 'data']).load(self._data)

    def action(self) -> Items:
        return ItemsDBAL(self._session).update(**self._data)


class DeleteItemAction(BaseAction):
    def validate(self) -> None:
        ItemSchema(only=['id']).load(self._data)

    def action(self) -> None:
        return ItemsDBAL(self._session).delete(**self._data)


if __name__ == '__main__':
    new_item = CreateItemAction(session, {'data': 'data'}).run()
    print('New item:', new_item)

    item = ReadItemAction(session, {'id': new_item.id}).run()
    print('Item:', item)

    updated_item = UpdateItemAction(session, {'id': new_item.id, 'data': 'updated_data'}).run()
    print('Updated item:', updated_item)

    DeleteItemAction(session, {'id': new_item.id}).run()
    try:
        item = ReadItemAction(session, {'id': new_item.id}).run()
    except DBALObjectNotFoundException:
        print('Deleted item.')
```
