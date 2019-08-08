REMOTE_PATH_SEPARATOR = '/'


def ensure_known(target, value, known):
    """
    Validate whether the a target argument is known and supported. The
    ``target`` is only used to provide a friendlier message to the user.
    The given ``value`` is checked against ``known`` and ``supported``.

    Args:
        target (str): name of the target, as known to the end-user.
        value (str): value of the target key.
        known (list,tuple): known possible values for the target.

    Raises:
          :class:`ValueError`: if given value is not in ``known``.
    """
    if value not in known:
        raise ValueError(f'{target}={value} must be one of {known}')
