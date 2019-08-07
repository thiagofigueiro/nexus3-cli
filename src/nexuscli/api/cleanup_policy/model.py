from nexuscli.api.cleanup_policy import validations


class CleanupPolicy(object):
    """
    Represents a Nexus Cleanup Policy.

    Args:
        client (nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.
        name (str): name of the new policy.
        format (str): 'all' or the name of the repository format this policy
            applies to.
        mode (str): 'delete'
        criteria (dict): the deletion criteria for the policy. Supports one or
            more of the following attributes:
                - ``lastDownloaded`` (int): seconds since artefact last
                  downloaded;
                - ``lastBlobUpdated`` (int): seconds since last update to
                  artefact;
    """
    def __init__(self, client, **kwargs):
        self._client = client
        self._raw = kwargs

    @property
    def configuration(self):
        """
        Nexus 3 Cleanup Policy representation as a python dict. The dict
        returned by this property can
        be converted to JSON for use with the ``nexus3-cli-cleanup-policy``
        groovy script created by the
        :py:class:`~nexuscli.api.cleanup_policy.collection.CleanupPolicyCollection`
        methods.

        Example structure and attributes common to all repositories:

        >>> cleanup_policy = {
        >>>     'name': 'my-policy',
        >>>     'format': 'bower',
        >>>     'mode': 'delete',
        >>>     'criteria': {
        >>>         'lastDownloaded': 172800,
        >>>         'lastBlobUpdated': 86400
        >>>     }
        >>> }

        Depending on the repository type and format (recipe), other attributes
        will be present.

        :return: cleanup policy as a dict
        :rtype: dict
        """
        # TODO: validate format, mode
        validations.policy_criteria(self._raw)
        validations.policy_name(self._raw)
        return self._raw
