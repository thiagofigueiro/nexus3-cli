class NexusClientAPIError(Exception):
    """Unexpected response from Nexus service."""
    pass


class NexusClientInvalidCredentials(Exception):
    """
    Login credentials not accepted by Nexus service. Usually the result of a
    HTTP 401 response.
    """
    pass


class NexusClientInvalidRepositoryPath(Exception):
    """
    Used when an operation against the Nexus service uses an invalid or
    non-existent path.
    """
    pass


class NexusClientInvalidRepository(Exception):
    """The given repository does not exist in Nexus."""
    pass


class NexusClientCreateRepositoryError(Exception):
    """Used when a repository creation operation in Nexus fails."""
    pass


class DownloadError(Exception):
    """Error retrieving artefact from Nexus service."""
    pass
