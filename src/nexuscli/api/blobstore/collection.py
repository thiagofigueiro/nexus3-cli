import json
import re

from nexuscli import exception, nexus_util
from nexuscli.api.blobstore import model

_camel2under_re = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def camel2under(camel_string):
    """Converts a camelcased string to underscores. Useful for turning a
    class name into a function name.

    >>> camel2under('BasicParseTest')
    'basic_parse_test'
    """
    return _camel2under_re.sub(r'_\1', camel_string).lower()


def _get_class(raw_blob):
    for class_ in model.__all__:
        if raw_blob.get(class_.TYPE):
            return class_
    raise NotImplementedError(f'Blobstore type for {raw_blob}')


def _get_args_kwargs(raw_blob, blob_type):
    args = (raw_blob['name'],)
    quota_limit = raw_blob.get('blobStoreQuotaConfig').get('quotaLimitBytes')
    quota_type = raw_blob.get('blobStoreQuotaConfig').get('quotaType')

    kwargs = {
        'blob_store_quota_limit': quota_limit,
        'blob_store_quota_type': quota_type,
    }

    # add values from raw_blob, rewriting keys from camelCase to snake_case
    kwargs.update({camel2under(k): v for k, v in raw_blob[blob_type].items()})

    return args, kwargs


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

    def get_raw(self, name):
        blobstore = {'_action': 'get', 'name': name}
        script_args = json.dumps(blobstore)

        try:
            response = self._client.scripts.run(
                self.GROOVY_SCRIPT_NAME, data=script_args)
        except exception.NexusClientAPIError as e:
            raise exception.NexusClientCreateBlobStoreError(
                f'{name}: {e}') from None

        return json.loads(response.get('result', '{}'))

    def get(self, name):
        raw_blob = self.get_raw(name)

        blobstore_class = _get_class(raw_blob)

        raw_blob['name'] = name
        args, kwargs = _get_args_kwargs(raw_blob, blobstore_class.TYPE)

        return blobstore_class(*args, nexus_client=self._client, **kwargs)

    def raw_list(self):
        blobstore = {'_action': 'list'}
        script_args = json.dumps(blobstore)

        response = self._client.scripts.run(
            self.GROOVY_SCRIPT_NAME, data=script_args)

        return json.loads(response)

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
        self._client.scripts.run(self.GROOVY_SCRIPT_NAME, data=script_args)
