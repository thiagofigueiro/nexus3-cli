import json

from nexuscli import exception, nexus_util
from .model import CleanupPolicy

SCRIPT_NAME = 'nexus3-cli-cleanup-policy'


class CleanupPolicyCollection(object):
    """
    A class to manage Nexus 3 Cleanup Policies.

    Args:
        client(nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.

    Attributes:
        client(nexuscli.nexus_client.NexusClient): as per ``client``
            argument of :class:`RepositoryCollection`.
    """
    def __init__(self, client=None):
        self._client = client

    def get_by_name(self, name):
        """
        Get a Nexus 3 cleanup policy by its name.

        :param name: name of the wanted policy
        :type name: str
        :return: the requested object
        :rtype: CleanupPolicy
        :raise exception.NexusClientInvalidRepository: when a repository with
            the given name isn't found.
        """
        content = nexus_util.groovy_script(SCRIPT_NAME)
        self._client.scripts.create_if_missing(SCRIPT_NAME, content)

        script_args = json.dumps({'name': name})

        try:
            response = self._client.scripts.run(SCRIPT_NAME, data=script_args)
        except exception.NexusClientAPIError:
            raise exception.NexusClientInvalidCleanupPolicy(name)

        cleanup_policy = json.loads(response['result'])

        return CleanupPolicy(self._client, **cleanup_policy)
