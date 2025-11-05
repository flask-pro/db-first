from typing import Any

from .exc import MetaNotFound
from .exc import OptionNotFound


class BaseCRUD:
    @classmethod
    def _get_option_from_meta(cls, name: str, default: Any | None = ...) -> Any:
        try:
            meta = cls.Meta
        except AttributeError:
            raise MetaNotFound('You need add class Meta with options.')

        try:
            option = getattr(meta, name)
        except AttributeError:
            if default is Ellipsis:
                raise OptionNotFound(f'Option <{name}> not set in Meta class.')
            else:
                option = default

        return option
