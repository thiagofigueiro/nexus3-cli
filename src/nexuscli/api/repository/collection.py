import json

from nexuscli import exception, nexus_util
from nexuscli.api.repository.model import LegacyRepository

SCRIPT_NAME_CREATE = 'nexus3-cli-repository-create'
SCRIPT_NAME_DELETE = 'nexus3-cli-repository-delete'


class RepositoryCollection(object):
    """
    A class to manage Nexus 3 repositories.

    Args:
        client(nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.
    """
    def __init__(self, client=None):
        self._client = client
        self._repositories_json = None

    def get_by_name(self, name):
        """
        Get a Nexus 3 repository by its name.

        :param name: name of the repository wanted
        :type name: str
        :rtype: LegacyRepository
        :raise exception.NexusClientInvalidRepository: when a repository with
            the given name isn't found.
        """
        try:
            raw_repo = self.get_raw_by_name(name)
        except IndexError:
            raise exception.NexusClientInvalidRepository(name)

        return LegacyRepository(self._client, **raw_repo)

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
        response = self._client.http_get('repositories')
        if response.status_code != 200:
            raise exception.NexusClientAPIError(response.content)

        self._repositories_json = response.json()

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
        :type name: str
        """
        content = nexus_util.groovy_script(SCRIPT_NAME_DELETE)
        self._client.scripts.create_if_missing(SCRIPT_NAME_DELETE, content)
        self._client.scripts.run(SCRIPT_NAME_DELETE, data=name)

    def create(self, repository):
        """
        Creates a Nexus repository with the given format and type.

        :param repository: the instance containing the settings for the
            repository to be created.
        :type repository: LegacyRepository
        :raises NexusClientCreateRepositoryError: error creating repository.
        """
        if not isinstance(repository, LegacyRepository):
            raise TypeError('repository ({}) must be a Repository'.format(
                type(repository)
            ))
        content = nexus_util.groovy_script(SCRIPT_NAME_CREATE)
        self._client.scripts.create_if_missing(SCRIPT_NAME_CREATE, content)

        script_args = json.dumps(repository.configuration)
        resp = self._client.scripts.run(SCRIPT_NAME_CREATE, data=script_args)

        result = resp.get('result')
        if result != 'null':
            raise exception.NexusClientCreateRepositoryError(resp)
