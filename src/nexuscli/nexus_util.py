# -*- coding: utf-8 -*-
import hashlib
import mmap
import os
import pkg_resources


def _resource_filename(resource_name):
    """wrapper for pkg_resources.resource_filename"""
    return pkg_resources.resource_filename('nexuscli', resource_name)


def groovy_script(script_name):
    """
    Returns the content for a groovy script located in the package installation
    path under script/groovy.

    E.g.: groovy_script('foo') returns the content for the file at
    ``.../site-packages/nexuscli/script/groovy/foo.groovy``.

    :param script_name: file name of the groovy script; ``.groovy`` is appended
        to this parameter to form the file name.
    :return: content for the groovy script
    :rtype: str
    """
    script_path = os.path.join(
        'api', 'script', 'groovy', f'{script_name}.groovy')
    script_path = _resource_filename(script_path)
    return open(script_path).read()


def validate_strings(*args):
    """
    Checks that all given arguments have a string type (e.g. str, basestring,
    unicode etc)

    Args:
        *args: values to be validated.

    Returns:
        bool: True if all arguments are of a string type. False otherwise.
    """
    for arg in args:
        if not isinstance(arg, str):
            return False

    return True


def filtered_list_gen(raw_response, term=None, partial_match=True):
    """
    Iterates over items yielded by raw_response_gen, validating that:
        1. the `path` dict key is a str
        2. the `path` value starts with starts_with (if provided)

    >>> r = [{
    >>>     'checksum': {
    >>>         'md5': 'd94b865aa7620c46ef8faef7059a311c',
    >>>         'sha1': '2186934d880cf24dd9ecc578335e290026695522',
    >>>         'sha256': 'b7bb3424a6a6(...)4113bc38fd7807528481a8ffe3cf',
    >>>         'sha512': 'e7806f3caa3e(...)3caeb9bbc54bbde286c07f837fdc'
    >>>     },
    >>>     'downloadUrl': 'http://nexus/repository/repo_name/a/file.ext',
    >>>     'format': 'yum',
    >>>     'id': 'Y2xvdWRlcmEtbWFuYWdlcj(...)mRiNWU0YjllZWQzMg',
    >>>     'path': 'a/fake.rpm',
    >>>     'repository': 'cloudera-manager'}]
    >>>
    >>> for i in filtered_list_gen(r, starts_with='a/fake.rpm')
    >>>     print(i['path'])
    a/fake.rpm
    >>> for i in filtered_list_gen(r, starts_with='b')
    >>>     print(i['path'])
    # (nothing printed)

    Args:
        raw_response (iterable): an iterable that yields one element of a nexus
            search response at a time, such as the one returned by
            _paginate_get().
        term (str): if defined, only items with an attribute `path` that starts
            with the given parameter are returned.
        partial_match (bool): if True, include items whose artefact path starts
            with the given term.

    Yields:
        dict: items that matched the filter.
    """
    def is_match(path_, term_):
        if partial_match:
            return path_.startswith(term_)
        else:
            return path_ == term_

    for artefact in raw_response:
        artefact_path = artefact.get('path')
        if artefact_path is None:
            continue
        if not validate_strings(artefact_path):
            continue
        if term is None or is_match(artefact_path, term):
            yield artefact


def calculate_hash(hash_name, file_path_or_handle):
    """
    Calculate a hash for the given file.

    :param hash_name: name of the hash algorithm in hashlib
    :type hash_name: str
    :param file_path_or_handle: source file name (:py:obj:`str`) or file
        handle (:py:obj:`file-like`) for the hash algorithm.
    :type file_path_or_handle: str
    :return: the calculated hash
    :rtype: str
    """
    def _hash(_fd):
        h = hashlib.new(hash_name)
        stat = os.fstat(_fd.fileno())
        if stat.st_size > 0:  # can't map a zero-length file
            m = mmap.mmap(_fd.fileno(),
                          stat.st_size, access=mmap.ACCESS_READ)
            h.update(m)
        return h.hexdigest()

    if hasattr(file_path_or_handle, 'read'):
        return _hash(file_path_or_handle)
    else:
        with open(file_path_or_handle, 'rb') as fd:
            return _hash(fd)


def has_same_hash(artefact, filepath):
    """
    Checks if a Nexus artefact has the same hash as a local filepath.

    :param artefact:  as returned by
        :py:meth:`~nexuscli.nexus_client.NexusClient.list_raw`
    :type artefact: dict
    :param filepath: local file path
    :return: True if artefact and filepath have the same hash.
    :rtype: bool
    """
    for hash_name in ['sha1', 'md5']:
        remote_hash = artefact.get('checksum', {}).get(hash_name)
        if remote_hash is None:
            continue

        local_hash = calculate_hash(hash_name, filepath)
        return local_hash == remote_hash

    return False
