
def _to_int(attribute_dict, key):
    if attribute_dict.get(key) is None:
        return False
    attribute_dict[key] = int(attribute_dict[key])
    return True


def policy_criteria(raw_policy):
    """
    Ensures the policy criteria fields are valid. Will transform strings to the
    correct type where needed.

    :param raw_policy: as returned by the
        :py:class:`~nexuscli.api.cleanup_policy.model.CleanupPolicy`
        :py:attr:`~nexuscli.api.cleanup_policy.model.CleanupPolicy.configuration`
    :raises ValueError: when a criterion has an invalid value.
    """
    criteria = raw_policy.get('criteria')
    if criteria is None:
        return

    for key in ['lastDownloaded', 'lastBlobUpdated']:
        if _to_int(criteria, key):
            if criteria[key] < 1:
                raise ValueError(f'{key} in criteria must be greater than 0')


def policy_name(raw_policy):
    """
    Ensure the policy has a name

    :raises ValueError: when the name attribute is missing.
    """
    if not raw_policy.get('name'):
        raise ValueError('required attribute `name` is missing or empty')
