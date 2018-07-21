import json

from nexuscli import exception
from nexuscli.repository import validations, groovy


class RepositoryCollection(object):
    """
    A class to manage Nexus 3 repositories.
    """
    def __init__(self, client=None):
        """
        :param client: client instance
        :type client:  nexuscli.nexus_client.NexusClient
        """
        self.client = client
        self._repositories_json = None

    def get_raw_by_name(self, name):
        """
        Return the raw dict for the repository called ``name``. Remember to
        :meth:`refresh` to get the latest from the server.

        Args:
            name (str): name of wanted repository

        Returns:
            dict: the repository, if found.

        Raises:
            :class:`IndexError`: if no repository named ``name`` is found.

        """
        for r in self._repositories_json:
            if r['name'] == name:
                return r

        raise IndexError

    def refresh(self):
        """
        Refresh local list of repositories with latest from service. A raw
        representation of repositories can be fetched using :meth:`raw_list`.
        """
        previous_api_version = self.client._api_version
        self.client._api_version = 'beta'
        response = self.client._get('repositories')
        if response.status_code != 200:
            raise exception.NexusClientAPIError(response.content)

        self._repositories_json = response.json()
        self.client._api_version = previous_api_version

    def raw_list(self):
        """
        A raw representation of the Nexus repositories.

        Returns:
            dict: for the format, see `List Repositories
            <https://help.sonatype.com/repomanager3/rest-and-integration-api/repositories-api#RepositoriesAPI-ListRepositories>`_.
        """
        self.refresh()
        return self._repositories_json

    def delete(self, name):
        """
        Delete a repository.

        :param name: name of the repository to be deleted.
        """
        script = {
            'type': 'groovy',
            'name': 'nexus3-cli-repository-delete',
            'content': """
            log.info("Deleting repository [${args}]")
            repository.repositoryManager.delete(args)
            """,
        }
        self.client.scripts.create_if_missing(script)
        self.client.scripts.run(script['name'], data=name)

    def create(self, repository):
        """
        Creates a Nexus repository with the given format and type.

        :param repository:
        :type repository: Repository
        :return: None
        """
        if not isinstance(repository, Repository):
            raise TypeError('repository ({}) must be a Repository'.format(
                type(repository)
            ))

        script = {
            'type': 'groovy',
            'name': 'nexus3-cli-repository-create',
            'content': groovy.script_create_repo(),
        }
        self.client.scripts.create_if_missing(script)

        script_args = json.dumps(repository.configuration)
        resp = self.client.scripts.run(script['name'], data=script_args)

        result = resp.get('result')
        if result != 'null':
            raise exception.NexusClientCreateRepositoryError(resp)


class Repository(object):
    """
    Creates an object representing a Nexus repository with the given
    format, type and attributes.

    Args:
        name (str): name of the new repository.
        format (str): format (recipe) of the new repository. Must be one
            of data:`nexuscli.repository.validations.KNOWN_FORMATS`.
        blob_store_name (str):
        depth (int): only valid when ``repo_format=yum``. The repodata
            depth.
        remote_url (str):
        strict_content_type_validation (bool):
        version_policy (str):
        write_policy (str): One of :py:data:
        layout_policy (str): One of
        ignore_extra_kwargs (bool): if True, raise an exception for
            unnecessary/extra/invalid kwargs.

    :param repo_type: type for the new repository. Must be one of
        :py:data:`nexuscli.repository.validations.KNOWN_TYPES`.
    :param kwargs: attributes for the new repository.
    :return: the created repository
    :rtype: Repository
    """
    def __init__(self, repo_type, **kwargs):
        self._repo_type = repo_type
        self._raw = validations.upcase_policy_args(kwargs)

    def __repr__(self):
        return 'Repository({self._repo_type}, {self._raw})'.format(self=self)

    def _recipe_name(self):
        repo_format = self._raw['format']
        if repo_format == 'maven':
            repo_format = 'maven2'
        return '{repo_format}-{self._repo_type}'.format(**locals())

    @property
    def configuration(self):
        validations.repository_args(self._repo_type, **self._raw)
        if self._repo_type == 'hosted':
            return self._configuration_hosted()
        elif self._repo_type == 'proxy':
            return self._configuration_proxy()
        elif self._repo_type == 'group':
            return self._configuration_group()

        raise RuntimeError(
            'Unexpected repository type: {}'.format(self._repo_type))

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
