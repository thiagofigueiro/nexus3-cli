import os
import pytest
import time
from faker import Faker
from subprocess import check_call

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
    repositories = nexus_client().repositories.raw_list()

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
            # prepare content for repositories.refresh()
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

    client = nexuscli.nexus_client.NexusClient()
    client.repositories.refresh()
    return client


@pytest.fixture
def deep_file_tree(faker, tmpdir):
    """
    Yields a tuple(str, set). The str is the current working directory. The
    list contains deep file paths, relative to the current working dir, where
    all files exist in the filesystem.
    """
    fixture = []
    with tmpdir.as_cwd():
        for _ in range(faker.random_int(1, 100)):
            relative_path = faker.file_path(
                depth=faker.random_number(1, 10))[1:]
            fixture.append(relative_path)
            tmpdir.join(relative_path).ensure()

    yield str(tmpdir), set(fixture)


@pytest.helpers.register
def repo_list(client, repo_name, expected_count, repo_path):
    """
    Nexus doesn't show uploaded files when you list the contents immediately
    after an upload. This helper retries it 3 times with increasing back-off.
    """
    def _list():
        file_list = client.list(repo_name)

        files = []
        for f in iter(file_list):
            files.append(f[len(repo_path)+1:])

        return files

    attempt = 1
    file_set = set(_list())
    while len(file_set) != expected_count and attempt < 4:
        attempt += 1
        time.sleep(2 * attempt)
        file_set = set(_list())

    # let it fail if we run out of attempts
    return file_set


@pytest.helpers.register
def find_file_count(dir_name):
    """Find the number of files in a directory"""
    file_list = [
        f for f in os.listdir(dir_name)
        if os.path.isfile(os.path.join(dir_name, f))
    ]
    return len(file_list)


@pytest.fixture
def hosted_raw_repo_empty(tmpdir, faker):
    repo_name = faker.word()
    command = 'nexus3 repo create hosted raw {}'.format(repo_name)
    check_call(command.split())
    return repo_name
