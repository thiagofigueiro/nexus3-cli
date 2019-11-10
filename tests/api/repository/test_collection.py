import itertools
import pytest
from pprint import pformat

from nexuscli import exception
from nexuscli.api import repository


def test_create_type_error(repository_collection, faker):
    """Ensure the method raises TypeError when not given a Repository"""
    with pytest.raises(TypeError):
        repository_collection.create(faker.pyiterable())


def test_create_repository_error(repository_collection, mocker):
    """
    Ensure the incorrect response from Nexus results in the expected exception
    """
    mocker.patch('json.dumps')

    with pytest.raises(exception.NexusClientCreateRepositoryError):
        repository_collection.create(repository.Repository('dummy'))


@pytest.mark.parametrize('repo_class, response', itertools.product(
    repository.model.__all__,
    [{}, {'result': 'something'}, {'result': 'null'}]))
def test_create_repository(
        repo_class, response, nexus_mock_client, faker, mocker):
    """Ensure the method behaves as expected for all Repository classes"""
    x_configuration = faker.pydict()
    mocker.patch('nexuscli.nexus_client.ScriptCollection')
    nexus_mock_client.scripts.run.return_value = response

    json_dumps = mocker.patch('json.dumps', return_value=x_configuration)

    mocker.patch.object(
        repo_class, 'configuration',
        new_callable=mocker.PropertyMock, return_value=x_configuration)

    kwargs = {}
    if repo_class.TYPE == 'proxy':
        kwargs['remote_url'] = faker.url()

    repo = repo_class(faker.word(), **kwargs)

    if response.get('result') == 'null':
        nexus_mock_client.repositories.create(repo)
    else:
        with pytest.raises(exception.NexusClientCreateRepositoryError):
            nexus_mock_client.repositories.create(repo)

    nexus_mock_client.scripts.create_if_missing.assert_called_once()
    json_dumps.assert_called_with(repo.configuration)
    nexus_mock_client.scripts.run.assert_called_with(
        'nexus3-cli-repository-create', data=json_dumps.return_value)


def test_delete(nexus_mock_client, faker, mocker):
    """
    Ensure the delete method verifies the groovy script is in place and runs it
    with the configuration for the repository to be created as argument. Also
    test that the result is correctly interpreted for success/failure.
    """
    mocker.patch('nexuscli.nexus_client.ScriptCollection')
    x_name = faker.word()

    nexus_mock_client.repositories.delete(x_name)

    nexus_mock_client.scripts.create_if_missing.assert_called_once()
    nexus_mock_client.scripts.run.assert_called_with(
        'nexus3-cli-repository-delete', data=x_name)


# TODO: test all repos, not just the built-in maven ones
@pytest.mark.parametrize('x_configuration', pytest.helpers.default_repos())
@pytest.mark.integration
def test_get_raw_by_name(x_configuration, nexus_client):
    """Ensure the method finds and returns a repo configuration by name"""
    name = x_configuration['repositoryName']
    configuration = nexus_client.repositories.get_raw_by_name(name)

    added, removed, modified, _ = pytest.helpers.compare_dict(
        configuration, x_configuration)

    if added or removed or modified:
        print(
            f'added: {pformat(added)}\n'
            f'removed: {pformat(removed)}\n'
            f'modified: {pformat(modified)}\n')
        pytest.fail('Configuration mismatch')


@pytest.mark.integration
def test_get_raw_by_name_error(nexus_client, faker):
    """Ensure the method raises an exception when a repo is not found"""
    with pytest.raises(exception.NexusClientInvalidRepository):
        nexus_client.repositories.get_raw_by_name(faker.pystr())


def test_refresh(nexus_mock_client):
    """
    Ensure the method retrieves latest repositories and sets the class
    attribute.
    """
    repositories = nexus_mock_client.repositories.raw_list()
    x_repositories = nexus_mock_client.http_request.return_value._json

    nexus_mock_client.http_request.assert_called_with(
        'get', 'repositories', stream=True)
    assert repositories == x_repositories


def test_refresh_error(nexus_mock_client):
    """
    Ensure the method does't modify the existing repositories attribute when
    the client request fails.
    """
    nexus_mock_client.http_request.return_value.status_code = 400
    nexus_mock_client.repositories._repositories_json = None

    with pytest.raises(exception.NexusClientAPIError):
        nexus_mock_client.repositories.refresh()

    assert nexus_mock_client.repositories._repositories_json is None


@pytest.mark.integration
def test_raw_list(nexus_client):
    """Ensure the method returns a raw list of repositories"""
    repositories = nexus_client.repositories.raw_list()

    assert isinstance(repositories, list)
    assert all(r.get('name') for r in repositories)
    assert all(r.get('format') for r in repositories)
    assert all(r.get('type') for r in repositories)
    assert all(r.get('url') for r in repositories)
