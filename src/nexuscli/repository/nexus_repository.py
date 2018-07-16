from nexuscli.repository import validations


class RepositoryCollection(object):
    """
    A class representing a Nexus 3 repository.
    """
    def __init__(self, client=None):
        """
        :param client: client instance
        :type client:  nexuscli.nexus_client.NexusClient
        """
        self.client = client

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
        self.client.script_create_if_missing(script)
        self.client.script_run(script['name'], data=name)

    def create(self, repo_type, **kwargs):
        """
        Creates a Nexus repository with the given format and type.

        Args:
            name (str): name of the new repository.
            format (str): format (recipe) of the new repository. Must be one
                of :py:data:`KNOWN_FORMATS`.
            blob_store_name (str):
            depth (int): only valid when ``repo_format=yum``. The repodata
                depth.
            remote_url (str):
            strict_content_type_validation (bool):
            version_policy
            write_policy
            layout_policy

        :param repo_type: type for the new repository. Must be one of
            :py:data:`KNOWN_FORMATS`.
        :param kwargs: attributes for the new repository.
        :return: the created repository
        :rtype: Repository
        """
        validations.check_create_args(repo_type, **kwargs)
        # script = groovy.script_create_repository(repo_type, **kwargs)
        raise NotImplementedError


class Repository(object):
    pass
