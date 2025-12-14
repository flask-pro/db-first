from abc import abstractmethod
from typing import Any

from . import BaseAction


class BaseWebAction(BaseAction):
    """The base class for all Actions that implement logic."""

    serialized_result: dict[str, Any]

    @abstractmethod
    def permit(self) -> None:
        """Permit called by `self.run()` to check access permissions.

        Will raise exception if permit fails.

        :raises: ActionPermitException
        """
        raise NotImplementedError('Implement method for checking permissions.')

    @abstractmethod
    def serialization(self) -> Any:
        """Serialization called by `self.run()` to serialize result.

        Will raise exception if serialization fails.

        :raises: ActionSerializationException
        """
        raise NotImplementedError('Implement method for serialization output data.')

    def run(self) -> Any:
        """Run executes the Action.

        Can raise functions exceptions.

        :raises: ActionRunException
        """
        self.permit()
        self.validate()
        self.result = self.action()
        self.serialized_result = self.serialization()
        return self.serialized_result
