import pytest

from nexuscli.cleanup_policy import validations


@pytest.mark.parametrize('method_name, broken_configuration', [
    ('policy_criteria', {'criteria': {'lastDownloaded': 0}}),
    ('policy_criteria', {'criteria': {'lastBlobUpdated': 0}}),
    ('policy_name', {'name': None}),
    ('policy_name', {'name': ''}),
])
def test_validation_exception(
        method_name, broken_configuration, cleanup_policy_configuration):
    """It raises ValueError when a broken configuration is given"""
    cleanup_policy_configuration.update(broken_configuration)

    with pytest.raises(ValueError):
        getattr(validations, method_name)(cleanup_policy_configuration)
