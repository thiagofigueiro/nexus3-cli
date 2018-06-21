import io
import json
import py
import requests
try:
    from urllib.parse import urljoin  # Python 3
except ImportError:
    from urlparse import urljoin      # Python 2

from . import exception


class NexusClient(object):
    # Relevant javadocs
    # Script API:
    # http://search.maven.org/remotecontent?filepath=org/sonatype/nexus/plugins/nexus-script-plugin/3.12.1-01/nexus-script-plugin-3.12.1-01-javadoc.jar
    # REST API doc:
    # https://help.sonatype.com/repomanager3/rest-and-integration-api
    CONFIG_PATH = '~/.nexus-cli'
    DEFAULT_URL = 'http://localhost:8081'
    DEFAULT_USER = 'admin'
    DEFAULT_PASS = 'admin123'

    def __init__(self, url=None, user=None, password=None, config=None):
        self.auth = None
        self.base_url = None
        self._api_version = 'v1'
        self.config = config or NexusClient.CONFIG_PATH

        self.set_config(
            user or NexusClient.DEFAULT_USER,
            password or NexusClient.DEFAULT_PASS,
            url or NexusClient.DEFAULT_URL)

    def set_config(self, user, password, base_url):
        self.auth = (user, password)
        self.base_url = base_url

    @property
    def rest_url(self):
        url = urljoin(self.base_url, '/service/rest/')
        return urljoin(url, self._api_version + '/')

    def write_config(self):
        nexus_config = py.path.local(self.config, expanduser=True)
        nexus_config.ensure()
        nexus_config.chmod(0o600)
        with io.open(nexus_config.strpath, mode='w+', encoding='utf-8') as fh:
            # If this looks dumb it's because it needs to work with Python 2
            fh.write(str(
                json.dumps({
                    'nexus_user': self.auth[0],
                    'nexus_pass': self.auth[1],
                    'nexus_url': self.base_url,
                }, ensure_ascii=False)
            ))

    def read_config(self):
        nexus_config = py.path.local(self.config, expanduser=True)
        try:
            with nexus_config.open(mode='r', encoding='utf-8') as fh:
                config = json.load(fh)
        except py.error.ENOENT:
            raise exception.NexusClientConfigurationNotFound

        self.set_config(
            config['nexus_user'], config['nexus_pass'], config['nexus_url'])

    def _request(self, method, endpoint, **kwargs):
        url = urljoin(self.rest_url, endpoint)
        response = requests.request(
            method=method, auth=self.auth, url=url, verify=False, **kwargs)

        if response.status_code == 401:
            raise exception.NexusClientInvalidCredentials(
                'Try running `nexus3 login`')

        return response

    def _get(self, endpoint):
        return self._request('get', endpoint)

    def _post(self, endpoint, **kwargs):
        return self._request('post', endpoint, **kwargs)

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
        resp = self._get('repositories')
        if resp.status_code == 200:
            return resp.json()
        else:
            raise exception.NexusClientAPIError(resp.content)
