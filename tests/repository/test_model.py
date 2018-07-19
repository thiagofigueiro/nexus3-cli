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
