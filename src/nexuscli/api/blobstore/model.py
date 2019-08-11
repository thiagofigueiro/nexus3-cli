from nexuscli.api import validations

DEFAULT_TYPE = 'file'


class Blobstore:
    """
    Base Nexus3 Blob Store

    :param name: blobStore id
    :type name: str
    :param nexus_client: the :class:`~nexuscli.nexus_client.NexusClient`
        instance that will be used to perform operations against the Nexus 3
        service. You must provide this at instantiation or set it before
        calling any methods that require connectivity to Nexus.
    :type nexus_client: nexuscli.nexus_client.NexusClient
    :param blob_store_quota_limit: quota limit, in bytes, for this blob store
    :type blob_store_quota_limit: int
    :param blob_store_quota_type: quota type for this blob store. Must be one
        of :py:attr:`QUOTA_TYPES`. See Nexus documentation for details.
    :type blob_store_quota_type: str
    """
    TYPE = None
    QUOTA_TYPES = ['spaceUsedQuota', 'spaceRemainingQuota']

    def __init__(self, name,
                 nexus_client=None,
                 blob_store_quota_limit=None,
                 blob_store_quota_type=None,
                 ):
        self.name = name
        self.nexus_client = nexus_client
        self.blob_store_quota_limit = blob_store_quota_limit
        self.blob_store_quota_type = blob_store_quota_type

        self.__validate_params()

    def __validate_params(self):
        validations.ensure_known(
            'blob_store_quota_type',
            self.blob_store_quota_type, self.QUOTA_TYPES)

    def quota_status(self):
        # BlobStoreQuotaResultXO
        # {
        #   "isViolation": false,
        #   "message": "Blob store thiagonexustest is limited to having 111.00 MB available space, and has 9.22 EB space remaining",
        #   "blobStoreName": "thiagonexustest"
        # }
        pass


class FileBlobstore(Blobstore):
# 'result': '{\n
# "file": {\n
# "path": "/tmp/test/1"\n    },\n
# "blobStoreQuotaConfig": {\n        \n    }\n}'}
    TYPE = 'file'

    def __init__(self, name,
                 region=None,
                 bucket=None,
                 prefix='',
                 expiration=3,
                 access_key_id=None,
                 secret_access_key=None,
                 assume_role='',
                 session_token='',
                 **kwargs):
        super().__init__(name, **kwargs)


class S3Blobstore(Blobstore):
# {'name': 'nexus3-cli-blobstore',
#  'result': '{\n    "s3": {
#  \n        "region": "us-east-1",
#  \n        "bucket": "thiagonexustest",
#  \n        "prefix": "test_path_prefix",
#  \n        "expiration": "3",
#  \n        "accessKeyId": "AKIASLMFS2HWLQOLE6SI",
#  \n        "secretAccessKey": "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",
#  \n        "assumeRole": "",
#  \n        "sessionToken": ""
#  \n    },\n
    TYPE = 's3'

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
