"""Module for custom exceptions used in the Orcha package."""


class InvalidConfigFileError(Exception):
    """Exception raised when the configuration file is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        """Return the error message, kept consistent with ``str(self)``."""
        return str(self)


class ServerConnectionError(Exception):
    """Exception raised when a connection to an MCP server fails.

    Raised when the server subprocess cannot be started (e.g. command not
    found) or when a remote server is unreachable.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        """Return the error message, kept consistent with ``str(self)``."""
        return str(self)
