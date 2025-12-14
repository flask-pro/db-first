from ..exc import DBFirstError


class DBALException(DBFirstError):
    """Main exception for DBAL."""


class DBALCreateException(DBALException):
    """Exception for create methods."""


class DBALObjectNotFoundException(DBALException):
    """Exception for read methods."""


class DBALUpdateException(DBALException):
    """Exception for update methods."""


class DBALPaginateException(DBALException):
    """Exception for paginate mixin."""
