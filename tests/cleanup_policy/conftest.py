import json
import pytest

from nexuscli.cleanup_policy import CleanupPolicyCollection


@pytest.fixture
def cleanup_policy_collection(mocker):
    """An instance with a magic mock as its client"""
    fixture = CleanupPolicyCollection(client=mocker.Mock())
    return fixture


@pytest.fixture
def cleanup_policy_configuration(faker):
    """Raw policy configuration dict"""
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


@pytest.fixture
def create_response():
    """Creates a Nexus script run response based on the policy configuration"""
    def fixture(configuration):
        return {'result': json.dumps(configuration)}
    return fixture
