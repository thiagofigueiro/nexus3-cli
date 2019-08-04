import os
from clint.textui import progress

from nexuscli import exception
from nexuscli.api.repository import validations, util
from nexuscli.api.repository.validations import REMOTE_PATH_SEPARATOR


class LegacyRepository(object):
    """
    Do not use this. It will be removed before 2.0.0 final is out.

    Creates an object representing a Nexus repository with the given
    format, type and attributes.

    Args:
        name (str): name of the new repository.
        format (str): format (recipe) of the new repository. Must be one
            of :py:data:`nexuscli.repository.validations.KNOWN_FORMATS`.
        type (str): type of the new repository. Must be one of
            :py:data:`nexuscli.repository.validations.KNOWN_TYPES`.
        blob_store_name (str): an existing blob store; 'default' should work
            on most installations.
        depth (int): only accepted when ``repo_format='yum'``. The Yum repodata
            depth. Usually 1.
        remote_url (str): only accepted when ``repo_type='proxy'``. The URL of
            the repository being proxied, including the protocol scheme.
        strict_content_type_validation (bool): only accepted when
            ``repo_type='hosted'``. Whether to validate file extension against
            its content type.
        version_policy (str): only accepted when ``repo_type='hosted'``. Must
            be one of
            :py:data:`nexuscli.repository.validations.VERSION_POLICIES`.
        write_policy (str): only accepted when ``repo_type='hosted'``. Must
            be one of
            :py:data:`nexuscli.repository.validations.WRITE_POLICIES`.
        layout_policy (str): only accepted when ``format='maven'``. Must
            be one of
            :py:data:`nexuscli.repository.validations.LAYOUT_POLICIES`.
        ignore_extra_kwargs (bool): if True, do not raise an exception for
            unnecessary/extra/invalid kwargs.

    :param client: the client instance that
        will be used to perform operations against the Nexus 3 service. You
        must provide this at instantiation or set it before calling any methods
        that require connectivity to Nexus.
    :type client: nexuscli.nexus_client.NexusClient
    :param kwargs: attributes for the new repository.
    :return: a Repository instance with the given settings
    :rtype: LegacyRepository
    """
    SUPPORTED_FORMATS_FOR_UPLOAD = ['raw', 'yum']

    def __init__(self, client, **kwargs):
        self._client = client
        self._raw = validations.upcase_policy_args(kwargs)

    def __repr__(self):
        return 'Repository({self.type}, {self._raw})'.format(self=self)

    def _recipe_name(self):
        repo_format = self._raw['format']
        if repo_format == 'maven':
            repo_format = 'maven2'
        return f'{repo_format}-{self.type}'

    @property
    def format(self):
        return self._raw['format']

    @property
    def name(self):
        return self._raw['name']

    @property
    def type(self):
        return self._raw['type']

    @property
    def configuration(self):
        """
        Validate the configuration for the Repository and build its
        representation as a python dict. The dict returned by this property can
        be converted to JSON for use with the ``nexus3-cli-repository-create``
        groovy script created by the
        :py:meth:`nexuscli.repository.RepositoryCollection.create` method.

        Example structure and attributes common to all repositories:

        >>> common_configuration = {
        >>>     'name': 'my-repository',
        >>>     'online': True,
        >>>     'recipeName': 'raw',
        >>>     '_state': 'present',
        >>>     'attributes': {
        >>>         'storage': {
        >>>             'blobStoreName': 'default',
        >>>         },
        >>>         'cleanup': {
        >>>             'policyName': None,
        >>>         }
        >>>     }
        >>> }

        Depending on the repository type and format (recipe), other attributes
        will be present.

        :return: repository configuration
        :rtype: dict
        """
        validations.repository_args(self.type, **self._raw)
        if self.type == 'hosted':
            return self._configuration_hosted()
        elif self.type == 'proxy':
            return self._configuration_proxy()
        elif self.type == 'group':
            return self._configuration_group()

        raise RuntimeError(
            'Unexpected repository type: {}'.format(self.type))

    def _configuration_common(self):
        repo_config = {
            'name': self._raw['name'],
            'online': True,
            'recipeName': self._recipe_name(),
            '_state': 'present',
            'attributes': {
                'storage': {
                    'blobStoreName': self._raw['blob_store_name'],
                },
                'cleanup': {
                    'policyName': self._raw['cleanup_policy'],
                }
            }
        }

        return repo_config

    def _configuration_add_maven_attr(self, repo_config):
        if self._raw['format'] == 'maven':
            repo_config['attributes']['maven'] = {
                'versionPolicy': self._raw['version_policy'],
                'layoutPolicy': self._raw['layout_policy'],
            }

    def _configuration_hosted(self):
        repo_config = self._configuration_common()
        repo_config['attributes']['storage'].update({
            'writePolicy': self._raw['write_policy'],
            'strictContentTypeValidation': self._raw[
                'strict_content_type_validation'],

        })

        self._configuration_add_maven_attr(repo_config)

        return repo_config

    def _configuration_proxy(self):
        repo_config = self._configuration_common()
        repo_config['attributes'].update({
            'httpclient': {
                'blocked': False,
                'autoBlock': True,
            },
            'proxy': {
                'remoteUrl': self._raw['remote_url'],
                'contentMaxAge': 1440,
                'metadataMaxAge': 1440,
            },
            'negativeCache': {
              'enabled': True,
              'timeToLive': 1440,
            },
        })
        repo_config['attributes']['storage'].update({
            'strictContentTypeValidation': self._raw[
                'strict_content_type_validation'],
        })

        self._configuration_add_maven_attr(repo_config)

        return repo_config

    def _configuration_group(self):
        repo_config = self._configuration_common()
        repo_config['attributes']['group'] = {
            'memberNames': self._raw['member_names'],
        }

        # TODO: accept/validate member_names in kwargs
        raise NotImplementedError

    def upload_file(self, src_file, dst_dir, dst_file=None):
        """
        Uploads a singe file to this Nexus repository under the directory and
        file name specified. If the destination file name isn't given, the
        source file name is used.

        :param src_file: path to the local file to be uploaded.
        :param dst_dir: directory under dst_repo to place file in.
        :param dst_file: destination file name.
        """
        # TODO: support all repository formats
        if self.format not in self.SUPPORTED_FORMATS_FOR_UPLOAD:
            raise NotImplementedError(
                'Upload to {} repository not supported'.format(self.format))

        if dst_file is None:
            dst_file = os.path.basename(src_file)

        _upload = getattr(self, '_upload_file_' + self.format)
        _upload(src_file, dst_dir, dst_file)

    def _upload_file_raw(self, src_file, dst_dir, dst_file):
        """Process upload_file() for raw repositories"""
        if dst_dir is None or dst_dir.startswith(REMOTE_PATH_SEPARATOR):
            raise exception.NexusClientInvalidRepositoryPath(
                'Destination path does not contain a directory, which is '
                'required by raw repositories')

        params = {'repository': self.name}
        files = {'raw.asset1': open(src_file, 'rb').read()}
        data = {
            'raw.directory': dst_dir,
            'raw.asset1.filename': dst_file,
        }

        response = self._client.http_post(
            'components', files=files, data=data, params=params)
        if response.status_code != 204:
            raise exception.NexusClientAPIError(
                f'Uploading to {self.name}. Reason: {response.reason}')

    def _upload_file_yum(self, src_file, dst_dir, dst_file):
        """Process upload_file() for yum repositories"""
        dst_dir = dst_dir or REMOTE_PATH_SEPARATOR
        repository_path = REMOTE_PATH_SEPARATOR.join(
            ['repository', self.name, dst_dir, dst_file])

        with open(src_file, 'rb') as fh:
            response = self._client.http_put(
                repository_path, data=fh, service_url=self._client.config.url)

        if response.status_code != 200:
            raise exception.NexusClientAPIError(
                f'Uploading to {repository_path}. Reason: {response.reason}')

    def upload_directory(self, src_dir, dst_dir, recurse=True, flatten=False):
        """
        Uploads all files in a directory to the specified destination directory
        in this repository, honouring options flatten and recurse.

        :param src_dir: path to local directory to be uploaded
        :param dst_dir: destination directory in dst_repo
        :param recurse: when True, upload directory recursively.
        :type recurse: bool
        :param flatten: when True, the source directory tree isn't replicated
            on the destination.
        :return: number of files uploaded
        :rtype: int
        """
        file_set = util.get_files(src_dir, recurse)
        file_count = len(file_set)
        file_set = progress.bar(file_set, expected_size=file_count)

        for relative_filepath in file_set:
            file_path = os.path.join(src_dir, relative_filepath)
            sub_directory = util.get_upload_subdirectory(
                            dst_dir, file_path, flatten)
            self.upload_file(file_path, sub_directory)

        return file_count
