import os
from clint.textui import progress
from urllib.parse import urlparse

from nexuscli.api.repository import validations, util, upload

DEFAULT_RECIPE = 'raw'
DEFAULT_WRITE_POLICY = 'ALLOW'
DEFAULT_BLOB_STORE_NAME = 'default'
DEFAULT_STRICT_CONTENT = False


class Repository:
    """
    A base Nexus repository.

    Nexus 3 repository recipes (formats) supported by this class:

        - `bower
          <https://help.sonatype.com/repomanager3/formats/bower-repositories>`_
        - `npm
          <https://help.sonatype.com/repomanager3/formats/npm-registry>`_
        - `nuget
          <https://help.sonatype.com/repomanager3/formats/nuget-repositories>`_
        - `pypi
          <https://help.sonatype.com/repomanager3/formats/pypi-repositories>`_
        - `raw
          <https://help.sonatype.com/repomanager3/formats/raw-repositories>`_
        - `rubygems
          <https://help.sonatype.com/repomanager3/formats/rubygems-repositories>`_

    :param name: name of the repository.
    :type name: str
    :param nexus_client: the :class:`~nexuscli.nexus_client.NexusClient`
        instance that will be used to perform operations against the Nexus 3
        service. You must provide this at instantiation or set it before
        calling any methods that require connectivity to Nexus.
    :type nexus_client: nexuscli.nexus_client.NexusClient
    :param recipe: format (recipe) of the new repository. Must be one of
        :py:attr:`RECIPES`. See Nexus documentation for details.
    :type recipe: str
    :param blob_store_name: name of an existing blob store; 'default'
        should work on most installations.
    :type blob_store_name: str
    :param strict_content_type_validation: Whether to validate file
        extension against its content type.
    :type strict_content_type_validation: bool
    :param cleanup_policy: name of an existing repository clean-up policy.
    :type cleanup_policy: str
    """

    RECIPES = ('bower', 'npm', 'nuget', 'pypi', 'raw', 'rubygems')
    TYPE = None

    def __init__(self, name,
                 nexus_client=None,
                 recipe=DEFAULT_RECIPE,
                 blob_store_name=DEFAULT_BLOB_STORE_NAME,
                 strict_content_type_validation=DEFAULT_STRICT_CONTENT,
                 cleanup_policy=None
                 ):
        self.name = name
        self.nexus_client = nexus_client
        self.recipe = recipe
        self.blob_store_name = blob_store_name
        self.strict_content = strict_content_type_validation
        self.cleanup_policy = cleanup_policy

        self.__validate_params()

    def __repr__(self):
        return f'{self.__class__.__name__}-{self.name}-{self.recipe}'

    def __validate_params(self):
        validations.ensure_known('recipe', self.recipe, self.RECIPES)

    @property
    def recipe_name(self):
        """
        The Nexus 3 name for this repository's recipe (format). This is almost
        always the same as :attr:`name` with ``maven`` being the notable
        exception.
        """
        if self.recipe == 'maven':
            return 'maven2'

        return self.recipe

    @property
    def configuration(self):
        """
        Repository configuration represented as a python dict. The dict
        returned by this property can be converted to JSON for use with the
        ``nexus3-cli-repository-create``
        groovy script created by the
        :py:meth:`~nexuscli.api.repository.collection.RepositoryCollection.create`
        method.

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
        repo_config = {
            'name': self.name,
            'online': True,
            'recipeName': f'{self.recipe_name}-{self.TYPE}',
            '_state': 'present',
            'attributes': {
                'storage': {
                    'blobStoreName': self.blob_store_name,
                    'strictContentTypeValidation': self.strict_content,
                },
            }
        }

        if self.cleanup_policy is not None:
            repo_config['attributes']['cleanup'] = {
                'policyName': self.cleanup_policy}

        return repo_config


class ProxyRepository(Repository):
    """
    A proxy Nexus repository.

    :param name: name of the repository.
    :type name: str
    :param remote_url: The URL of the repository being proxied, including the
        protocol scheme.
    :type remote_url: str
    :param auto_block: Auto-block outbound connections on the repository if
        remote peer is detected as unreachable/unresponsive.
    :type auto_block: bool
    :param content_max_age: How long (in minutes) to cache artifacts before
        rechecking the remote repository. Release repositories should use -1.
    :type content_max_age: int
    :param metadata_max_age: How long (in minutes) to cache metadata before
        rechecking the remote repository.
    :type metadata_max_age: int
    :param negative_cache_enabled: Cache responses for content not present in
        the proxied repository
    :type negative_cache_enabled: bool
    :param negative_cache_ttl: How long to cache the fact that a file was not
        found in the repository (in minutes)
    :type negative_cache_ttl: int
    :param kwargs: see :class:`Repository`
    """

    TYPE = 'proxy'

    def __init__(self, name,
                 remote_url=None,
                 auto_block=True,
                 content_max_age=1440,
                 metadata_max_age=1440,
                 negative_cache_enabled=True,
                 negative_cache_ttl=1440,
                 **kwargs):
        self.remote_url = remote_url
        self.auto_block = auto_block
        self.content_max_age = content_max_age
        self.metadata_max_age = metadata_max_age
        self.negative_cache_enabled = negative_cache_enabled
        self.negative_cache_ttl = negative_cache_ttl

        super().__init__(name, **kwargs)

        self.__validate_params()

    def __validate_params(self):
        if not isinstance(self.remote_url, str):
            raise ValueError('remote_url must be a str')

        parsed_url = urlparse(self.remote_url)
        if not (parsed_url.scheme and parsed_url.netloc):
            raise ValueError(
                f'remote_url={self.remote_url} is not a valid URL')

    @property
    def configuration(self):
        """
        As per :py:obj:`Repository.configuration` but specific to this
        repository recipe and type.

        :rtype: str
        """
        repo_config = super().configuration

        repo_config['attributes'].update({
            'httpclient': {
                'blocked': False,
                'autoBlock': self.auto_block,
            },
            'proxy': {
                'remoteUrl': self.remote_url,
                'contentMaxAge': self.content_max_age,
                'metadataMaxAge': self.metadata_max_age,
            },
            'negativeCache': {
                'enabled': self.negative_cache_enabled,
                'timeToLive': self.negative_cache_ttl,
            },
        })

        return repo_config


class HostedRepository(Repository):
    """
    A hosted Nexus repository.

    :param name: name of the repository.
    :type name: str
    :param write_policy: one of :py:attr:`WRITE_POLICIES`. See Nexus
        documentation for details.
    :type write_policy: str
    :param kwargs: see :class:`Repository`
    """
    WRITE_POLICIES = ['ALLOW', 'ALLOW_ONCE', 'DENY']
    """Nexus 3 repository write policies supported by this class."""

    TYPE = 'hosted'

    def __init__(self, name, write_policy=DEFAULT_WRITE_POLICY, **kwargs):
        self.write_policy = write_policy

        super().__init__(name, **kwargs)

        self.__validate_params()

    def __validate_params(self):
        validations.ensure_known(
            'write_policy', self.write_policy, self.WRITE_POLICIES)

    @property
    def configuration(self):
        """
        As per :py:obj:`Repository.configuration` but specific to this
        repository recipe and type.

        :rtype: str
        """
        repo_config = super().configuration

        repo_config['attributes']['storage'].update({
            'writePolicy': self.write_policy,
            'strictContentTypeValidation': self.strict_content,
        })

        return repo_config

    def upload_file(self, src_file, dst_dir, dst_file=None):
        """
        Uploads a singe file to the directory and file name specified.

        :param src_file: path to the local file to be uploaded.
        :param dst_dir: directory under dst_repo to place file in.
        :param dst_file: destination file name. If not given, the basename of
            ``src_file`` name is used.
        """
        if dst_file is None:
            dst_file = os.path.basename(src_file)

        upload_method_name = f'upload_file_{self.recipe_name}'
        try:
            # Find upload method in the upload module using naming convention
            upload_method = getattr(upload, upload_method_name)
        except AttributeError:
            raise NotImplementedError(upload_method_name) from None

        upload_method(self, src_file, dst_dir, dst_file)

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


class MavenRepository(Repository):
    """
    A base `Maven
    <https://help.sonatype.com/repomanager3/formats/maven-repositories#MavenRepositories-MavenRepositoryFormat>`_
    Nexus repository.

    :param name: name of the repository.
    :type name: str
    :param layout_policy: one of :py:attr:`LAYOUT_POLICIES`. See Nexus
        documentation for details.
    :param version_policy: one of :py:attr:`VERSION_POLICIES`. See Nexus
        documentation for details.
    :param kwargs: see :class:`Repository`
    """
    RECIPES = ('maven',)

    LAYOUT_POLICIES = ('PERMISSIVE', 'STRICT')
    """Maven layout policies"""

    VERSION_POLICIES = ('RELEASE', 'SNAPSHOT', 'MIXED')
    """Maven version policies"""

    def __init__(self, name,
                 layout_policy='PERMISSIVE',
                 version_policy='RELEASE',
                 **kwargs):
        self.layout_policy = layout_policy
        self.version_policy = version_policy

        kwargs.update({'recipe': 'maven'})

        super().__init__(name, **kwargs)

        self.__validate_params()

    def __validate_params(self):
        validations.ensure_known(
            'layout_policy', self.layout_policy, self.LAYOUT_POLICIES)
        validations.ensure_known(
            'version_policy', self.version_policy, self.VERSION_POLICIES)

    @property
    def configuration(self):
        """
        As per :py:obj:`Repository.configuration` but specific to this
        repository recipe and type.

        :rtype: str
        """
        repo_config = super().configuration

        repo_config['attributes']['maven'] = {
            'layoutPolicy': self.layout_policy,
            'versionPolicy': self.version_policy,
        }

        return repo_config


class MavenHostedRepository(HostedRepository, MavenRepository):
    """
    A `Maven
    <https://help.sonatype.com/repomanager3/formats/maven-repositories#MavenRepositories-MavenRepositoryFormat>`_
    hosted Nexus repository.

    See :class:`HostedRepository` and :class:`MavenRepository`
    """
    pass


class MavenProxyRepository(MavenRepository, ProxyRepository):
    """
    A `Maven
    <https://help.sonatype.com/repomanager3/formats/maven-repositories#MavenRepositories-MavenRepositoryFormat>`_
    proxy Nexus repository.

    See :class:`MavenRepository` and :class:`ProxyRepository`
    """
    pass


class YumRepository(Repository):
    """
    A `Yum <https://help.sonatype.com/repomanager3/formats/yum-repositories>`_
    base Nexus repository.

    :param name: name of the repository.
    :type name: str
    :param depth: The Yum ``repodata`` depth. Usually 1.
    :type depth: int
    :param kwargs: see :class:`Repository`
    """
    RECIPES = ('yum',)

    def __init__(self, name, depth=1, **kwargs):
        self.depth = depth

        kwargs.update({'recipe': 'yum'})

        super().__init__(name, **kwargs)

    @property
    def configuration(self):
        """
        As per :py:obj:`Repository.configuration` but specific to this
        repository recipe and type.

        :rtype: str
        """
        repo_config = super().configuration
        repo_config['attributes']['yum'] = {
            'repodataDepth': self.depth
        }
        return repo_config


class YumHostedRepository(HostedRepository, YumRepository):
    """
    A `Yum <https://help.sonatype.com/repomanager3/formats/yum-repositories>`_
    hosted Nexus repository.

    See :class:`HostedRepository` and :class:`YumRepository`
    """
    pass


class YumProxyRepository(ProxyRepository, YumRepository):
    """
    A `Yum <https://help.sonatype.com/repomanager3/formats/yum-repositories>`_
    proxy Nexus repository.

    See :class:`ProxyRepository` and :class:`YumRepository`
    """
    pass


__all__ = [
    Repository, HostedRepository, ProxyRepository,
    MavenHostedRepository, MavenProxyRepository,
    YumHostedRepository, YumProxyRepository,
]
