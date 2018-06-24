# -*- coding: utf-8 -*-
"""Nexus 3 CLI

Usage:
  nexus3 --help, -h
  nexus3 login
  nexus3 (list|ls) <repository_path>
  nexus3 (upload|up) <from_src> <to_repository>
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
  list          List all files within a path in the repository
  repo create   Create a repository using the format and options provided
  repo list     List all repositories available on the server
  repo rm       Not implemented; please use Nexus Web UI to remove <repo_name>
  script create Create or update a script using the <script.json> file
  script list   List all scripts available on the server
  script rm     Remove existing <script_name>
  script run    Run the existing <script_name>
"""
import getpass
import inflect
import json
import sys
import types

from builtins import str  # unfuck Python 2's unicode
from docopt import docopt

from nexuscli import nexus_repository
from nexuscli.exception import NexusClientConfigurationNotFound
from nexuscli.nexus_client import NexusClient
from nexuscli.nexus_script import script_method_object

PLURAL = inflect.engine().plural


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


def nexus_policy(policy_name, user_option):
    if user_option == '__imports':
        return nexus_repository.POLICY_IMPORTS[policy_name]

    policy = nexus_repository.POLICIES[policy_name].get(user_option)
    if policy is None:
        raise AttributeError('Valid options for --{} are: {}'.format(
            policy_name, list(nexus_repository.POLICIES[policy_name])))
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


def cmd_repo_do_create(
        nexus_client, repo_params, repo_type='hosted', repo_format=None):
    script_method = script_method_object(repo_type, repo_format)
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


def cmd_list(args):
    """
    Performs the `rekt ar search` command using the configured artefact
    repository service.
    """
    nexus_client = get_client()
    repository_path = args['<repository_path>']
    artefact_list = nexus_client.list(repository_path)

    # FIXME: is types.GeneratorType still used?
    if isinstance(artefact_list, (list, types.GeneratorType)):
        for artefact in iter(artefact_list):
            sys.stdout.write('{}\n'.format(artefact))
        return 0
    else:
        return 1


def _cmd_up_down_errors(count, action):
    """Print and exit with error if upload/download didn't succeed"""
    if count == 0:
        # FIXME: inflex the action verb to past participle
        sys.stderr.write('WARNING: no files were {}\'ed.'.format(action))
        sys.exit(1)

    if count == -1:
        sys.stderr.write('ERROR during {} operation.'.format(action))
        sys.exit(2)


def cmd_upload(args):
    """
    Performs the `rekt ar upload` command using the configured artefact
    repository service.
    """
    nexus_client = get_client()
    source = args['<from_src>']
    destination = args['<to_repository>']

    sys.stderr.write(
        'Uploading {source} to {destination}\n'.format(**locals()))

    upload_count = nexus_client.upload(source, destination)

    _cmd_up_down_errors(upload_count, 'upload')

    file = PLURAL('file', upload_count)
    sys.stderr.write(
        'Uploaded {upload_count} {file} to {destination}\n'.format(**locals()))
    return 0


def main(argv=None):
    arguments = docopt(__doc__, argv=argv)
    if arguments.get('login'):
        do_login()
        NexusClient()
    elif arguments.get('script'):
        cmd_script(arguments)
    elif arguments.get('repo'):
        cmd_repo(arguments)
    elif arguments.get('list') or arguments.get('ls'):
        cmd_list(arguments)
    elif arguments.get('upload') or arguments.get('up'):
        cmd_upload(arguments)
    else:
        raise NotImplementedError
