import pytest

from nexuscli.cleanup_policy import CleanupPolicyCollection


@pytest.fixture
def cleanup_policy_collection(mocker):
    fixture = CleanupPolicyCollection(client=mocker.Mock())
    return fixture


@pytest.fixture
def cleanup_policy_configuration(faker):
    fixture = {
        'name': faker.pystr(),
        'format': faker.word(),
        'mode': 'delete',
        'criteria': {
            'lastDownloaded': faker.random_number() + 1,
            'lastBlobUpdated': faker.random_number() + 1,
        }
    }
    return fixture
