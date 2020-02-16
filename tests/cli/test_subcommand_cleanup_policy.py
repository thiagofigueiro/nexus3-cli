import pytest

from nexuscli.cli import nexus_cli


@pytest.mark.integration
def test_cleanup_policy(cli_runner, faker):
    """Ensure the command creates a new policy and that is shows on the list"""
    x_name = faker.pystr()
    # CLI accepts days, Nexus stores seconds
    downloaded = faker.random_int(1, 365)
    x_downloaded = str(downloaded * 86400)
    updated = faker.random_int(1, 365)
    x_updated = str(updated * 86400)

    create_command = (f'cleanup-policy create {x_name} '
                      f'--downloaded={downloaded} --updated={updated}')
    list_command = 'cleanup-policy list'

    create_result = cli_runner.invoke(nexus_cli, create_command)
    list_result = cli_runner.invoke(nexus_cli, list_command)

    assert create_result.exit_code == 0
    assert create_result.output == ''
    assert list_result.exit_code == 0

    entry = ''
    for line in list_result.output.splitlines():
        print('checking', line)
        if line.startswith(x_name):
            entry = line
            break

    assert x_name in entry
    assert x_downloaded in entry
    assert x_updated in entry
    assert 'ALL_FORMATS' in entry
