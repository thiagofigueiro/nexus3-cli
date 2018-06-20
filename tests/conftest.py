import pytest

import nexuscli


@pytest.fixture
def docopt_args(faker):
    args = {
        '--blob': 'default',
        '--deploy': 'disable',
        '--depth': '0',
        '--help': False,
        '--help,': False,
        '--layout': 'strict',
        '--strict-content': False,
        '--version': 'release',
        '<repo_name>': faker.word(),
        '<script.json>': None,
        '<script_name>': None,
        'create': False,
        'hosted': False,
        'list': False,
        'login': False,
        'maven2': True,
        'npm': False,
        'pypi': False,
        'raw': False,
        'repo': False,
        'rm': False,
        'rubygems': False,
        'run': False,
        'script': False,
        'yum': False
    }

    return args


@pytest.fixture(scope='session')
def nexus_client():
    return nexuscli.cli.get_client()


@pytest.helpers.register
def create_and_inspect(argv, expected_repo_name):
    nexuscli.cli.main(argv=list(filter(None, argv)))
    repositories = nexus_client().repo_list()

    return any(r['name'] == expected_repo_name for r in repositories)


@pytest.helpers.register
def create_argv(argv_string, **kwargs):
    argv = argv_string.format(**kwargs).split(' ')
    return list(filter(None, argv))
