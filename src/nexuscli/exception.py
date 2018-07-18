class NexusClientAPIError(Exception):
    pass


class NexusClientConfigurationNotFound(Exception):
    pass


class NexusClientInvalidCredentials(Exception):
    pass


class NexusClientInvalidRepositoryPath(Exception):
    pass


class NexusClientInvalidRepository(Exception):
    pass


class NexusClientDownloadError(Exception):
    pass


class NexusClientCreateRepositoryError(Exception):
    pass
