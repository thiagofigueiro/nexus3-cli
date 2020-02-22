import json
import pytest

from nexuscli.api.cleanup_policy import CleanupPolicyCollection


@pytest.fixture
def cleanup_policy_collection(mocker, nexus_mock_client):
    """An instance with a magic mock as its client"""
    nexus_mock_client._scripts = mocker.Mock()
    fixture = CleanupPolicyCollection(client=nexus_mock_client)
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
