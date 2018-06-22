# -*- coding: utf-8 -*-


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

    :param raw_response: an iterable that yields one element of a nexus
        search response at a time, such as the one returned by
        _paginate_get().
    :type raw_response: iterable
    :param term: if defined, only items with an attribute `path`
        that starts with the given parameter are returned.
    :param partial_match: if True, include items whose artefact path starts
        with the given term.
    :return: a generator that yields items that matched the filter.
    :rtype: iterable
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
        if not isinstance(artefact_path, str):
            continue
        if term is None or is_match(artefact_path, term):
            yield artefact
