import pytest
from click.testing import CliRunner
from faker import Faker

from nexuscli import cli

_faker = Faker()


@pytest.helpers.register
def repo_name(basename, *args):
    name = basename
    for token in args:
        name += f'-{token}'
    return f'{name}-{_faker.pystr()}'


@pytest.fixture(scope='session')
def cli_runner():
    return CliRunner()


@pytest.fixture
def login_env(faker):
    yesno_bool = {'Yes': True, 'No': False}

    env = {
        f'{cli.ENV_VAR_PREFIX}_LOGIN_URL': faker.uri(),
        f'{cli.ENV_VAR_PREFIX}_LOGIN_USERNAME': faker.user_name(),
        f'{cli.ENV_VAR_PREFIX}_LOGIN_PASSWORD': faker.password(),
        f'{cli.ENV_VAR_PREFIX}_LOGIN_X509_VERIFY': faker.random_element(
            ['Yes', 'No']),
    }

    # e.g.: NEXUS3_LOGIN_X509_VERIFY -> x509_verify
    xargs = {'_'.join(k.split('_')[2:]).lower(): v for k, v in env.items()}
    xargs.update({'x509_verify': yesno_bool[xargs['x509_verify']]})

    return env, xargs


def _as_bool(flag:str):
    if flag.startswith('--no-'):
        return False
    return True


@pytest.fixture
def upload_args_factory(faker):
    def fixture(cmd, flatten, recurse):
        src = faker.file_path()
        dst = faker.file_path()

        args = f'{cmd} {src} {dst} {flatten} {recurse}'
        xargs = {
            'src': src,
            'dst': dst,
            'flatten': _as_bool(flatten),
            'recurse': _as_bool(recurse),
        }
        return args, xargs

    return fixture
