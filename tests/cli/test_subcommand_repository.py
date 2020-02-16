import pytest
import itertools

from nexuscli import exception
from nexuscli.api import repository
from nexuscli.cli import nexus_cli, subcommand_repository


def test_list(cli_runner, mocker):
    client = mocker.patch('nexuscli.cli.subcommand_repository.util.get_client')
    mocker.patch('nexuscli.cli.subcommand_repository.cmd_list')

    result = cli_runner.invoke(nexus_cli, 'repository list')

    assert result.exit_code == 0
    subcommand_repository.util.get_client.assert_called_with()
    subcommand_repository.cmd_list.assert_called_with(client.return_value)


@pytest.mark.parametrize(
    'repo_format, w_policy, strict, c_policy', itertools.product(
        repository.model.HostedRepository.RECIPES,  # format
        repository.model.HostedRepository.WRITE_POLICIES,  # w_policy
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
    ))
@pytest.mark.integration
def test_create_hosted(
        nexus_client, cli_runner, repo_format, w_policy, strict, c_policy):
    repo_name = pytest.helpers.repo_name(
        'hosted', repo_format, w_policy, strict, c_policy)

    create_cmd = (
        f'repository create hosted {repo_format} {repo_name} '
        f'--write-policy={w_policy} {strict} {c_policy}')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name


@pytest.mark.parametrize(
    'v_policy, l_policy, w_policy, strict, c_policy', itertools.product(
        repository.model.MavenRepository.VERSION_POLICIES,  # v_policy
        repository.model.MavenRepository.LAYOUT_POLICIES,  # l_policy
        repository.model.HostedRepository.WRITE_POLICIES,  # w_policy
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
    ))
@pytest.mark.integration
def test_create_hosted_maven(
        v_policy, l_policy, w_policy, strict, c_policy, nexus_client,
        cli_runner):
    repo_name = pytest.helpers.repo_name(
        'hosted-maven', v_policy, l_policy, w_policy, strict, c_policy)
    create_cmd = (
        f'repository create hosted maven {repo_name} '
        f'--write-policy={w_policy} --layout-policy={l_policy} '
        f'--version-policy={v_policy} {strict} {c_policy}')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name


@pytest.mark.parametrize(
    'w_policy, depth, strict, c_policy', itertools.product(
        repository.model.HostedRepository.WRITE_POLICIES,  # w_policy
        list(range(6)),  # depth
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
    ))
@pytest.mark.integration
def test_create_hosted_yum(
        w_policy, depth, strict, c_policy, nexus_client, cli_runner):
    repo_name = pytest.helpers.repo_name(
        'hosted-yum', w_policy, depth, strict, c_policy)
    create_cmd = (
        f'repository create hosted yum {repo_name} --write-policy={w_policy} '
        f'--depth={depth} {strict} {c_policy}')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name
    assert nexus_client.repositories.get_by_name(repo_name).depth == depth


@pytest.mark.parametrize(
    'repo_format, strict, c_policy, remote_auth_type', itertools.product(
        repository.model.ProxyRepository.RECIPES,  # format
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
        [None, 'username']  # remote-auth-type
    ))
@pytest.mark.integration
def test_create_proxy(
        repo_format, strict, c_policy, remote_auth_type, faker, nexus_client,
        cli_runner):
    """ Test all variations of the `repository create proxy` command"""
    remote_url = faker.uri()
    repo_name = pytest.helpers.repo_name(
        'proxy', repo_format, strict, c_policy,
        remote_auth_type)
    create_cmd = (
        f'repository create proxy {repo_format} {repo_name} {remote_url} '
        f'{strict} {c_policy} ')
    if remote_auth_type is not None:
        create_cmd += (
            f'--remote-auth-type={remote_auth_type} '
            f'--remote-username={faker.user_name()} '
            f'--remote-password={faker.password()}')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name


@pytest.mark.parametrize(
    'v_policy, l_policy, strict, c_policy, '
    'remote_auth_type', itertools.product(
        repository.model.MavenRepository.VERSION_POLICIES,  # v_policy
        repository.model.MavenRepository.LAYOUT_POLICIES,  # l_policy
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
        [None, 'username'],  # remote-auth-type
    ))
@pytest.mark.integration
def test_create_proxy_maven(
        v_policy, l_policy, strict, c_policy, remote_auth_type, faker,
        nexus_client, cli_runner):
    """Test all variations of the `nexus3 repo create proxy maven ` command"""
    remote_url = faker.uri()
    repo_name = pytest.helpers.repo_name(
        'proxy-maven', v_policy, l_policy, strict, c_policy,
        remote_auth_type)
    create_cmd = (
        f'repository create proxy maven {repo_name} {remote_url} '
        f'--layout-policy={l_policy} --version-policy={v_policy} {strict} '
        f'--cleanup-policy={c_policy} ')

    if remote_auth_type is not None:
        create_cmd += (
            f'--remote-auth-type={remote_auth_type} '
            f'--remote-username={faker.user_name()} '
            f'--remote-password={faker.password()}')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name


@pytest.mark.parametrize(
    'v1_enabled, force_basic_auth, index_type, '
    'strict, c_policy, remote_auth_type', itertools.product(
        ['--no-v1-enabled', '--v1-enabled'],
        ['--no-force-basic-auth', '--force-basic-auth'],
        ('registry', 'custom', 'hub'),  # index_type
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
        [None, 'username'],  # remote-auth-type
    ))
@pytest.mark.integration
def test_create_proxy_docker(
        v1_enabled, force_basic_auth, index_type, strict, c_policy,
        remote_auth_type, faker, nexus_client, cli_runner):
    """Test all variations of the `repo create proxy docker` command"""
    remote_url = faker.uri()
    repo_name = pytest.helpers.repo_name(
        'proxy-docker', v1_enabled, force_basic_auth,
        index_type, strict, c_policy,
        remote_auth_type)
    create_cmd = (
        f'repository create proxy docker {repo_name} {remote_url} '
        f'{v1_enabled} {force_basic_auth} --index-type={index_type} '
        f'{strict} --cleanup-policy={c_policy} ')

    if remote_auth_type is not None:
        create_cmd += (
            f'--remote-auth-type={remote_auth_type} '
            f'--remote-username={faker.user_name()} '
            f'--remote-password={faker.password()}')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name


@pytest.mark.parametrize(
    'flat, strict, c_policy, remote_auth_type', itertools.product(
        ['--no-flat', '--flat'],  # flat
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
        [None, 'username'],  # remote-auth-type
    ))
@pytest.mark.integration
def test_create_proxy_apt(
        flat, strict, c_policy, remote_auth_type, faker, nexus_client,
        cli_runner):
    """Test all combinations of the `repository create proxy apt` command"""
    distribution = faker.pystr()
    remote_url = faker.uri()
    repo_name = pytest.helpers.repo_name(
        'proxy-apt', distribution, flat, strict, c_policy, remote_auth_type)

    create_cmd = (
        f'repository create proxy apt {repo_name} {remote_url} {flat} '
        f'--distribution={distribution} {strict} --cleanup-policy={c_policy} ')

    if remote_auth_type is not None:
        create_cmd += (
            f'--remote-auth-type={remote_auth_type} '
            f'--remote-username={faker.user_name()} '
            f'--remote-password={faker.password()}')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name


@pytest.mark.parametrize(
    'passphrase, w_policy, strict, c_policy', itertools.product(
        [None, 'passphrase'],  # passphrase
        repository.model.HostedRepository.WRITE_POLICIES,  # w_policy
        ['--no-strict-content', '--strict-content'],  # strict
        ['', '--cleanup-policy=c_policy'],  # c_policy
    ))
@pytest.mark.integration
def test_create_hosted_apt(
        passphrase, w_policy, strict, c_policy, apt_gpg_key_path, faker,
        nexus_client, cli_runner):
    """Test variations of the `repository create hosted apt` command"""
    distribution = faker.pystr()
    gpg_random = faker.pystr()
    repo_name = pytest.helpers.repo_name(
        'hosted-apt', gpg_random, distribution, strict, c_policy)

    create_cmd = (
        f'repository create hosted apt {repo_name} '
        f'--gpg-keypair={apt_gpg_key_path} --passphrase={passphrase} '
        f'--distribution={distribution} {strict} {c_policy} '
        f'--write-policy={w_policy} ')

    result = cli_runner.invoke(nexus_cli, create_cmd)

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert nexus_client.repositories.get_by_name(repo_name).name == repo_name


@pytest.mark.integration
def test_del(cli_runner, nexus_client, faker):
    """Test that `repo rm` will remove an existing repository"""
    repo_name = f'delete-test-{faker.pystr()}'

    create_cmd = f'repository create hosted raw {repo_name}'
    cli_runner.invoke(nexus_cli, create_cmd)
    repositories_before = nexus_client.repositories.raw_list()

    result = cli_runner.invoke(nexus_cli, f'repository del {repo_name} --yes')
    repositories_after = nexus_client.repositories.raw_list()

    assert result.output == ''
    assert result.exit_code == exception.CliReturnCode.SUCCESS.value
    assert any(r['name'] == repo_name for r in repositories_before)
    assert not any(r['name'] == repo_name for r in repositories_after)
