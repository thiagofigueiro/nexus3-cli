from enum import Enum


class CliReturnCode(Enum):
    """Error codes returned by :py:mod:`nexuscli.cli`"""
    SUCCESS = 0
    NO_FILES = 1
    API_ERROR = 2
    CONNECTION_ERROR = 3
    DOWNLOAD_ERROR = 4
    INVALID_CREDENTIALS = 5
    INVALID_SUBCOMMAND = 10
    SUBCOMMAND_ERROR = 11
    POLICY_NOT_FOUND = 20
    REPOSITORY_NOT_FOUND = 30
    UNKNOWN_ERROR = 99
