import pytest

from nexuscli import repository


@pytest.fixture
def repository_collection(mocker):
    fixture = repository.RepositoryCollection(client=mocker.Mock())
    return fixture
