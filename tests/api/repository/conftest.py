import pytest

from nexuscli.api import repository


@pytest.fixture
def repository_collection(mocker):
    """A RepositoryCollection with the nexus_client mocked"""
    fixture = repository.RepositoryCollection(client=mocker.Mock())
    return fixture


@pytest.helpers.register
def repositories_by_type(repo_types):
    """Yield all repositories with the ``repo_type`` TYPE."""
    if isinstance(repo_types, str):
        repo_types = [repo_types]

    for repo_class in repository.model.__all__:
        if repo_class.TYPE in repo_types:
            yield repo_class
