import io
import json
import os.path
import py
import requests
try:
    from urllib.parse import urljoin  # Python 3
except ImportError:
    from urlparse import urljoin      # Python 2

from . import exception, nexus_util

SUPPORTED_FORMATS_FOR_UPLOAD = ['raw', 'yum']


class NexusClient(object):
    """
    Relevant javadocs
    Script API:
    http://search.maven.org/remotecontent?filepath=org/sonatype/nexus/plugins/nexus-script-plugin/3.12.1-01/nexus-script-plugin-3.12.1-01-javadoc.jar
    REST API doc:
    https://help.sonatype.com/repomanager3/rest-and-integration-api

    Args:
        url (str): URL to Nexus 3 OSS service.
        user (str): login for Nexus service at given url.
        password (str): password for given login.
        config_path (str): local file containing configuration above in JSON
            format as ``nexus_url``, ``nexus_user`` and ``nexus_pass``.

    Attributes:
        base_url (str): as per url argument.
        config_path (str): as per arguments.
        repositories (list): list of repositories on Nexus service. See
            :py:meth:`refresh_repositories` for format.
    """
    CONFIG_PATH = '~/.nexus-cli'
    DEFAULT_URL = 'http://localhost:8081'
    DEFAULT_USER = 'admin'
    DEFAULT_PASS = 'admin123'

    def __init__(self, url=None, user=None, password=None, config_path=None):
        self.base_url = None
        self.config_path = config_path or NexusClient.CONFIG_PATH
        self.repositories = None
        self._auth = None
        self._api_version = 'v1'
        self._local_sep = os.path.sep
        self._remote_sep = '/'

        self.set_config(
            user or NexusClient.DEFAULT_USER,
            password or NexusClient.DEFAULT_PASS,
            url or NexusClient.DEFAULT_URL)
        self.refresh_repositories()

    def set_config(self, user, password, base_url):
        self._auth = (user, password)
        self.base_url = base_url

    @property
    def rest_url(self):
        url = urljoin(self.base_url, '/service/rest/')
        return urljoin(url, self._api_version + '/')

    def write_config(self):
        nexus_config = py.path.local(self.config_path, expanduser=True)
        nexus_config.ensure()
        nexus_config.chmod(0o600)
        with io.open(nexus_config.strpath, mode='w+', encoding='utf-8') as fh:
            # If this looks dumb it's because it needs to work with Python 2
            fh.write(str(
                json.dumps({
                    'nexus_user': self._auth[0],
                    'nexus_pass': self._auth[1],
                    'nexus_url': self.base_url,
                }, ensure_ascii=False)
            ))

    def read_config(self):
        nexus_config = py.path.local(self.config_path, expanduser=True)
        try:
            with nexus_config.open(mode='r', encoding='utf-8') as fh:
                config = json.load(fh)
        except py.error.ENOENT:
            raise exception.NexusClientConfigurationNotFound

        self.set_config(
            config['nexus_user'], config['nexus_pass'], config['nexus_url'])

    def _request(self, method, endpoint, **kwargs):
        """
        Performs a request to the Nexus service URL.

        :param method: one of ``get``, ``put``, ``post``, ``delete``.
        :param endpoint: URI path to be appended to the service URL.
        :param kwargs: if ``service_url`` is not provided,
            :py:property:`self.rest_url` is used by default. All other kwargs
            are passed-through to ``requests.method``.
        :return: requests response object
        """
        try:
            service_url = kwargs.pop('service_url')
        except KeyError:
            service_url = self.rest_url

        url = urljoin(service_url, endpoint)
        response = requests.request(
            method=method, auth=self._auth, url=url, verify=False, **kwargs)

        if response.status_code == 401:
            raise exception.NexusClientInvalidCredentials(
                'Try running `nexus3 login`')

        return response

    def _get(self, endpoint):
        return self._request('get', endpoint)

    def _get_paginated(self, endpoint, **request_kwargs):
        """
        Performs a GET request using the given args and kwargs. If the response
        is paginated, the method will repeat the request, manipulating the
        `params` keyword argument each time in order to receive all pages of
        the response.

        Items in the responses are sent in "batches": when all elements of a
        response have been yielded, a new request is made and the process
        repeated.

        :param args: passed verbatim to the _request() method.
        :param request_kwargs: passed verbatim to the _request() method, except
            for the argument needed to paginate requests.
        :return: a generator that yields on response item at a time.
        """
        response = self._request('get', endpoint, **request_kwargs)
        if response.status_code == 404:
            raise exception.NexusClientAPIError(response.reason)

        content = response.json()
        while True:
            for item in content.get('items'):
                yield item

            continuation_token = content.get('continuationToken')
            if continuation_token is None:
                break

            request_kwargs['params'].update(
                {'continuationToken': continuation_token})
            response = self._request('get', endpoint, **request_kwargs)
            content = response.json()

    def _post(self, endpoint, **kwargs):
        return self._request('post', endpoint, **kwargs)

    def _put(self, endpoint, **kwargs):
        return self._request('put', endpoint, **kwargs)

    def _delete(self, endpoint, **kwargs):
        return self._request('delete', endpoint, **kwargs)

    def script_list(self):
        resp = self._get('script')
        if resp.status_code != 200:
            raise exception.NexusClientAPIError(resp.content)

        return resp.json()

    def script_create(self, script_content):
        resp = self._post('script', json=script_content)
        if resp.status_code != 204:
            raise exception.NexusClientAPIError(resp.content)

    def script_run(self, script_name):
        headers = {'content-type': 'text/plain'}
        endpoint = 'script/{}/run'.format(script_name)
        resp = self._post(endpoint, headers=headers, data='')
        if resp.status_code != 200:
            raise exception.NexusClientAPIError(resp.content)

    def script_delete(self, script_name):
        endpoint = 'script/{}'.format(script_name)
        resp = self._delete(endpoint)
        if resp.status_code != 204:
            raise exception.NexusClientAPIError(resp.reason)

    def repo_list(self):
        self._api_version = 'beta'
        response = self._get('repositories')
        if response.status_code == 200:
            return response.json()
        else:
            raise exception.NexusClientAPIError(response.content)

    def list(self, repository_path):
        """
        List all the artefacts, recursively, in a given repository_path.

        :param repository_path: location on the repository service.
        :param kwargs: implementation-specific arguments.
        :return: list of artefacts
        :rtype: list
        """
        for artefact in self.list_raw(repository_path):
            yield artefact.get('path')

    def _list_raw_search(self, repository_name, path_filter, partial_match):
        # TODO: use `group` attribute in raw repositories to speed-up queries
        query = {
            'repository': repository_name,
        }
        self._api_version = 'beta'
        raw_response = self._get_paginated('search/assets', params=query)

        return nexus_util.filtered_list_gen(
            raw_response, term=path_filter, partial_match=partial_match)

    def list_raw(self, repository_path):
        """
        As per list but returns a generator of raw Nexus artefact objects
        """
        repo, directory, filename = self.split_component_path(repository_path)
        path_filter = ''  # matches everything
        partial_match = True

        if directory is not None:
            path_filter = directory
            # Not all repos require a directory as part of the artefact path.
            if not (path_filter == '' or
                    path_filter.endswith(self._remote_sep)):
                path_filter += self._remote_sep

        if filename is not None:
            partial_match = False
            # The artefact path is always relative to the given repo.
            path_filter += filename

        list_gen = self._list_raw_search(repo, path_filter, partial_match)

        for artefact in list_gen:
            yield artefact

    def split_component_path(self, component_path):
        """
        A Nexus path for a raw directory must have this format:

        repository_name/directory[(/subdir1)...][/|filename]

        A path ending in / means it represents a directory; otherwise it
        represents a filename.

            >>> dst0 = 'myrepo0/dir/'
            >>> dst1 = 'myrepo1/dir/subdir/'
            >>> dst2 = 'myrepo2/dir/subdir/file'
            >>> dst3 = 'myrepo3/dir/subdir/etc/file.ext'
            >>> split_component_path(dst0)
            >>> ('myrepo0', 'dir', None)
            >>> split_component_path(dst1)
            >>> ('myrepo1', 'dir/subdir', None)
            >>> split_component_path(dst2)
            >>> ('myrepo2', 'dir/subdir', 'file')
            >>> split_component_path(dst3)
            >>> ('myrepo3', 'dir/subdir/etc', 'file.ext')

        :param component_path: the Nexus component path, as described above.
        :type component_path: str
        :return: tuple of (repository_name, directory, filename). If the given
            component_path doesn't represent a file, filename is set to None.
        :rtype: tuple
        """
        filename = None
        path_fragments = component_path.split(self._remote_sep)
        try:
            repository = path_fragments.pop(0)
            # no cheating!
            if not repository or repository == '.':
                raise IndexError
        except IndexError:
            raise exception.NexusClientInvalidRepositoryPath(
                'The given path does not contain a repository: {}'.format(
                    component_path))

        try:
            if not component_path.endswith(self._remote_sep):
                filename = path_fragments.pop()
                if not filename or filename == '.':
                    raise IndexError
        except IndexError:
            return repository, None, None

        directory = self._remote_sep.join(path_fragments)
        # for consistency
        if directory.endswith(self._remote_sep):
            directory = directory[:-1]
        # nice try, user but no cigar
        if not directory or directory == '.':
            directory = None

        return repository, directory, filename

    def refresh_repositories(self):
        """
        Refresh local list of repositories with latest from service.

        >>> [
        >>>     {
        >>>         'format': 'raw',
        >>>         'name': 'myraw',
        >>>         'type': 'hosted',
        >>>         'url': 'http://localhost:8081/repository/myraw'
        >>>     },
        >>>     # (...)
        >>> ]
        """
        self._api_version = 'beta'
        response = self._get('repositories')
        if response.status_code != 200:
            raise exception.NexusClientAPIError(response.content)

        self.repositories = response.json()
        self._api_version = 'v1'

    def get_repository_by_name(self, name):
        """ Search self.repositories for the entry named `name`"""
        for r in self.repositories:
            if r['name'] == name:
                return r

        raise IndexError

    def _upload_file_raw(self, src_file, dst_repo, dst_dir, dst_file):
        """Process upload_file() for raw repositories"""
        if dst_dir is None or dst_dir.startswith(self._remote_sep):
            raise exception.NexusClientInvalidRepositoryPath(
                'Destination path does not contain a directory, which is '
                'required by raw repositories')

        params = {'repository': dst_repo}
        files = {'raw.asset1': open(src_file, 'rb').read()}
        data = {
            'raw.directory': dst_dir,
            'raw.asset1.filename': dst_file,
        }

        self._api_version = 'beta'
        response = self._post(
            'components', files=files, data=data, params=params)
        if response.status_code != 204:
            raise exception.NexusClientAPIError(
                'Uploading to {dst_repo}. '
                'Reason: {response.reason}'.format(**locals()))

    def _upload_file_yum(self, src_file, dst_repo, dst_dir, dst_file):
        """Process upload_file() for yum repositories"""
        dst_dir = dst_dir or self._remote_sep
        repository_path = self._remote_sep.join(
            ['repository', dst_repo, dst_dir, dst_file])

        with open(src_file, 'rb') as fh:
            response = self._put(
                repository_path, data=fh, service_url=self.base_url)

        print('HELLO', response.__dict__)
        if response.status_code != 200:
            raise exception.NexusClientAPIError(
                'Uploading to {repository_path}. '
                'Reason: {response.reason}'.format(**locals()))

    def upload_file(self, src_file, dst_repo, dst_dir, dst_file=None):
        """
        Uploads a singe file to a Nexus repository under the directory and
        file name specified. If the destination file name isn't given, the
        source file name is used.

        :param src_file: path to the local file to be uploaded.
        :param dst_repo: name of the Nexus repository.
        :param dst_dir: directory under dst_repo to place file in.
        :param dst_file: destination file name.
        """
        try:
            repository = self.get_repository_by_name(dst_repo)
        except IndexError:
            raise exception.NexusClientInvalidRepository(dst_repo)

        # TODO: support all repository formats
        repo_format = repository['format']
        if repo_format not in SUPPORTED_FORMATS_FOR_UPLOAD:
            raise NotImplementedError(
                'Upload to {} repository not supported'.format(repo_format))

        if dst_file is None:
            dst_file = os.path.basename(src_file)

        _upload = getattr(self, '_upload_file_' + repo_format)
        _upload(src_file, dst_repo, dst_dir, dst_file)

    def _upload_dir_or_file(self, file_or_dir, dst_repo, dst_dir, dst_file):
        """
        Helper for self.upload() to call the correct upload method according to
        the source given by the user.

        :param file_or_dir: location or file or directory to be uploaded.
        :param dst_repo: destination repository in Nexus.
        :param dst_dir: destination directory in dst_repo.
        :param dst_file: destination file name.
        :return: number of files uploaded.
        """
        if os.path.isdir(file_or_dir):
            if dst_file is None:
                raise NotImplementedError('Source must be a file')
            else:
                raise exception.NexusClientInvalidRepositoryPath(
                    'Not allowed to upload a directory to a file')

        self.upload_file(file_or_dir, dst_repo, dst_dir, dst_file)
        return 1

    def upload(self, source, destination):
        """
        Process an upload. The source must be either a local file name or
        directory. The flatten and recurse class attributes are honoured for
        directory uploads.

        The destination must be a valid Nexus 3 repository path, including the
        repository name as the first component of the path.

        :param source: location of file or directory to be uploaded.
        :param destination: destination path in Nexus, including repository
            name and, if required, directory name (e.g. raw repos require a
            directory).
        :return: number of files uploaded.
        """
        repo, directory, filename = self.split_component_path(destination)
        upload_count = self._upload_dir_or_file(
            source, repo, directory, filename)

        return upload_count
