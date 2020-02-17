from click import ClickException
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


class NexusClientBaseError(ClickException):
    exit_code = CliReturnCode.UNKNOWN_ERROR.value

    # TODO: add error message; e.g.:
    # nexus_error = CliReturnCode.UNKNOWN_ERROR
    # def __init__(self, message):
    #     super().__init__(self.nexus_error.message)


class NexusClientAPIError(NexusClientBaseError):
    """Unexpected response from Nexus service."""
    exit_code = CliReturnCode.API_ERROR.value


class NexusClientConnectionError(NexusClientBaseError):
    """Generic network connector error."""
    exit_code = CliReturnCode.CONNECTION_ERROR.value


class NexusClientInvalidCredentials(NexusClientBaseError):
    """
    Login credentials not accepted by Nexus service. Usually the result of a
    HTTP 401 response.
    """
    exit_code = CliReturnCode.INVALID_CREDENTIALS.value


class NexusClientInvalidRepositoryPath(NexusClientBaseError):
    """
    Used when an operation against the Nexus service uses an invalid or
    non-existent path.
    """
    pass


class NexusClientInvalidRepository(NexusClientBaseError):
    """The given repository does not exist in Nexus."""
    exit_code = CliReturnCode.REPOSITORY_NOT_FOUND.value


class NexusClientInvalidCleanupPolicy(NexusClientBaseError):
    """The given cleanup policy does not exist in Nexus."""
    exit_code = CliReturnCode.SUBCOMMAND_ERROR.value


class NexusClientCreateRepositoryError(NexusClientBaseError):
    """Used when a repository creation operation in Nexus fails."""
    exit_code = CliReturnCode.SUBCOMMAND_ERROR.value


class NexusClientCreateCleanupPolicyError(NexusClientBaseError):
    """Used when a cleanup policy creation operation in Nexus fails."""
    exit_code = CliReturnCode.SUBCOMMAND_ERROR.value


class DownloadError(NexusClientBaseError):
    """Error retrieving artefact from Nexus service."""
    exit_code = CliReturnCode.DOWNLOAD_ERROR.value
