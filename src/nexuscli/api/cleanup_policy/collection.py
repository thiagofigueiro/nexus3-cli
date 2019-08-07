import json

from nexuscli import exception, nexus_util
from nexuscli.api.cleanup_policy import CleanupPolicy


class CleanupPolicyCollection(object):
    """
    A class to manage Nexus 3 Cleanup Policies.

    Args:
        client(nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.
    """
    GROOVY_SCRIPT_NAME = 'nexus3-cli-cleanup-policy'
    """Groovy script used by this class"""

    def __init__(self, client=None):
        self._client = client
        script_content = nexus_util.groovy_script(self.GROOVY_SCRIPT_NAME)
        self._client.scripts.create_if_missing(
            self.GROOVY_SCRIPT_NAME, script_content)

    def create_or_update(self, cleanup_policy):
        """
        Creates the given Cleanup Policy in the Nexus repository. If a policy
        with the same name already exists, it will be updated.

        :param cleanup_policy: the policy to create or update.
        :type cleanup_policy: CleanupPolicy
        :raises exception.NexusClientCreateCleanupPolicyError: when the Nexus
            API returns an error or unexpected result.
        """
        if not isinstance(cleanup_policy, CleanupPolicy):
            raise TypeError(
                f'cleanup_policy ({type(cleanup_policy)}) must be a '
                f'CleanupPolicy')

        script_args = json.dumps(cleanup_policy.configuration)
        try:
            response = self._client.scripts.run(
                self.GROOVY_SCRIPT_NAME, data=script_args)
        except exception.NexusClientAPIError:
            raise exception.NexusClientCreateCleanupPolicyError(
                cleanup_policy.configuration['name'])

        result = json.loads(response['result'])
        if result['name'] != cleanup_policy.configuration['name']:
            raise exception.NexusClientCreateCleanupPolicyError(response)

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
        script_args = json.dumps({'name': name})

        try:
            response = self._client.scripts.run(
                self.GROOVY_SCRIPT_NAME, data=script_args)
        except exception.NexusClientAPIError:
            raise exception.NexusClientInvalidCleanupPolicy(name)

        cleanup_policy = json.loads(response['result'])

        return CleanupPolicy(self._client, **cleanup_policy)

    def list(self):
        """
        Return all cleanup policies.

        :return: every policy as a list of
            :class:`~nexuscli.api.cleanup_policy.model.CleanupPolicy`
            instances.
        :rtype: list[CleanupPolicy]
        """
        response = self._client.scripts.run(self.GROOVY_SCRIPT_NAME, data={})

        cleanup_policies = json.loads(response['result'])

        return [CleanupPolicy(self._client, **c) for c in cleanup_policies]
