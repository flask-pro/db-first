from abc import ABC
from abc import abstractmethod
from typing import Any

from sqlalchemy.orm import Session


class BaseAction(ABC):
    """The base class for all Actions that implement logic."""

    _session: Session
    _data: dict[str, Any]
    result: dict[str, Any]

    def __init__(self, session: Session, data: dict[str, Any]):
        """Init method for Action.

        self._session - database session object.
        self._data - input data for action.
        self.result - result of data processing and performed actions.
        """
        self._session = session
        self._data = data

    @abstractmethod
    def validate(self) -> None:
        """Validate called by `self.run()` to validate data.

        Will raise exception if validation fails.

        :raises: ActionValidationException
        """
        raise NotImplementedError('Implement method for validate input data.')

    @abstractmethod
    def action(self) -> Any:
        """Action called by `self.run()` to execute logic.

        Will raise exception if action fails.

        :raises: ActionException
        """
        raise NotImplementedError('Implement logic here.')

    def run(self) -> Any:
        """Run executes the Action.

        Can raise functions exceptions.

        :raises: ActionRunException
        """
        self.validate()
        self.result = self.action()
        return self.result
