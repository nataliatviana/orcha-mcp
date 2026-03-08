"""Module for custom exceptions used in the Orcha package."""


class InvalidConfigFileError(Exception):
    """Exception raised when the configuration file is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
