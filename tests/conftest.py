import os
import pytest
import time
from faker import Faker
from subprocess import check_call

import nexuscli
import nexuscli.cli.util


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
        '<script.groovy>': None,
        '<script_name>': None,
        'create': False,
        'hosted': False,
        'list': False,
        'login': False,
        'maven2': True,
        'npm': False,
        'pypi': False,
        'raw': False,
        'repository': False,
        'delete': False,
        'rubygems': False,
        'run': False,
        'script': False,
        'yum': False
    }

    return args


@pytest.fixture(scope='session')
def nexus_client():
    return nexuscli.cli.util.get_client()


@pytest.helpers.register
def create_and_inspect(client, argv, expected_repo_name):
    nexuscli.cli.main(argv=list(filter(None, argv)))
    repositories = client.repositories.raw_list()

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
        # for _ in range(faker.random_int(1, 100)):
        for _ in range(2):
            relative_path = faker.file_path(
                # depth=faker.random_number(1, 10))[1:]
                depth=2)[1:]
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
    """Create an empty hosted raw repository"""
    repo_name = faker.pystr()
    command = 'nexus3 repository create hosted raw {}'.format(repo_name)
    check_call(command.split())
    return repo_name


@pytest.helpers.register
def get_ResponseMock():
    """Generate mock return value for request"""
    class ResponseMock:
        def __init__(self, status_code, reason):
            self.status_code = status_code
            self.reason = reason

    return ResponseMock


@pytest.fixture
def client_args(faker, tmpdir):
    """Parameters suitable for use with NexusClient()"""
    fixture = {
        'url': faker.url(),
        'user': faker.user_name(),
        'password': faker.password(),
        'config_path': tmpdir.join(faker.file_name()),
    }
    return fixture


@pytest.fixture
def nexus_raw_repo(nexus_mock_client, faker):
    repo_name = faker.uri_page()
    nexus_mock_client.repositories._repositories_json.append({
        'name': repo_name, 'format': 'raw'})

    return nexus_mock_client.repositories.get_by_name(repo_name)


@pytest.fixture
def nexus_yum_repo(nexus_mock_client, faker):
    repo_name = faker.uri_page()
    nexus_mock_client.repositories._repositories_json.append({
        'name': repo_name, 'format': 'yum'})

    return nexus_mock_client.repositories.get_by_name(repo_name)
