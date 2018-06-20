# -*- coding: utf-8 -*-
"""Nexus 3 CLI

Usage:
  nexus3 --help, -h
  nexus3 login
  nexus3 repo create hosted maven <repo_name>
         [--blob=<store_name>] [--version=<v_policy>]
         [--layout=<l_policy>] [--strict-content]
         [--write=<w_policy>]
  nexus3 repo create hosted (npm|pypi|raw|rubygems) <repo_name>
         [--blob=<store_name>] [--write=<w_policy>] [--strict-content]
  nexus3 repo create hosted yum <repo_name>
         [--blob=<store_name>] [--write=<w_policy>]
         [--depth=<repo_depth>] [--strict-content]
  nexus3 repo create proxy maven <repo_name> <remote_url>
         [--blob=<store_name>] [--version=<v_policy>]
         [--layout=<l_policy>] [--strict-content]
  nexus3 repo create proxy (npm|pypi|raw|rubygems|yum)
          <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content]
  nexus3 repo list
  nexus3 repo rm <repo_name>
  nexus3 script create <script.json>
  nexus3 script list
  nexus3 script (rm|run) <script_name>

Options:
  -h --help             This screen
  --blob=<store_name>   Use this blob with new repository  [default: default]
  --depth=<repo_depth>  Depth (0-5) where repodata folder(s) exist [default: 0]
  --write=<w_policy>    Accepted: allow, allow_once, deny [default: allow_once]
  --layout=<l_policy>   Accepted: strict, permissive [default: strict]
  --version=<v_policy>  Accepted: release, snapshot, mixed [default: release]
  --strict-content      Enable strict content type validation

Commands:
  login         Test login and save credentials to ~/.nexus-cli
  repo create   Create a repository using the format and options provided
  repo list     List all repositories available on the server
  repo rm       Not implemented; please use Nexus Web UI to remove <repo_name>
  script create Create or update a script using the <script.json> file
  script list   List all scripts available on the server
  script rm     Remove existing <script_name>
  script run    Run the existing <script_name>
"""
import getpass
import io
import json
import py
import requests
import sys

from builtins import str  # unfuck Python 2's unicode
from docopt import docopt

try:
    from urllib.parse import urljoin  # Python 3
except ImportError:
    from urlparse import urljoin      # Python 2


class NexusClientConfigurationNotFound(Exception):
    pass


class NexusClient(object):
    # Relevant javadocs
    # Script API:
    # http://search.maven.org/remotecontent?filepath=org/sonatype/nexus/plugins/nexus-script-plugin/3.12.1-01/nexus-script-plugin-3.12.1-01-javadoc.jar
    # LayoutPolicy, VersionPolicy
    # http://search.maven.org/remotecontent?filepath=org/sonatype/nexus/plugins/nexus-repository-maven/3.12.1-01/nexus-repository-maven-3.12.1-01-javadoc.jar
    # WritePolicy
    # http://search.maven.org/remotecontent?filepath=org/sonatype/nexus/nexus-repository/3.0.2-02/nexus-repository-3.0.2-02-javadoc.jar
    # REST API doc:
    # https://help.sonatype.com/repomanager3/rest-and-integration-api
    CONFIG_PATH = '~/.nexus-cli'
    DEFAULT_URL = 'http://localhost:8081'
    DEFAULT_USER = 'admin'
    DEFAULT_PASS = 'admin123'

    POLICY_IMPORTS = {
        'layout': ['org.sonatype.nexus.repository.maven.LayoutPolicy'],
        'version': ['org.sonatype.nexus.repository.maven.VersionPolicy'],
        'write': ['org.sonatype.nexus.repository.storage.WritePolicy'],
    }

    POLICIES = {
        'layout': {
            'permissive': 'LayoutPolicy.PERMISSIVE',
            'strict': 'LayoutPolicy.STRICT',
        },
        'version': {
            'release': 'VersionPolicy.RELEASE',
            'snapshot': 'VersionPolicy.SNAPSHOT',
            'mixed': 'VersionPolicy.MIXED',
        },
        'write': {
            'allow': 'WritePolicy.ALLOW',
            'allow_once': 'WritePolicy.ALLOW_ONCE',
            'deny': 'WritePolicy.DENY',
        },
    }

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
            raise NexusClientConfigurationNotFound

        self.set_config(
            config['nexus_user'], config['nexus_pass'], config['nexus_url'])

    def _request(self, method, endpoint, **kwargs):
        url = urljoin(self.rest_url, endpoint)
        response = requests.request(
            method=method, auth=self.auth, url=url, verify=False, **kwargs)

        if response.status_code == 401:
            raise AttributeError('Invalid credentials')

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
            raise RuntimeError(resp.content)

        return resp.json()

    def script_create(self, script_content):
        resp = self._post('script', json=script_content)
        if resp.status_code != 204:
            raise RuntimeError(resp.content)

    def script_run(self, script_name):
        headers = {'content-type': 'text/plain'}
        endpoint = 'script/{}/run'.format(script_name)
        resp = self._post(endpoint, headers=headers, data='')
        if resp.status_code != 200:
            raise RuntimeError(resp.content)

    def script_delete(self, script_name):
        endpoint = 'script/{}'.format(script_name)
        resp = self._delete(endpoint)
        if resp.status_code != 204:
            raise RuntimeError(resp.reason)

    def repo_list(self):
        self._api_version = 'beta'
        resp = self._get('repositories')
        if resp.status_code == 200:
            return resp.json()
        else:
            raise RuntimeError(resp.content)


def _input(prompt, default=None):
    """
    :return: raw_input for Python 2.x and input for Python 3.x
    :rtype: function
    """
    if sys.version_info < (3, 0):
        real_input = raw_input  # noqa - Python2
    else:
        real_input = input

    value = real_input('{prompt} ({default}):'.format(**locals()))
    if value:
        return value
    else:
        return default


def do_login():
    nexus_url = _input('Nexus OSS URL', NexusClient.DEFAULT_URL)
    nexus_user = _input('Nexus admin username', NexusClient.DEFAULT_USER)
    nexus_pass = getpass.getpass(
        prompt='Nexus admin password ({}):'.format(
            NexusClient.DEFAULT_PASS))
    if not nexus_pass:
        nexus_pass = NexusClient.DEFAULT_PASS

    client = NexusClient(url=nexus_url, user=nexus_user, password=nexus_pass)
    client.write_config()

    sys.stderr.write('\nConfiguration saved to {}\n'.format(
        NexusClient.CONFIG_PATH))


def get_client():
    client = NexusClient()
    try:
        client.read_config()
        return client
    except NexusClientConfigurationNotFound:
        sys.stderr.write(
            'Configuration not found; please run nexus-cli.py login\n')
        sys.exit(1)


def cmd_script_do_list(nexus_client):
    json_response = nexus_client.script_list()

    sys.stderr.write('Name (type)\n')
    for script in json_response:
        sys.stdout.write('{script[name]} ({script[type]})\n'.format(
            script=script))


def cmd_script_do_create(nexus_client, script_path):
    script_content = json.load(open(script_path), strict=False)
    nexus_client.script_create(script_content)


def cmd_script(args):
    nexus_client = get_client()

    if args.get('list'):
        cmd_script_do_list(nexus_client)
    elif args.get('rm'):
        nexus_client.script_delete(args.get('<script_name>'))
    elif args.get('run'):
        nexus_client.script_run(args.get('<script_name>'))
    elif args.get('create'):
        cmd_script_do_create(nexus_client, args.get('<script.json>'))
    else:
        raise NotImplementedError


def cmd_repo_do_list(nexus_client):
    json_response = nexus_client.repo_list()

    output_format = '{0:40} {1:7} {2:7} {3}\n'
    sys.stderr.write(output_format.format('Name', 'Format', 'Type', 'URL'))
    sys.stderr.write(output_format.format('----', '------', '----', '---'))
    for repo in json_response:
        sys.stdout.write(output_format.format(
            repo['name'], repo['format'], repo['type'], repo['url']))


def script(script_name, imports, create_statement=None):
    script_ = {
        'type': 'groovy',
        'name': script_name,
        'content': '{imports}\n{create_statement}\n'.format(**locals()),
    }
    return script_, script_name


def script_imports(import_list):
    import_list = import_list or []
    imports = ''
    for import_ in import_list:
        imports += 'import {};\n'.format(import_)
    return imports


def script_common(parameters):
    script_name = 'create_{}'.format(parameters['name'])
    imports = script_imports(parameters.get('__imports', []))
    return script_name, imports


def script_hosted_maven(maven_parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{versionPolicy}, "
                        "{writePolicy}, "
                        "{layoutPolicy});".format(**maven_parameters))

    return script(
        *script_common(maven_parameters), create_statement=create_statement)


def script_proxy_maven(maven_parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{remoteUrl}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{versionPolicy}, "
                        "{layoutPolicy});".format(**maven_parameters))

    return script(
        *script_common(maven_parameters), create_statement=create_statement)


def script_hosted_yum(parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{writePolicy}, "
                        "{depth});".format(**parameters))

    return script(
        *script_common(parameters), create_statement=create_statement)


def script_proxy_yum(parameters):
    return script_proxy(parameters)


def script_hosted(parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{writePolicy});".format(**parameters))

    return script(
        *script_common(parameters), create_statement=create_statement)


def script_proxy(parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{remoteUrl}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation});".format(**parameters))

    return script(
        *script_common(parameters), create_statement=create_statement)


def nexus_policy(policy_name, user_option):
    if user_option == '__imports':
        return NexusClient.POLICY_IMPORTS[policy_name]

    policy = NexusClient.POLICIES[policy_name].get(user_option)
    if policy is None:
        raise AttributeError('Valid options for --{} are: {}'.format(
            policy_name, list(NexusClient.POLICIES[policy_name])))
    return policy


def args_to_repo_params_hosted_maven(args):
    #   Repository createMavenHosted(final String name,
    #                            final String blobStoreName,
    #                            final boolean strictContentTypeValidation,
    #                            final VersionPolicy versionPolicy,
    #                            final WritePolicy writePolicy,
    #                            final LayoutPolicy layoutPolicy);
    repo_params = args_to_repo_params_hosted(args)
    repo_params.update({
        'versionPolicy': nexus_policy('version', args['--version']),
        'layoutPolicy': nexus_policy('layout', args['--layout']),
        '__imports': [
            item for policy_name in ['version', 'write', 'layout']
            for item in nexus_policy(policy_name, '__imports')],
    })

    return repo_params


def args_to_repo_params_proxy_maven(args):
    # createMavenProxy(
    #     String name,
    #     String remoteUrl,
    #     String blobStoreName,
    #     boolean strictContentTypeValidation,
    #     org.sonatype.nexus.repository.maven.VersionPolicy versionPolicy,
    #     org.sonatype.nexus.repository.maven.LayoutPolicy layoutPolicy)

    # the unused 'write' import doesn't hurt and the extra writePolicy param
    # will be ignored as the format string for the statement doesn't use it
    repo_params = args_to_repo_params_hosted_maven(args)
    repo_params.update(args_to_repo_params_proxy(args))

    return repo_params


def args_to_repo_params_hosted_yum(args):
    # createYumHosted(
    #     String name,
    #     String blobStoreName,
    #     boolean strictContentTypeValidation,
    #     org.sonatype.nexus.repository.storage.WritePolicy writePolicy,
    #     int depth)
    repo_params = args_to_repo_params_hosted(args)
    repo_params.update({'depth': args['--depth']})

    return repo_params


def args_to_repo_params_proxy_yum(args):
    # createYumProxy(
    #     String name,
    #     String remoteUrl,
    #     String blobStoreName,
    #     boolean strictContentTypeValidation)
    return args_to_repo_params_proxy(args)


def args_to_repo_params(args):
    # Parameters common to createFormatHosted and createFormatProxy
    # create(Npm|PyPi|Raw|Rubygems)Hosted(
    #     String name,
    #     String blobStoreName,
    #     boolean strictContentTypeValidation,
    #     org.sonatype.nexus.repository.storage.WritePolicy writePolicy)
    repo_params = {
        'name': args['<repo_name>'],
        'blobStoreName': args['--blob'],
        'strictContentTypeValidation': str(args['--strict-content']).lower(),
    }

    return repo_params


def args_to_repo_params_hosted(args):
    # create(Npm|PyPi|Raw|Rubygems)Hosted(
    #     String name,
    #     String blobStoreName,
    #     boolean strictContentTypeValidation,
    #     org.sonatype.nexus.repository.storage.WritePolicy writePolicy)
    method_name = 'repository.create{}Hosted'.format(args_to_repo_format(args))
    repo_params = args_to_repo_params(args)
    repo_params.update({
        'writePolicy': nexus_policy('write', args['--write']),
        '__method': method_name,
        '__imports': nexus_policy('write', '__imports'),
    })

    return repo_params


def args_to_repo_params_proxy(args):
    # create(Npm|PyPi|Raw|Rubygems)Proxy(
    #     String name,
    #     String remoteUrl,
    #     String blobStoreName,
    #     boolean strictContentTypeValidation)
    method_name = 'repository.create{}Proxy'.format(args_to_repo_format(args))
    repo_params = args_to_repo_params(args)
    repo_params.update({
        'remoteUrl': args['<remote_url>'],
        '__method': method_name,
    })

    return repo_params


def script_method_name(repo_type, repo_format):
    method_name_tokens = ['script', repo_type]
    if repo_format is not None:
        method_name_tokens.append(repo_format)
    return '_'.join(method_name_tokens)


def cmd_repo_do_create(
        nexus_client, repo_params, repo_type='hosted', repo_format=None):
    script_method = globals()[script_method_name(repo_type, repo_format)]
    script_content, script_name = script_method(repo_params)
    nexus_client.script_create(script_content)
    nexus_client.script_run(script_name)
    nexus_client.script_delete(script_name)
    sys.stderr.write('Created repository: {}\n'.format(repo_params['name']))


def args_to_repo_format(args):
    accepted_formats = ['maven', 'npm', 'pypi', 'raw', 'rubygems', 'yum']
    # docopt guarantees only one is True
    for format_name in accepted_formats:
        if args.get(format_name) is True:
            if format_name == 'pypi':
                return 'PyPi'  # bloody bastards 🤬
            else:
                return format_name.title()
    # Just in case:
    raise AttributeError(
        'User arguments did not match a recognised format: {}'.format(
            accepted_formats))


def args_to_repo_type(args):
    accepted_types = ['hosted', 'proxy']
    # docopt guarantees only one is True
    for type_name in accepted_types:
        if args.get(type_name) is True:
            return type_name
    # Just in case:
    raise AttributeError(
        'User arguments did not match a recognised type: {}'.format(
            accepted_types))


def cmd_repo_create(nexus_client, args):
    repo_type = args_to_repo_type(args)
    repo_format = args_to_repo_format(args).lower()

    # these special snowflakes have their own groovy method signatures
    snowflake_repo_formats = ['maven', 'yum']
    if repo_format in snowflake_repo_formats:
        # ie: args_to_repo_params_maven, args_to_repo_params_yum
        method_name = 'args_to_repo_params_{repo_type}_{repo_format}'.format(
            **locals())
        args_to_repo_params_method = globals()[method_name]
    else:
        method_name = 'args_to_repo_params_{repo_type}'.format(**locals())
        args_to_repo_params_method = globals()[method_name]
        repo_format = None

    repo_params = args_to_repo_params_method(args)
    cmd_repo_do_create(nexus_client, repo_params,
                       repo_type=repo_type, repo_format=repo_format)


def cmd_repo(args):
    nexus_client = get_client()

    if args.get('list'):
        cmd_repo_do_list(nexus_client)
    elif args.get('create'):
        cmd_repo_create(nexus_client, args)
    else:
        raise NotImplementedError


def main(argv=None):
    arguments = docopt(__doc__, argv=argv)
    if arguments.get('login'):
        do_login()
        get_client().repo_list()
    elif arguments.get('script'):
        cmd_script(arguments)
    elif arguments.get('repo'):
        cmd_repo(arguments)
    else:
        raise NotImplementedError
