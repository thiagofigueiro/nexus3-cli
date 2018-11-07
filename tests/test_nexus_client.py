# -*- coding: utf-8 -*-
import pytest

import nexuscli
from nexuscli import exception, nexus_client


def test_login_config(mocker):
    """
    Ensure that the class tries to read the configuration and fetch
    repositories on instantiation
    """
    mocker.patch('nexuscli.nexus_client.RepositoryCollection')
    mocker.patch.object(nexus_client.NexusClient, 'read_config')

    client = nexus_client.NexusClient()

    nexuscli.nexus_client.RepositoryCollection.assert_called()
    client.repositories.refresh.assert_called_once()
    client.read_config.assert_called_once()


def test_login_params(faker, mocker):
    """
    Ensure that the class doesn't try to read the configuration and, instead,
    uses the provided connection parameters on instantiation.
    """
    mocker.patch('nexuscli.nexus_client.RepositoryCollection')
    mocker.patch.object(nexus_client.NexusClient, 'set_config')
    mocker.patch.object(nexus_client.NexusClient, 'read_config')

    x_user = faker.user_name()
    x_pass = faker.password()
    x_url = faker.url()
    x_verify = faker.pybool()

    client = nexus_client.NexusClient(
        user=x_user, password=x_pass, url=x_url, verify=x_verify)

    nexuscli.nexus_client.RepositoryCollection.assert_called()
    client.repositories.refresh.assert_called_once()
    client.read_config.assert_not_called()
    client.set_config.assert_called_with(x_user, x_pass, x_url, x_verify)


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


def test_write_config(client_args, mocker):
    """Ensure values written in config file can be read back"""
    mocker.patch('nexuscli.nexus_client.RepositoryCollection')
    mocker.patch.object(nexus_client.NexusClient, 'read_config')

    client = nexus_client.NexusClient(**client_args)
    client.write_config()

    mocker.patch.object(nexus_client.NexusClient, 'set_config')
    client_with_config = nexus_client.NexusClient(
        config_path=client_args['config_path'])

    x_args = (client_args['user'], client_args['password'], client_args['url'])
    assert client_with_config.set_config.called_with(*x_args)
