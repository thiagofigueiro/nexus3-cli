import pytest
import itertools

from nexuscli.api import repository
from nexuscli.cli import subcommand_repository


SUPPORTED_FORMATS = set(
    [recipe for cls in repository.model.__all__ for recipe in cls.RECIPES])


def test_list(mocker):
    mocker.patch('nexuscli.cli.subcommand_repository.util.get_client')
    mocker.patch('nexuscli.cli.subcommand_repository.cmd_list')

    argv = 'repository list'.split(' ')
    subcommand_repository.main(argv=argv)

    subcommand_repository.util.get_client.assert_called_once()
    subcommand_repository.cmd_list.assert_called_once()


@pytest.mark.parametrize(
    'repo_format, w_policy, strict, c_policy', itertools.product(
        SUPPORTED_FORMATS,  # format
        repository.model.HostedRepository.WRITE_POLICIES,  # w_policy
        ['', '--strict-content'],  # strict
        ['', '--cleanup=c_policy'],  # c_policy
    ))
@pytest.mark.integration
def test_create_hosted(nexus_client, repo_format, w_policy, strict, c_policy):
    strict_name = strict[2:8]
    repo_name = pytest.helpers.repo_name(
        'hosted', repo_format, w_policy, strict, c_policy)
    argv = pytest.helpers.create_argv(
        'repository create hosted {repo_format} {repo_name} '
        '--write={w_policy} {strict} {c_policy}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'v_policy, l_policy, w_policy, strict, c_policy', itertools.product(
        repository.model.MavenRepository.VERSION_POLICIES,  # v_policy
        repository.model.MavenRepository.LAYOUT_POLICIES,  # l_policy
        repository.model.HostedRepository.WRITE_POLICIES,  # w_policy
        ['', '--strict-content'],  # strict
        [None, 'Some'],  # c_policy
    ))
@pytest.mark.integration
def test_create_hosted_maven(
        nexus_client, v_policy, l_policy, w_policy, strict, c_policy):
    strict_name = strict[2:8]
    repo_name = pytest.helpers.repo_name(
        'hosted-maven', v_policy, l_policy, w_policy, strict, c_policy)
    argv = pytest.helpers.create_argv(
        'repository create hosted maven {repo_name} --write={w_policy} '
        '--layout={l_policy} --version={v_policy} {strict} '
        '--cleanup={c_policy}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'w_policy, depth, strict, c_policy', itertools.product(
        repository.model.HostedRepository.WRITE_POLICIES,  # w_policy
        list(range(6)),  # depth
        ['', '--strict-content'],  # strict
        [None, 'Some'],  # c_policy
    ))
@pytest.mark.integration
def test_create_hosted_yum(nexus_client, w_policy, depth, strict, c_policy):
    strict_name = strict[2:8]
    repo_name = pytest.helpers.repo_name(
        'hosted-yum', w_policy, depth, strict, c_policy)
    argv = pytest.helpers.create_argv(
        'repository create hosted yum {repo_name} --write={w_policy} '
        '--depth={depth} {strict} --cleanup={c_policy}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)
    assert nexus_client.repositories.get_by_name(repo_name).depth == depth


@pytest.mark.parametrize(
    'repo_format, strict, c_policy, remote_auth_type', itertools.product(
        SUPPORTED_FORMATS,  # format
        ['', '--strict-content'],  # strict
        [None, 'Some'],  # c_policy
        [(None, None, None),  # remote_auth_type
         ('username', 'username', 'password')]
    ))
@pytest.mark.integration
def test_create_proxy(nexus_client, repo_format, strict,
                      c_policy, remote_auth_type, faker):
    """
    Test all variations of this command:

    nexus3 repository create proxy (bower|npm|nuget|pypi|raw|rubygems|yum)
         <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--remote_auth_type=<remote_auth_type>]
         [--remote_username=<username>] [--remote_username=<password>]
    """
    strict_name = strict[2:8]
    remote_url = faker.uri()
    repo_name = pytest.helpers.repo_name(
        'proxy', repo_format, strict, c_policy,
        remote_auth_type[0])
    print(repo_name)
    argv = pytest.helpers.create_argv(
        'repository create proxy {repo_format} {repo_name} {remote_url} '
        '{strict} --cleanup={c_policy} '
        '--remote_auth_type={remote_auth_type[0]} '
        '--remote_username={remote_auth_type[1]} '
        '--remote_password={remote_auth_type[2]}', **locals())
    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'v_policy, l_policy, strict, c_policy, '
    'remote_auth_type', itertools.product(
        repository.model.MavenRepository.VERSION_POLICIES,  # v_policy
        repository.model.MavenRepository.LAYOUT_POLICIES,  # l_policy
        ['', '--strict-content'],  # strict
        [None, 'Some'],  # c_policy
        [(None, None, None),  # remote_auth_type
         ('username', 'username', 'password')],
    ))
@pytest.mark.integration
def test_create_proxy_maven(
        nexus_client, v_policy, l_policy, strict,
        c_policy, remote_auth_type, faker):
    """
    Test all variations of this command:

    nexus3 repo create proxy maven <repo_name> <remote_url>
           [--blob=<store_name>] [--version=<v_policy>]
           [--layout=<l_policy>] [--strict-content] --cleanup c_policy
    """
    strict_name = strict[2:8]
    remote_url = faker.uri()
    repo_name = pytest.helpers.repo_name(
        'proxy-maven', v_policy, l_policy, strict, c_policy,
        remote_auth_type[0])
    print(repo_name)
    argv = pytest.helpers.create_argv(
        'repository create proxy maven {repo_name} {remote_url} '
        '--layout={l_policy} --version={v_policy} {strict} '
        '--cleanup={c_policy} '
        '--remote_auth_type={remote_auth_type[0]} '
        '--remote_username={remote_auth_type[1]} '
        '--remote_password={remote_auth_type[2]}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.parametrize(
    'v1_enabled, force_basic_auth, index_type, '
    'strict, c_policy, remote_auth_type', itertools.product(
        ['', '--v1_enabled'],  # v1_enabled
        ['', '--force_basic_auth'],  # basic_auth
        ('registry', 'custom', 'hub'),  # index_type
        ['', '--strict-content'],  # strict
        [None, 'Some'],  # c_policy
        [(None, None, None),  # remote_auth_type
         ('username', 'username', 'password')],
    ))
@pytest.mark.integration
def test_create_proxy_docker(
        nexus_client, v1_enabled, force_basic_auth,
        index_type, strict, c_policy, remote_auth_type, faker):
    """
    Test all variations of this command:

    nexus3 repo create proxy docker <repo_name> <remote_url>
           [--blob=<store_name>] [--version=<v_policy>]
           [--v1_enabled=<v1_enabled>] [--force_basic_auth=<force_basic_auth>]
           [--index_type=<index_type] [--strict-content] --cleanup c_policy
    """
    strict_name = strict[2:8]
    remote_url = faker.uri()
    repo_name = pytest.helpers.repo_name(
        'proxy-docker', v1_enabled, force_basic_auth,
        index_type, strict, c_policy,
        remote_auth_type[0])
    print(repo_name)
    argv = pytest.helpers.create_argv(
        'repository create proxy docker {repo_name} {remote_url} '
        '{v1_enabled} {force_basic_auth} --index_type={index_type} '
        '{strict} --cleanup={c_policy} '
        '--remote_auth_type={remote_auth_type[0]} '
        '--remote_username={remote_auth_type[1]} '
        '--remote_password={remote_auth_type[2]}', **locals())

    assert pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)


@pytest.mark.integration
def test_del(nexus_client):
    """Test that `repo rm` will remove an existing repository"""
    # TODO: create random repo
    argv_rm = pytest.helpers.create_argv(
        'repository del maven-public -f', **locals())
    subcommand_repository.main(argv=list(filter(None, argv_rm)))
    repositories = nexus_client.repositories.raw_list()

    assert not any(r['name'] == 'maven-public' for r in repositories)
