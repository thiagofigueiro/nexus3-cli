from time import sleep
import pytest

from nexuscli.cli import nexus_cli
from nexuscli import exception


def test_login(cli_runner, mocker, login_env):
    """Ensure it calls the expected method"""
    env, xargs = login_env
    mock_cmd_login = mocker.patch('nexuscli.cli.root_commands.cmd_login')

    result = cli_runner.invoke(nexus_cli, 'login', env=env)

    assert result.exit_code == 0
    mock_cmd_login.assert_called_with(**xargs)


@pytest.mark.parametrize('repo_name', [
    'maven-snapshots', 'maven-central', 'nuget-group', 'maven-releases',
    'nuget-hosted'])
@pytest.mark.integration
def test_list(repo_name, cli_runner, faker):
    result = cli_runner.invoke(nexus_cli, f'list {repo_name}/')

    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert result.output == ''


# TODO: upload to all repository types
@pytest.mark.integration
def test_upload(cli_runner, upload_repo, faker):
    """Ensure that `nexus3 upload` command works"""
    repo_name, src_dir, x_file_list = upload_repo
    xcount = len(x_file_list)
    dst_dir = faker.uri_path() + '/'

    upload_command = f'upload {src_dir} {repo_name}/{dst_dir}'

    result = cli_runner.invoke(nexus_cli, upload_command)

    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert f'\nUploaded {xcount} file' in result.output


@pytest.mark.integration
def test_download(cli_runner, upload_repo, tmpdir):
    """
    Ensure that `nexus3 download` command works. This test relies on
    `test_upload` running in the same session.
    """
    repo_name, _, x_file_list = upload_repo
    xcount = len(x_file_list)

    # Wait for Nexus 3 to reindex
    sleep(5)

    download_to = str(tmpdir)
    download_cmd = f'download {repo_name}/ {download_to}/'
    result = cli_runner.invoke(nexus_cli, download_cmd)

    assert result.exit_code == 0
    assert f'Downloaded {xcount} file' in result.output


@pytest.mark.integration
def test_delete(cli_runner, upload_repo, tmpdir):
    """
    Ensure that `nexus3 delete` command works. This test relies on
    `test_upload` running in the same session.
    """
    repo_name, _, x_file_list = upload_repo
    xcount = len(x_file_list)

    result = cli_runner.invoke(nexus_cli, f'delete {repo_name}/')

    assert result.exit_code == 0
    assert f'Deleted {xcount} file' in result.output
