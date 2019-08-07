import pytest
from faker import Faker

faker = Faker()


@pytest.helpers.register
def repo_name(basename, *args):
    name = basename
    for token in args:
        name += f'-{token}'
    return f'{name}-{faker.random_number()}'
