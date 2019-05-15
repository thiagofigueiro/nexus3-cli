import itertools
import json
import pytest

from nexuscli import exception, repository


def test_collection_delete(repository_collection, faker):
    """
    Ensure the delete method verifies the groovy script is in place and runs it
    with the name of the repository to be deleted as an argument
    """
    x_name = faker.word()

    repository_collection.delete(x_name)

    repository_collection.client.scripts.create_if_missing.assert_called_once()
    repository_collection.client.scripts.run.assert_called_with(
        'nexus3-cli-repository-delete', data=x_name)


def test_create_type_error(repository_collection, faker):
    with pytest.raises(TypeError):
        repository_collection.create(faker.pyiterable())


@pytest.mark.parametrize('repo_type', repository.validations.KNOWN_TYPES)
def test_create_repository_error(repo_type, repository_collection, mocker):
    mocker.patch('json.dumps')
    mocker.patch.object(
        repository.Repository, 'configuration',
        new_callable=mocker.PropertyMock)

    repo = repository.Repository(repo_type)

    with pytest.raises(exception.NexusClientCreateRepositoryError):
        repository_collection.create(repo)


@pytest.mark.parametrize('repo_type, response', itertools.product(
    repository.validations.KNOWN_TYPES,
    [{}, {'result': 'something'}, {'result': 'null'}]))
def test_create_repository(
        repo_type, response, repository_collection, faker, mocker):
    """
    Ensure the delete method verifies the groovy script is in place and runs it
    with the configuration for the repository to be created as argument. Also
    test that the result is correctly interpreted for success/failure.
    """
    x_configuration = faker.pydict()
    repository_collection.client.scripts.run.return_value = response

    mocker.patch('json.dumps')
    json.dumps.return_value = x_configuration

    mocker.patch.object(
        repository.Repository, 'configuration',
        new_callable=mocker.PropertyMock, return_value=x_configuration)

    repo = repository.Repository(repo_type)

    if response.get('result') == 'null':
        repository_collection.create(repo)
    else:
        with pytest.raises(exception.NexusClientCreateRepositoryError):
            repository_collection.create(repo)

    repository_collection.client.scripts.create_if_missing.assert_called_once()
    json.dumps.assert_called_with(repo.configuration)
    repository_collection.client.scripts.run.assert_called_with(
        'nexus3-cli-repository-create', data=json.dumps.return_value)


def test_refresh_repositories(nexus_mock_client):
    """
    Ensure the method retrieves latest repositories and sets the class
    attribute.
    """
    repositories = nexus_mock_client.repositories.raw_list()
    x_repositories = nexus_mock_client._request.return_value._json

    nexus_mock_client._request.assert_called_with(
        'get', 'repositories', stream=True)
    assert repositories == x_repositories


def test_refresh_repositories_error(nexus_mock_client):
    """
    Ensure the method does't modify the existing repositories attribute when
    the client request fails.
    """
    nexus_mock_client._request.return_value.status_code = 400
    nexus_mock_client.repositories._repositories_json = None

    with pytest.raises(exception.NexusClientAPIError):
        nexus_mock_client.repositories.refresh()

    assert nexus_mock_client.repositories._repositories_json is None


@pytest.mark.parametrize('x_found', [True, False])
def test_get_repository_by_name(
        x_found, nexus_mock_client, faker):
    """Ensure the method returns a repo found by name or raises an exception"""
    nexus = nexus_mock_client
    x_name = faker.pystr()
    x_format = faker.pystr()
    x_repo = None
    x_values = nexus_mock_client._request.return_value._json

    if x_found:
        x_repo = pytest.helpers.nexus_repository(x_name, x_format)
        x_values.append(x_repo)

    nexus.repositories.refresh()

    if x_found:
        assert nexus.repositories.get_raw_by_name(x_name) == x_repo
        assert nexus.repositories.get_raw_by_name(x_name)['name'] == x_name
        assert nexus.repositories.get_raw_by_name(x_name)['format'] == x_format
    else:
        with pytest.raises(IndexError):
            nexus.repositories.get_raw_by_name(x_name)
