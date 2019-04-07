import pytest
from subprocess import check_call, check_output


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
