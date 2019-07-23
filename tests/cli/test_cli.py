import pytest
from subprocess import check_call
from time import sleep

from nexuscli import cli


def test_login(mocker):
    """Ensure it calls the expected method"""
    mocker.patch('nexuscli.cli.cmd_login')

    cli.main(argv=['login'])

    cli.cmd_login.assert_called_once()


@pytest.mark.integration
def test_list(nexus_client, faker):
    repo_name = faker.pystr()
    argv_create = pytest.helpers.create_argv(
        'repository create hosted raw {repo_name}', **locals())
    argv_list = pytest.helpers.create_argv('list {repo_name}', **locals())

    has_created = pytest.helpers.create_and_inspect(
        nexus_client, argv_create, repo_name)
    exit_code = cli.main(argv=list(filter(None, argv_list)))

    assert has_created
    assert exit_code == 0


@pytest.mark.integration
def test_upload(hosted_raw_repo_empty, deep_file_tree, faker):
    """Ensure that `nexus3 upload` command works"""
    src_dir, x_file_set = deep_file_tree
    dst_dir = faker.uri_path() + '/'

    repo_name = hosted_raw_repo_empty
    dest_repo_path = '{}/{}'.format(repo_name, dst_dir)
    upload_command = f'nexus3 upload {src_dir} {dest_repo_path}'

    retcode = check_call(upload_command.split())

    assert retcode == 0


@pytest.mark.xfail(reason='Nexus takes too long to index uploaded files')
@pytest.mark.integration
def test_download(hosted_raw_repo_empty, deep_file_tree, faker, tmpdir):
    """Ensure that `nexus3 download` command works"""
    src_dir, x_file_set = deep_file_tree
    dst_dir = faker.uri_path()

    repo_name = hosted_raw_repo_empty

    dest_repo_path = f'{repo_name}/{dst_dir}'
    upload_command = f'nexus3 upload {src_dir} {dest_repo_path}/'
    retcode = check_call(upload_command.split())
    assert retcode == 0

    # FIXME: force Nexus 3 to reindex so there's no need to sleep
    sleep(5)

    download_dest = str(tmpdir)
    download_command = f'nexus3 download {dest_repo_path} {download_dest}/'
    retcode = check_call(download_command.split())
    assert retcode == 0


@pytest.mark.integration
def test_delete(hosted_raw_repo_empty, deep_file_tree, faker):
    """Ensure that `nexus3 delete` command works"""
    src_dir, x_file_set = deep_file_tree
    dst_dir = faker.uri_path() + '/'

    repo_name = hosted_raw_repo_empty

    dest_repo_path = '{}/{}/'.format(repo_name, dst_dir)
    upload_command = f'nexus3 upload {src_dir} {dest_repo_path}'
    retcode = check_call(upload_command.split())
    assert retcode == 0

    # FIXME: force Nexus 3 to reindex so there's no need to sleep
    sleep(5)

    delete_command = f'nexus3 delete {dest_repo_path}'
    retcode = check_call(delete_command.split())
    assert retcode == 0
