from collections.abc import Callable
from collections.abc import Iterable
from functools import wraps
from typing import Any

from marshmallow.schema import SchemaMeta


class Validation:
    @classmethod
    def input(
        cls, schema: SchemaMeta, deserialize: bool = True, keys: Iterable[str] or None = None
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, **data) -> Any or dict[Any, Any]:
                if deserialize:
                    deserialized_data = schema(only=keys).load(data)
                    return func(self, **deserialized_data)
                else:
                    schema(only=keys).validate(data)
                    return func(self, **data)

            return wrapper

        return decorator

    @classmethod
    def output(
        cls, schema: SchemaMeta, serialize: bool = False, keys: Iterable[str] or None = None
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs) -> Any or dict[Any, Any]:
                obj = func(self, *args, **kwargs)

                if serialize:
                    serialized_data = schema(only=keys).dump(obj)
                    return serialized_data
                else:
                    schema(only=keys).validate(obj)
                    return obj

            return wrapper

        return decorator
