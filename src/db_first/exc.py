class BaseToolsError(Exception):
    """Common exception for errors."""


class MetaNotFound(BaseToolsError):
    """Exception if class Meta is not defined."""


class OptionNotFound(MetaNotFound):
    """Exception if option not set in Meta class."""
