from marshmallow import post_dump
from marshmallow import Schema


class BaseSchema(Schema):
    __empty_values__ = ('', None, ..., [], {}, (), set())
    __skipped_keys__ = ()

    @post_dump()
    def _delete_keys_with_empty_value(self, data, many=False) -> dict or list:
        """Clearing hierarchical structures from empty values.

        Cleaning occurs for objects of the list and dict types, other types do not clean.

        :param data: an object for cleaning.
        :param many: Should be set to `True` if ``obj`` is a collection so that the object will
         be serialized to a list.
        :return: cleaned object.
        """

        if isinstance(data, dict):
            pre_cleaned_dict = {
                k: self._delete_keys_with_empty_value(v, many=many) for k, v in data.items()
            }

            cleaned_dict = {}
            for k, v in pre_cleaned_dict.items():
                if k not in self.__skipped_keys__ and v in self.__empty_values__:
                    continue
                else:
                    cleaned_dict[k] = v

            return cleaned_dict

        elif isinstance(data, list):
            pre_cleaned_list = [
                self._delete_keys_with_empty_value(item, many=many) for item in data
            ]
            return [item for item in pre_cleaned_list if item not in self.__empty_values__]

        else:
            return data
