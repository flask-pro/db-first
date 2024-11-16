from typing import Any

from sqlalchemy.engine import Result

from .exc import MetaNotFound
from .exc import OptionNotFound


class BaseCRUD:
    @classmethod
    def _get_option_from_meta(cls, name: str) -> Any:
        try:
            meta = cls.Meta
        except AttributeError:
            raise MetaNotFound('You need add class Meta with options.')

        try:
            option = getattr(meta, name)
        except AttributeError:
            raise OptionNotFound(f'Option <{name}> not set in Meta class.')

        return option

    @classmethod
    def deserialize_data(cls, schema_name: str, data: dict) -> dict:
        schema = cls._get_option_from_meta(schema_name)
        return schema().load(data)

    @classmethod
    def _clean_data(cls, data: Any) -> Any:
        """Clearing hierarchical structures from empty values.

        Cleaning occurs for objects of the list and dict types, other types do not clean.

        :param data: an object for cleaning.
        :return: cleaned object.
        """

        empty_values = ('', None, [], {}, (), set())

        if isinstance(data, dict):
            cleaned_dict = {k: cls._clean_data(v) for k, v in data.items()}
            return {k: v for k, v in cleaned_dict.items() if v not in empty_values}

        elif isinstance(data, list):
            cleaned_list = [cls._clean_data(item) for item in data]
            return [item for item in cleaned_list if item not in empty_values]

        else:
            return data

    @classmethod
    def serialize_data(cls, schema_name: str, data: Result, fields: list = None) -> dict:
        output_schema = cls._get_option_from_meta(schema_name)

        if isinstance(data, list):
            serialized_data = output_schema(many=True, only=fields).dump(data)
        else:
            serialized_data = output_schema(only=fields).dump(data)

        return cls._clean_data(serialized_data)
