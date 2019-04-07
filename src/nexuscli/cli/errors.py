from enum import Enum


class CliReturnCode(Enum):
    SUCCESS = 0
    INVALID_SUBCOMMAND = 10
    POLICY_NOT_FOUND = 20
