# -*- coding: utf-8 -*-
import pytest

from nexuscli import exception


@pytest.mark.parametrize(
    'component_path, x_repo, x_dir, x_file', [
        ('some/path/', 'some', 'path', None),
        ('some/other/path/', 'some', 'other/path', None),
        ('some/path/file', 'some', 'path', 'file'),
        ('some/other/path/file', 'some', 'other/path', 'file'),
        ('some/path/file.ext', 'some', 'path', 'file.ext'),
        ('repo', 'repo', None, None),
        ('repo/', 'repo', None, None),
        ('repo/.', 'repo', None, None),
        ('repo/./', 'repo', None, None),
        ('repo/./file', 'repo', None, 'file'),
        ('repo/file', 'repo', None, 'file'),
    ]
)
def test_split_component_path(
        component_path, x_repo, x_dir, x_file, nexus_mock_client):
    repository, directory, filename = nexus_mock_client.split_component_path(
        component_path)

    assert repository == x_repo
    assert directory == x_dir
    assert filename == x_file


@pytest.mark.parametrize(
    'component_path, x_error', [
        ('', 'does not contain a repository'),
        ('.', 'does not contain a repository'),
        ('./', 'does not contain a repository'),
    ]
)
def test_split_component_path_errors(
        component_path, x_error, nexus_mock_client):
    with pytest.raises(exception.NexusClientInvalidRepositoryPath) as e:
        nexus_mock_client.split_component_path(component_path)

    assert x_error in str(e.value)


def test_refresh_repositories(nexus_mock_client):
    """
    Ensure the method retrieves latest repositories and sets the class
    attribute.
    """
    repositories = nexus_mock_client.repo_list()
    x_repositories = nexus_mock_client._request.return_value._json

    nexus_mock_client._request.assert_called_with('get', 'repositories')
    assert repositories == x_repositories


def test_refresh_repositories_error(nexus_mock_client):
    """
    Ensure the method does't modify the existing repositories attribute when
    the client request fails.
    """
    nexus_mock_client._request.return_value.status_code = 400
    nexus_mock_client._repositories_json = None

    with pytest.raises(exception.NexusClientAPIError):
        nexus_mock_client.refresh_repositories()

    assert nexus_mock_client._repositories_json is None


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

    nexus.refresh_repositories()

    if x_found:
        assert nexus.get_repository_by_name(x_name) == x_repo
        assert nexus.get_repository_by_name(x_name)['name'] == x_name
        assert nexus.get_repository_by_name(x_name)['format'] == x_format
    else:
        with pytest.raises(IndexError):
            nexus.get_repository_by_name(x_name)
