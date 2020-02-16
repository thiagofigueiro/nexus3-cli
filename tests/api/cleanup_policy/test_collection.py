import json
import pytest

from nexuscli import exception
from nexuscli.api.cleanup_policy import CleanupPolicy


def test_get_by_name(cleanup_policy_collection, cleanup_policy_configuration):
    """
    It returns an instance of CleanupPolicy with the configuration given by the
    nexus script
    """
    response = {'result': json.dumps(cleanup_policy_configuration)}
    x_name = cleanup_policy_configuration['name']
    cleanup_policy_collection._client.scripts.run.return_value = response

    cleanup_policy = cleanup_policy_collection.get_by_name(x_name)

    assert cleanup_policy.configuration == cleanup_policy_configuration
    assert isinstance(cleanup_policy, CleanupPolicy)


def test_get_by_name_exception(cleanup_policy_collection, faker):
    """ It raises the documented exception when the policy name isn't found"""
    xname = faker.pystr()
    cleanup_policy_collection._client.scripts.run.side_effect = \
        exception.NexusClientAPIError(xname)

    with pytest.raises(exception.NexusClientInvalidCleanupPolicy):
        cleanup_policy_collection.get_by_name(xname)


def test_create_or_update(
        cleanup_policy_collection, cleanup_policy_configuration,
        create_response):
    """"""
    cleanup_policy = CleanupPolicy(None, **cleanup_policy_configuration)
    response = create_response(cleanup_policy_configuration)
    cleanup_policy_collection._client.scripts.run.return_value = response

    cleanup_policy_collection.create_or_update(cleanup_policy)

    cleanup_policy_collection._client.scripts.run.assert_called_once()
