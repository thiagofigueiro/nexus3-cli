import os
import pytest
from faker import Faker

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


def nexus_artefact():
    """
    See nexus_util.filtered_list_gen for raw_response format.
    """
    fake = Faker()

    fixture = {
        'checksum': {
            'md5': fake.md5(),
            'sha1': fake.sha1(),
            'sha256': fake.sha256(),
        },
        'downloadUrl': None,
        'format': None,
        'id': fake.pystr(min_chars=63, max_chars=63),
        'path': None,
        'repository': None,
    }

    return fixture


@pytest.helpers.register
def nexus_raw_response(file_list, repository=None):
    """
    See nexus_util.filtered_list_gen for raw_response format.
    """
    for artefact_path in file_list:
        artefact = nexus_artefact()
        artefact['path'] = artefact_path
        artefact['repository'] = repository or 'some_repository'
        yield artefact


@pytest.fixture
def file_upload_args(faker):
    """A tuple of arguments suitable for use with NexusClient"""
    x_src_file = faker.file_path()[1:]  # relative paths make testing easier
    x_dst_file = os.path.basename(x_src_file)
    x_repo_name = faker.uri_page()
    x_dst_dir = faker.uri_path()

    return x_src_file, x_repo_name, x_dst_dir, x_dst_file


@pytest.helpers.register
def nexus_repository(name, format_):
    return {
        'name': name,
        'format': format_,
    }


@pytest.fixture
def nexus_mock_client(mocker, faker):
    """A nexus_client with the request method mocked"""
    class ResponseMock:
        def __init__(self):
            self.status_code = 200
            self.content = faker.sentence()
            self.reason = faker.sentence()
            # get ready for refresh_repositories
            self._json = [
                nexus_repository(
                    name=faker.pystr(),
                    format_=faker.random.choice(
                        ['pypi', 'nuget', 'raw', 'yum', 'rubygems'])
                )
                for _ in range(faker.random_int(1, 10))
            ]

        def json(self):
            return self._json

    mocker.patch('nexuscli.nexus_client.NexusClient._request',
                 return_value=ResponseMock())

    return nexuscli.nexus_client.NexusClient()
