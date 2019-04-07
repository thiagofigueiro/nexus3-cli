from enum import Enum


class CliReturnCode(Enum):
    SUCCESS = 0
    NO_FILES = 1
    API_ERROR = 2
    INVALID_SUBCOMMAND = 10
    POLICY_NOT_FOUND = 20
    UNKNOWN_ERROR = 99
