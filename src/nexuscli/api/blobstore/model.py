from nexuscli import exception
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
    :param blob_store_quota_type: type of for this blob store. Must be one
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

    def __repr__(self):
        return f'{self.__class__.__name__}-{self.name}-{self.TYPE}'

    def __validate_params(self):
        if self.blob_store_quota_type is not None:
            validations.ensure_known(
                'blob_store_quota_type',
                self.blob_store_quota_type, self.QUOTA_TYPES)

    @property
    def _quota_config(self):
        config = {}
        if self.blob_store_quota_type is not None:
            config['quotaType'] = self.blob_store_quota_type
            config['quotaLimitBytes'] = self.blob_store_quota_limit
        return config

    @property
    def configuration(self):
        """
        Blobstore configuration represented as a python dict.

        :return: blobstore configuration
        :rtype: dict
        """
        config = {
            'name': self.name,
            'blobStoreQuotaConfig': self._quota_config,
        }

        return config

    @property
    def quota_status(self):
        """
        Status of the quota for the blobstore.

        Example:
        >>> self.quota_status
        >>> {
        >>>   "isViolation": false,
        >>>   "message": "Blob store s3test is limited to having 111.00 MB available space, and has 9.22 EB space remaining",
        >>>   "blobStoreName": "s3test"
        >>> }

        :return: the raw result from the quota-status API call, which is
            described as a ``BlobStoreQuotaResultXO`` in the Nexus 3 REST API.
        """
        response = self.nexus_client.http_get(
            f'blobstores/{self.name}/quota-status')
        if response.status_code != 200:
            raise exception.NexusClientAPIError(response.content)

        return response.json()


class FileBlobstore(Blobstore):
    """
    Represents a Blobstore of the ``file`` type.

    :param name: blobStore id
    :type name: str
    :param path: path where the blobstore resides on the local nexus server
        file system
    :type path: str
    :param kwargs: see :class:`Blobstore`
    """
    TYPE = 'file'

    def __init__(self, name, path=None, **kwargs):
        self.path = path
        super().__init__(name, **kwargs)

    @property
    def configuration(self):
        """
        As per :py:obj:`Blobstore.configuration` but specific to this
        blobstore type.

        :rtype: str
        """
        config = super().configuration
        config.update({
            'file': {
                'path': self.path,
            },
        })

        return config


class S3Blobstore(Blobstore):
    """
    Represents a Blobstore of the ``s3`` type.

    :param name: blobStore id
    :type name: str
    :param region: The AWS Region to use
    :type region: str
    :param bucket: S3 Bucket Name (must be between 3 and 63 characters long
        containing only lower-case characters, numbers, periods, and dashes)
    :type bucket: str
    :param prefix: S3 Path prefix
    :type prefix: str
    :param expiration: How many days until deleted blobs are finally removed
        from the S3 bucket (-1 to disable)
    :type expiration: int
    :param access_key_id: AWS Access Key ID with rw permissions to ``bucket``.
    :type access_key_id: str
    :param secret_access_key: Secret Access Key for ``access_key_id``
    :type secret_access_key: str
    :param assume_role: Assume Role ARN (Optional)
    :type assume_role: str
    :param session_token: Session Token ARN (Optional)
    :type session_token: str
    :param kwargs: see :class:`Blobstore`
    """
    TYPE = 's3'

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
        self.region = region
        self.bucket = bucket
        self.prefix = prefix
        self.expiration = expiration
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.assume_role = assume_role
        self.session_token = session_token

        super().__init__(name, **kwargs)

    @property
    def configuration(self):
        config = super().configuration
        config.update({
            's3': {
                'region': self.region,
                'bucket': self.bucket,
                'prefix': self.prefix,
                'expiration': self.expiration,
                'accessKeyId': self.access_key_id,
                'secretAccessKey': self.secret_access_key,
                'assumeRole': self.assume_role,
                'sessionToken': self.session_token
            },
        })

        return config


__all__ = [FileBlobstore, S3Blobstore]
