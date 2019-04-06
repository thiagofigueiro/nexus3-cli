import itertools
import pytest
from subprocess import check_call, check_output

import nexuscli
from nexuscli import repository


def test_login(mocker):
    mocker.patch('nexuscli.cli.do_login')
    mocker.patch('nexuscli.cli.NexusClient')

    nexuscli.cli.main(argv=['login'])

    nexuscli.cli.do_login.assert_called_once()
    nexuscli.cli.NexusClient.assert_called_once()


def test_repo_list(mocker):
    mocker.patch('nexuscli.cli.get_client')
    mocker.patch('nexuscli.cli.cmd_repo_do_list')

    argv = 'repo list'.split(' ')
    nexuscli.cli.main(argv=argv)

    nexuscli.cli.get_client.assert_called_once()
    nexuscli.cli.cmd_repo_do_list.assert_called_with(
        nexuscli.cli.get_client.return_value)


@pytest.mark.parametrize(
    'repo_format, w_policy, strict', itertools.product(
        repository.validations.SUPPORTED_FORMATS,  # format
        repository.validations.WRITE_POLICIES,  # w_policy
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_hosted(nexus_client, repo_format, w_policy, strict):
    strict_name = strict[2:8]
    repo_name = f'hosted-{repo_format}-{w_policy}-{strict_name}'
    argv = pytest.helpers.create_argv(
        'repo create hosted {repo_format} {repo_name} --write={w_policy} '
        '{strict}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'v_policy, l_policy, w_policy, strict', itertools.product(
        repository.validations.VERSION_POLICIES,  # v_policy
        repository.validations.LAYOUT_POLICIES,  # l_policy
        repository.validations.WRITE_POLICIES,  # w_policy
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_hosted_maven(
        nexus_client, v_policy, l_policy, w_policy, strict):
    strict_name = strict[2:8]
    repo_name = f'hosted-maven-{v_policy}-{l_policy}-{w_policy}-{strict_name}'
    argv = pytest.helpers.create_argv(
        'repo create hosted maven {repo_name} --write={w_policy} '
        '--layout={l_policy} --version={v_policy} {strict}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'w_policy, depth, strict', itertools.product(
        repository.validations.WRITE_POLICIES,  # w_policy
        list(range(6)),  # depth
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_hosted_yum(nexus_client, w_policy, depth, strict):
    strict_name = strict[2:8]
    repo_name = f'hosted-yum-{w_policy}-{depth}-{strict_name}'
    argv = pytest.helpers.create_argv(
        'repo create hosted yum {repo_name} --write={w_policy} '
        '--depth={depth} {strict}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'repo_format, strict', itertools.product(
        repository.validations.SUPPORTED_FORMATS,  # format
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_proxy(nexus_client, repo_format, strict, faker):
    """
    Test all variations of this command:

    nexus3 repo create proxy (npm|pypi|raw|rubygems|yum)
           <repo_name> <remote_url>
           [--blob=<store_name>] [--strict-content]
    """
    strict_name = strict[2:8]
    remote_url = faker.uri()
    repo_name = f'proxy-{repo_format}-{strict_name}'
    argv = pytest.helpers.create_argv(
        'repo create proxy {repo_format} {repo_name} {remote_url} '
        '{strict}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'v_policy, l_policy, strict', itertools.product(
        repository.validations.VERSION_POLICIES,  # v_policy
        repository.validations.LAYOUT_POLICIES,  # l_policy
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_proxy_maven(
        nexus_client, v_policy, l_policy, strict, faker):
    """
    Test all variations of this command:

    nexus3 repo create proxy maven <repo_name> <remote_url>
           [--blob=<store_name>] [--version=<v_policy>]
           [--layout=<l_policy>] [--strict-content]
    """
    strict_name = strict[2:8]
    remote_url = faker.uri()
    repo_name = f'proxy-maven-{v_policy}-{l_policy}-{strict_name}'
    argv = pytest.helpers.create_argv(
        'repo create proxy maven {repo_name} {remote_url} '
        '--layout={l_policy} --version={v_policy} {strict}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.integration
def test_list(nexus_client, faker):
    repo_name = faker.pystr()
    argv_create = pytest.helpers.create_argv(
        'repo create hosted raw {repo_name}', **locals())
    argv_list = pytest.helpers.create_argv('list {repo_name}', **locals())

    assert pytest.helpers.create_and_inspect(
        nexus_client, argv_create, repo_name)
    assert nexuscli.cli.main(argv=list(filter(None, argv_list))) is None


@pytest.mark.integration
def test_repo_rm(nexus_client):
    """Test that `repo rm` will remove an existing repository"""
    # TODO: create random repo
    argv_rm = pytest.helpers.create_argv(
        'repo rm -f maven-public', **locals())
    nexuscli.cli.main(argv=list(filter(None, argv_rm)))
    repositories = nexus_client.repositories.raw_list()

    assert not any(r['name'] == 'maven-public' for r in repositories)


@pytest.mark.integration
def test_script(nexus_client):
    """Test that the `repo script` commands for create, run and rm work"""
    x_name = 'test_script_run'
    argv = f'script create {x_name} tests/fixtures/script.groovy'.split(' ')
    nexuscli.cli.main(argv=argv)

    scripts = nexus_client.scripts.list()
    script_names = [s.get('name') for s in scripts]

    argv = 'script run {}'.format(x_name).split(' ')
    nexuscli.cli.main(argv=argv)

    argv = 'script del {}'.format(x_name).split(' ')
    nexuscli.cli.main(argv=argv)

    scripts = nexus_client.scripts.list()
    rm_script_names = [s.get('name') for s in scripts]

    assert x_name in script_names
    assert x_name not in rm_script_names


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


@pytest.mark.integration
def test_download(hosted_raw_repo_empty, deep_file_tree, faker, tmpdir):
    """Ensure that `nexus3 download` command works"""
    src_dir, x_file_set = deep_file_tree
    dst_dir = faker.uri_path() + '/'

    repo_name = hosted_raw_repo_empty

    dest_repo_path = '{}/{}'.format(repo_name, dst_dir)

    upload_command = f'nexus3 upload {src_dir} {dest_repo_path}'

    retcode = check_call(upload_command.split())
    assert retcode == 0

    download_dest = str(tmpdir)
    download_command = f'nexus3 download {dest_repo_path} {download_dest}'

    retcode = check_call(download_command.split())
    assert retcode == 0


@pytest.mark.integration
def test_delete(hosted_raw_repo_empty, deep_file_tree, faker, tmpdir):
    """Ensure that `nexus3 delete` command works"""
    src_dir, x_file_set = deep_file_tree
    dst_dir = faker.uri_path() + '/'

    repo_name = hosted_raw_repo_empty

    dest_repo_path = '{}/{}/'.format(repo_name, dst_dir)

    upload_command = f'nexus3 upload {src_dir} {dest_repo_path}'

    retcode = check_call(upload_command.split())
    assert retcode == 0

    delete_command = f'nexus3 delete {dest_repo_path}'

    retcode = check_call(delete_command.split())
    assert retcode == 0


@pytest.mark.integration
def test_cleanup_policy(faker):
    """Ensure the command creates a new policy and that is shows on the list"""
    x_name = faker.pystr()
    # CLI accepts days, Nexus stores seconds
    downloaded = faker.random_int(1, 365)
    x_downloaded = str(downloaded * 86400)
    updated = faker.random_int(1, 365)
    x_updated = str(updated * 86400)

    create_command = (f'nexus3 cleanup_policy create {x_name} '
                      f'--downloaded={downloaded} --updated={updated}')
    list_command = 'nexus3 cleanup_policy list'

    create_retcode = check_call(create_command.split())
    output = check_output(list_command.split(), encoding='utf-8')

    # find our entry in output
    entry = ''
    for line in output.splitlines():
        print('checking', line)
        if line.startswith(x_name):
            entry = line
            break

    assert create_retcode == 0
    assert x_name in entry
    assert x_downloaded in entry
    assert x_updated in entry
    assert 'ALL_FORMATS' in entry
