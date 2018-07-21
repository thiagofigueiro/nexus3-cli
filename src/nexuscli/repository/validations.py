from nexuscli.nexus_util import validate_strings

try:
    from urllib.parse import urlparse  # Python 3
except ImportError:
    from urlparse import urlparse      # Python 2


# TODO: remove when all known formats/types are supported
KNOWN_TYPES = ['group', 'hosted', 'proxy']
KNOWN_FORMATS = [
    'bower', 'docker', 'gitlfs', 'maven', 'npm', 'nuget', 'pypi', 'raw',
    'rubygems', 'yum']
SUPPORTED_FORMATS = [
    'bower', 'maven', 'npm', 'nuget', 'pypi', 'raw', 'rubygems', 'yum']
SUPPORTED_TYPES = ['hosted', 'proxy']
LAYOUT_POLICIES = ['PERMISSIVE', 'STRICT']
VERSION_POLICIES = ['RELEASE', 'SNAPSHOT', 'MIXED']
WRITE_POLICIES = ['ALLOW', 'ALLOW_ONCE', 'DENY']


def is_target_supported(target, value, known, supported):
    """
    Validate whether the a target argument is known and supported. The
    ``target`` is only used to provide a friendlier message to the user.
    The given ``value`` is checked against ``known`` and ``supported``.

    Args:
        target (str): name of the target, as known to the end-user.
        value (str): value of the target key.
        known (list): known possible values for the target.
        supported (list): values for the target supported by us.

    Raises:
          :class:`ValueError`: if given value is not in ``known``.
          :class:`NotImplementedError`: if given value is not in ``supported``.
    """
    if value not in known:
        raise ValueError(
            '{target}={value} must be one of {known}'.format(
                **locals()))

    if value not in supported:
        raise NotImplementedError(
            '{target}={value}; supported {target}s: {supported}'.format(
                **locals()))


def _upcase_values(raw_repo, targets=[]):
    for key in targets:
        value = raw_repo.get(key)
        if value is not None:
            raw_repo[key] = value.upper()


def upcase_policy_args(args):
    """
    Forces upper-case on the value of the ``layout_policy``, ``write_policy``
    and ``version_policy`` keys of a kwargs dict.

    :param args: kwargs given to caller
    :type args: dict
    :return: a copy of the original dict with the updated values.
    :rtype: dict
    """
    raw = dict(args)
    _upcase_values(raw, ['layout_policy', 'write_policy', 'version_policy'])
    return raw


def repository_args(repo_type, **kwargs):
    """
    Validate that the combination of arguments for a
    :class:`nexuscli.repository.model.Repository` is valid.

    Raises:
        :class:`ValueError`
            If the value of a given argument is invalid or unsupported, or if
            unrecognised keyword arguments are given.
        :class:`TypeError`
            If the type of a given argument has the wrong object type.
        :class:`NotImplementedError`
            If the combination of arguments isn't yet supported.

    :param repo_type: as given to
        :py:meth:`nexuscli.nexus_repository.Repository.create()
    :param kwargs: as given to
        :py:meth:`nexuscli.nexus_repository.Repository.create()
    """
    if not validate_strings(repo_type):
        raise TypeError('repo_type ({}) must be of string type'.format(
            type(repo_type)))
    is_target_supported('repo_type', repo_type, KNOWN_TYPES, SUPPORTED_TYPES)

    try:
        remaining_args = _check_common_args(**kwargs)
        remaining_args = _check_type_args(repo_type, **remaining_args)
    except KeyError as e:
        raise KeyError('Missing required keyword argument: {}'.format(e))

    ignore_extra = remaining_args.pop('ignore_extra_kwargs', False)
    if remaining_args and not ignore_extra:
        raise ValueError('Unrecognised keyword arguments: {}'.format(
            remaining_args.keys()))


def _check_common_args(**kwargs):
    name = kwargs.pop('name')
    format_ = kwargs.pop('format')
    if not validate_strings(name, format_):
        raise TypeError(
            'name ({0}) and format ({1}) must all be of string type'.format(
                *map(type, [name, format_])))
    is_target_supported('format', format_, KNOWN_FORMATS, SUPPORTED_FORMATS)

    blob_store_name = kwargs.pop('blob_store_name')
    # TODO: validate that blob_store_name exists on server
    assert blob_store_name

    strict_content_type_v = kwargs.pop('strict_content_type_validation')
    if not isinstance(strict_content_type_v, bool):
        raise TypeError(
            'strict_content_type_validation ({}) must be bool'.format(
                type(strict_content_type_v)))

    remaining_args = _check_format_args(format_, **kwargs)
    return remaining_args


def _check_format_args(repo_format, **kwargs):
    try:
        check_specific = globals()['_check_format_args_' + repo_format]
    except KeyError:
        # nothing specific to check on this repository format
        return kwargs

    return check_specific(**kwargs)


def _check_format_args_maven(**kwargs):
    version_policy = kwargs.pop('version_policy')
    layout_policy = kwargs.pop('layout_policy')
    is_target_supported(
        'version_policy', version_policy, VERSION_POLICIES, VERSION_POLICIES)
    is_target_supported(
        'layout_policy', layout_policy, LAYOUT_POLICIES, LAYOUT_POLICIES)

    return kwargs


def _check_format_args_yum(**kwargs):
    depth = kwargs.pop('depth')
    if depth < 0 or depth > 5:
        raise ValueError('depth={}; must be between 0-5'.format(depth))

    return kwargs


def _check_type_args(repo_type, **kwargs):
    try:
        check_specific = globals()['_check_type_args_' + repo_type]
    except KeyError:
        # nothing specific to check on this repository format
        return kwargs
    return check_specific(**kwargs)


def _check_type_args_hosted(**kwargs):
    write_policy = kwargs.pop('write_policy')
    is_target_supported(
        'write_policy', write_policy, WRITE_POLICIES, WRITE_POLICIES)

    return kwargs


def _check_type_args_proxy(**kwargs):
    remote_url = kwargs.pop('remote_url')
    parsed_url = urlparse(remote_url)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise ValueError('remote_url={} is not a valid URL'.format(remote_url))

    return kwargs
