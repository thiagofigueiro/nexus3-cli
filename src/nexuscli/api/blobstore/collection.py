import json

from nexuscli import exception, nexus_util


class BlobstoreCollection(object):
    """
    A class to manage Nexus 3 blobstores.

    Args:
        client(nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.

    Attributes:
        client(nexuscli.nexus_client.NexusClient): as per ``client``
            argument of :class:`ScriptCollection`.
    """

    GROOVY_SCRIPT_NAME = 'nexus3-cli-blobstore'
    """Groovy script used by this class"""

    def __init__(self, client=None):
        self._client = client
        script_content = nexus_util.groovy_script(self.GROOVY_SCRIPT_NAME)
        self._client.scripts.create_if_missing(
            self.GROOVY_SCRIPT_NAME, script_content)

    def raw_list(self):
        blobstore = {'_action': 'list'}
        script_args = json.dumps(blobstore)

        response = self._client.scripts.run(
            self.GROOVY_SCRIPT_NAME, data=script_args)

        return response.get('result')

    def create(self, name, path):
        blobstore = {
            '_action': 'create',
            'name': name,
            'path': path,
        }

        script_args = json.dumps(blobstore)
        try:
            self._client.scripts.run(self.GROOVY_SCRIPT_NAME, data=script_args)
        except exception.NexusClientAPIError as e:
            raise exception.NexusClientCreateBlobStoreError(
                f'{name}: {e}') from None

    def delete(self, name):
        blobstore = {
            '_action': 'delete',
            'name': name,
        }

        script_args = json.dumps(blobstore)
        try:
            self._client.scripts.run(self.GROOVY_SCRIPT_NAME, data=script_args)
        except exception.NexusClientAPIError:
            raise exception.NexusClientAPIError(name) from None
