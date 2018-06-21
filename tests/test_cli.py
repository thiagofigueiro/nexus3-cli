import itertools
import pytest

from nexuscli import nexus_repository
import nexuscli


def test_login(mocker):
    mocker.patch('nexuscli.cli.do_login')
    mocker.patch('nexuscli.cli.get_client')

    nexuscli.cli.main(argv=['login'])

    nexuscli.cli.do_login.assert_called_once()
    nexuscli.cli.get_client.assert_called_once()


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
        ['npm', 'pypi', 'raw', 'rubygems'],  # format
        list(nexus_repository.POLICIES['write']),  # w_policy
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
        list(nexus_repository.POLICIES['version']),  # v_policy
        list(nexus_repository.POLICIES['layout']),  # l_policy
        list(nexus_repository.POLICIES['write']),  # w_policy
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
        list(nexus_repository.POLICIES['write']),  # w_policy
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
        ['npm', 'pypi', 'raw', 'rubygems', 'yum'],  # format
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
        list(nexus_repository.POLICIES['version']),  # v_policy
        list(nexus_repository.POLICIES['layout']),  # l_policy
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
