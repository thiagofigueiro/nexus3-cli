import itertools
import os
import pytest

from nexuscli.cli import nexus_cli


@pytest.mark.integration
def test_upload_tree(nexus_client, deep_file_tree, faker):
    """
    Create a repository, upload a random file tree to Nexus and check that the
    resulting list of files in nexus corresponds to the uploaded list of files.
    """
    src_dir, x_file_set = deep_file_tree
    repo_name = faker.pystr()
    dst_dir = faker.uri_path() + '/'
    path = dst_dir[:-1] + src_dir

    argv = ('repository create hosted raw {}'.format(repo_name)).split()
    pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)
    nexus_client.repositories.refresh()

    r = nexus_client.repositories.get_by_name(repo_name)
    count = r.upload_directory(src_dir, dst_dir)
    file_set = pytest.helpers.repo_list(nexus_client, repo_name, count, path)

    assert file_set == x_file_set


@pytest.mark.integration
def test_upload_root(nexus_client, make_testfile, faker):
    """
    Create a repository, upload a random file to the root of a Nexus raw repo
    and check that the resulting list of files in nexus corresponds to
    the uploaded list of files.
    """
    src_dir, src_file = make_testfile
    repo_name = faker.pystr()
    dst_dir = '/'

    argv = ('repository create hosted raw {}'.format(repo_name)).split()
    pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)
    nexus_client.repositories.refresh()

    r = nexus_client.repositories.get_by_name(repo_name)
    r.upload_file(os.path.join(src_dir, src_file), dst_dir)
    file_set = pytest.helpers.repo_list(nexus_client, repo_name, 1)

    assert file_set == set([src_file])


@pytest.mark.parametrize('cmd,flatten,recurse', itertools.product(
    ['up', 'upload'],
    ['--flatten', '--no-flatten'],
    ['--recurse', '--no-recurse'],
))
def test_upload(
        cmd, flatten, recurse, nexus_mock_client, mocker, upload_args_factory,
        cli_runner):
    """
    Ensure all accepted variations of the upload command result in the
    cmd_upload method being called.
    https://github.com/thiagofigueiro/nexus3-cli/issues/76
    """
    mocker.patch(
        'nexuscli.cli.util.get_client', return_value=nexus_mock_client)
    mock_cmd_upload = mocker.patch('nexuscli.cli.root_commands.cmd_upload')

    args, xargs = upload_args_factory(cmd, flatten, recurse)

    result = cli_runner.invoke(nexus_cli, args)

    assert result.exit_code == 0
    mock_cmd_upload.assert_called_with(nexus_mock_client, **xargs)
