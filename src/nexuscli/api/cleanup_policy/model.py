class CleanupPolicy(object):
    """
    Represents a Nexus Cleanup Policy.

    Example structure and attributes common to all repositories:

        >>> kwargs = {
        >>>     'name': 'my-policy',
        >>>     'format': 'bower',
        >>>     'notes': 'Some comment',
        >>>     'criteria': {
        >>>         'lastDownloaded': 172800,
        >>>         'lastBlobUpdated': 86400,
        >>>         'regex': 'matchthis'
        >>>     }
        >>> }


    Args:
        client (nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.
        name (str): name of the new policy.
        format (str): 'all' or the format of the repository this policy
            applies to.
        lastDownloaded (int): deletion criterion: days since artefact last
            downloaded
        lastBlobUpdated (int): deletion criterion: days since last update to
            artefact
        regex (str): deletion criterion: only delete artefacts that match this
            regular expression
    """
    def __init__(self, client, **kwargs):
        self._client = client
        # TODO: validate kwargs
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

        :return: cleanup policy as a dict
        :rtype: dict
        """
        return self._raw
