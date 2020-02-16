import pytest

from nexuscli.cli import nexus_cli

SCRIPT_NAME = 'test_script_run'


@pytest.mark.integration
def test_create(cli_runner, nexus_client):
    """Test that the `repo script` commands for create, run and rm work"""
    cmd_create = f'script create {SCRIPT_NAME} tests/fixtures/script.groovy'
    result = cli_runner.invoke(nexus_cli, cmd_create)

    assert result.exit_code == 0
    assert result.output == ''
    assert SCRIPT_NAME in [s.get('name') for s in nexus_client.scripts.list()]


@pytest.mark.integration
def test_run(cli_runner, nexus_client):
    """Test that the `repo script` commands for create, run and rm work"""
    cmd_run = f'script run {SCRIPT_NAME}'
    result = cli_runner.invoke(nexus_cli, cmd_run)

    assert result.exit_code == 0
    assert SCRIPT_NAME in result.output


@pytest.mark.integration
def test_del(cli_runner, nexus_client):
    """Test that the `repo script` commands for create, run and rm work"""
    cmd_del = f'script del {SCRIPT_NAME}'
    result = cli_runner.invoke(nexus_cli, cmd_del)

    assert result.exit_code == 0
    assert result.output == ''
    assert SCRIPT_NAME not in [
        s.get('name') for s in nexus_client.scripts.list()]
