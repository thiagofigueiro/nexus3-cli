import itertools
import pytest

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
def test_repo_create_hosted(repo_format, w_policy, strict):
    strict_name = strict[2:8]
    repo_name = 'hosted-{repo_format}-{w_policy}-{strict_name}'.format(
        **locals())
    argv = pytest.helpers.create_argv(
        'repo create hosted {repo_format} {repo_name} --write={w_policy} '
        '{strict}', **locals())

    assert pytest.helpers.create_and_inspect(argv, repo_name)


@pytest.mark.parametrize(
    'v_policy, l_policy, w_policy, strict', itertools.product(
        repository.validations.VERSION_POLICIES,  # v_policy
        repository.validations.LAYOUT_POLICIES,  # l_policy
        repository.validations.WRITE_POLICIES,  # w_policy
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_hosted_maven(v_policy, l_policy, w_policy, strict):
    strict_name = strict[2:8]
    repo_name = ('hosted-maven-{v_policy}-{l_policy}-{w_policy}'
                 '-{strict_name}').format(**locals())
    argv = pytest.helpers.create_argv(
        'repo create hosted maven {repo_name} --write={w_policy} '
        '--layout={l_policy} --version={v_policy} {strict}', **locals())

    assert pytest.helpers.create_and_inspect(argv, repo_name)


@pytest.mark.parametrize(
    'w_policy, depth, strict', itertools.product(
        repository.validations.WRITE_POLICIES,  # w_policy
        list(range(6)),  # depth
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_hosted_yum(w_policy, depth, strict):
    strict_name = strict[2:8]
    repo_name = 'hosted-yum-{w_policy}-{depth}-{strict_name}'.format(
        **locals())
    argv = pytest.helpers.create_argv(
        'repo create hosted yum {repo_name} --write={w_policy} '
        '--depth={depth} {strict}', **locals())

    assert pytest.helpers.create_and_inspect(argv, repo_name)


@pytest.mark.parametrize(
    'repo_format, strict', itertools.product(
        repository.validations.SUPPORTED_FORMATS,  # format
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_proxy(repo_format, strict, faker):
    """
    Test all variations of this command:

    nexus3 repo create proxy (npm|pypi|raw|rubygems|yum)
           <repo_name> <remote_url>
           [--blob=<store_name>] [--strict-content]
    """
    strict_name = strict[2:8]
    remote_url = faker.uri()
    repo_name = 'proxy-{repo_format}-{strict_name}'.format(
        **locals())
    argv = pytest.helpers.create_argv(
        'repo create proxy {repo_format} {repo_name} {remote_url} '
        '{strict}', **locals())

    assert pytest.helpers.create_and_inspect(argv, repo_name)


@pytest.mark.parametrize(
    'v_policy, l_policy, strict', itertools.product(
        repository.validations.VERSION_POLICIES,  # v_policy
        repository.validations.LAYOUT_POLICIES,  # l_policy
        ['', '--strict-content'],  # strict
    ))
@pytest.mark.integration
def test_repo_create_proxy_maven(v_policy, l_policy, strict, faker):
    """
    Test all variations of this command:

    nexus3 repo create proxy maven <repo_name> <remote_url>
           [--blob=<store_name>] [--version=<v_policy>]
           [--layout=<l_policy>] [--strict-content]
    """
    strict_name = strict[2:8]
    remote_url = faker.uri()
    repo_name = 'proxy-maven-{v_policy}-{l_policy}-{strict_name}'.format(
        **locals())
    argv = pytest.helpers.create_argv(
        'repo create proxy maven {repo_name} {remote_url} '
        '--layout={l_policy} --version={v_policy} {strict}', **locals())

    assert pytest.helpers.create_and_inspect(argv, repo_name)


@pytest.mark.integration
def test_list(faker):
    repo_name = faker.pystr()
    argv_create = pytest.helpers.create_argv(
        'repo create hosted raw {repo_name}', **locals())
    argv_list = pytest.helpers.create_argv('list {repo_name}', **locals())

    assert pytest.helpers.create_and_inspect(argv_create, repo_name)
    assert nexuscli.cli.main(argv=list(filter(None, argv_list))) is None


@pytest.mark.integration
def test_repo_rm(nexus_client):
    """Test that `repo rm` will remove an existing repository"""
    # TODO: create random repo
    argv_rm = pytest.helpers.create_argv(
        'repo rm -f maven-public', **locals())
    nexuscli.cli.main(argv=list(filter(None, argv_rm)))
    repositories = nexus_client.repo_list()

    assert not any(r['name'] == 'maven-public' for r in repositories)


@pytest.mark.integration
def test_script(nexus_client):
    """Test that the `repo script` commands for create, run and rm work"""
    x_name = 'test_script_run'
    argv = 'script create tests/fixtures/script.json'.split(' ')
    nexuscli.cli.main(argv=argv)

    scripts = nexus_client.scripts.list()
    script_names = [s.get('name') for s in scripts]

    argv = 'script run {}'.format(x_name).split(' ')
    nexuscli.cli.main(argv=argv)

    argv = 'script rm {}'.format(x_name).split(' ')
    nexuscli.cli.main(argv=argv)

    scripts = nexus_client.scripts.list()
    rm_script_names = [s.get('name') for s in scripts]

    assert x_name in script_names
    assert x_name not in rm_script_names
