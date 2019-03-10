import json

from nexuscli import exception
from . import groovy
from .model import Repository


class RepositoryCollection(object):
    """
    A class to manage Nexus 3 repositories.

    Args:
        client(nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.

    Attributes:
        client(nexuscli.nexus_client.NexusClient): as per ``client``
            argument of :class:`RepositoryCollection`.
    """
    def __init__(self, client=None):
        self._client = client
        self._repositories_json = None

    def get_by_name(self, name):
        """
        Get a Nexus 3 repository by its name.

        :param name: name of the repository wanted
        :type name: str
        :return: the requested object
        :rtype: Repository
        :raise exception.NexusClientInvalidRepository: when a repository with
            the given name isn't found.
        """
        try:
            raw_repo = self.get_raw_by_name(name)
        except IndexError:
            raise exception.NexusClientInvalidRepository(name)

        return Repository(self._client, **raw_repo)

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
        previous_api_version = self._client._api_version
        response = self._client._get('repositories')
        if response.status_code != 200:
            raise exception.NexusClientAPIError(response.content)

        self._repositories_json = response.json()
        self._client._api_version = previous_api_version

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
        self._client.scripts.create_if_missing(script)
        self._client.scripts.run(script['name'], data=name)

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
        self._client.scripts.create_if_missing(script)

        script_args = json.dumps(repository.configuration)
        resp = self._client.scripts.run(script['name'], data=script_args)

        result = resp.get('result')
        if result != 'null':
            raise exception.NexusClientCreateRepositoryError(resp)
