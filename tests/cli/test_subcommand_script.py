import pytest

from nexuscli.cli import subcommand_script


@pytest.mark.integration
def test_script(nexus_client):
    """Test that the `repo script` commands for create, run and rm work"""
    x_name = 'test_script_run'
    argv = f'script create {x_name} tests/fixtures/script.groovy'.split(' ')
    subcommand_script.main(argv=argv)

    scripts = nexus_client.scripts.list()
    script_names = [s.get('name') for s in scripts]

    argv = 'script run {}'.format(x_name).split(' ')
    subcommand_script.main(argv=argv)

    argv = 'script del {}'.format(x_name).split(' ')
    subcommand_script.main(argv=argv)

    scripts = nexus_client.scripts.list()
    rm_script_names = [s.get('name') for s in scripts]

    assert x_name in script_names
    assert x_name not in rm_script_names
