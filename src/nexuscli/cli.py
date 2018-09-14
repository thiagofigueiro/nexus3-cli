# -*- coding: utf-8 -*-
"""Nexus 3 CLI

Usage:
  nexus3 --help, -h
  nexus3 login
  nexus3 (list|ls) <repository_path>
  nexus3 (upload|up) <from_src> <to_repository> [--flatten] [--norecurse]
  nexus3 (download|dl) <from_repository> <to_dst> [--flatten] [--nocache]
  nexus3 (delete|del) <repository_path>
  nexus3 repo create hosted maven <repo_name>
         [--blob=<store_name>] [--version=<v_policy>]
         [--layout=<l_policy>] [--strict-content]
         [--write=<w_policy>]
  nexus3 repo create hosted (bower|npm|nuget|pypi|raw|rubygems) <repo_name>
         [--blob=<store_name>] [--write=<w_policy>] [--strict-content]
  nexus3 repo create hosted yum <repo_name>
         [--blob=<store_name>] [--write=<w_policy>]
         [--depth=<repo_depth>] [--strict-content]
  nexus3 repo create proxy maven <repo_name> <remote_url>
         [--blob=<store_name>] [--version=<v_policy>]
         [--layout=<l_policy>] [--strict-content]
  nexus3 repo create proxy (bower|npm|nuget|pypi|raw|rubygems|yum)
          <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content]
  nexus3 repo list
  nexus3 repo rm <repo_name> [--force]
  nexus3 script create <script.json>
  nexus3 script list
  nexus3 script (rm|run) <script_name>

Options:
  -h --help             This screen
  --blob=<store_name>   Use this blob with new repository  [default: default]
  --depth=<repo_depth>  Depth (0-5) where repodata folder(s) exist [default: 0]
  --flatten             Flatten directory structure on `nexus3` transfers
                        [default: False]
  --force, -f           Execute action without confirmation
  --layout=<l_policy>   Accepted: strict, permissive [default: strict]
  --nocache             Force download even if local copy is up-to-date
                        [default: False]
  --norecurse           Don't process subdirectories on `nexus3 up` transfers.
                        [default: False]
  --strict-content      Enable strict content type validation
  --version=<v_policy>  Accepted: release, snapshot, mixed [default: release]
  --write=<w_policy>    Accepted: allow, allow_once, deny [default: allow_once]

Commands:
  download      Download an artefact or a directory to local file system
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
import os
import sys
import types

from docopt import docopt

from nexuscli.nexus_client import NexusClient
from nexuscli import repository

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
    if not os.path.isfile(NexusClient.CONFIG_PATH):
        sys.stderr.write(
            'Warning: configuration not found; proceeding with defaults.\n'
            'To remove this warning, please run nexus-cli.py login\n')
    return NexusClient()


def cmd_script_do_list(nexus_client):
    json_response = nexus_client.scripts.list()

    sys.stderr.write('Name (type)\n')
    for script in json_response:
        sys.stdout.write('{script[name]} ({script[type]})\n'.format(
            script=script))


def cmd_script_do_create(nexus_client, script_path):
    script_content = json.load(open(script_path), strict=False)
    nexus_client.scripts.create(script_content)


def cmd_script(args):
    nexus_client = get_client()

    if args.get('list'):
        cmd_script_do_list(nexus_client)
    elif args.get('rm'):
        nexus_client.scripts.delete(args.get('<script_name>'))
    elif args.get('run'):
        nexus_client.scripts.run(args.get('<script_name>'))
    elif args.get('create'):
        cmd_script_do_create(nexus_client, args.get('<script.json>'))
    else:
        raise NotImplementedError


def cmd_repo_do_list(nexus_client):
    json_response = nexus_client.repositories.raw_list()

    output_format = '{0:40} {1:7} {2:7} {3}\n'
    sys.stderr.write(output_format.format('Name', 'Format', 'Type', 'URL'))
    sys.stderr.write(output_format.format('----', '------', '----', '---'))
    for repo in json_response:
        sys.stdout.write(output_format.format(
            repo['name'], repo['format'], repo['type'], repo['url']))


def args_to_repo_format(args):
    # docopt guarantees only one is True
    for format_name in repository.validations.KNOWN_FORMATS:
        if args.get(format_name) is True:
            return format_name


def args_to_repo_type(args):
    # docopt guarantees only one is True
    for type_name in repository.validations.KNOWN_TYPES:
        if args.get(type_name) is True:
            return type_name


def cmd_repo_create(nexus_client, args):
    """Performs ``rekt repo create *`` commands"""
    r = repository.Repository(
        args_to_repo_type(args),
        ignore_extra_kwargs=True,
        name=args.get('<repo_name>'),
        format=args_to_repo_format(args),
        blob_store_name=args.get('--blob'),
        depth=int(args.get('--depth')),
        remote_url=args.get('<remote_url>'),
        strict_content_type_validation=args.get('--strict-content'),
        version_policy=args.get('--version'),
        write_policy=args.get('--write'),
        layout_policy=args.get('--layout'),
    )
    nexus_client.repositories.create(r)


def cmd_repo(args):
    """Performs ``nexus3 repo *`` commands"""
    nexus_client = get_client()

    if args.get('list'):
        cmd_repo_do_list(nexus_client)
    elif args.get('create'):
        cmd_repo_create(nexus_client, args)
    elif args.get('rm'):
        if not args.get('--force'):
            _input('Press ENTER to confirm deletion', 'ctrl+c to cancel')
        nexus_client.repositories.delete(args.get('<repo_name>'))
    else:
        raise NotImplementedError


def cmd_list(args):
    """Performs ``nexus3 list``"""
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
    """Print and exit with error if upload/download/delete didn't succeed"""
    if count == 0:
        # FIXME: inflex the action verb to past participle
        sys.stderr.write('WARNING: no files were {}\'ed.'.format(action))
        sys.exit(1)

    if count == -1:
        sys.stderr.write('ERROR during {} operation.'.format(action))
        sys.exit(2)


def cmd_upload(args):
    """Performs ``nexus3 upload``"""
    nexus_client = get_client()
    source = args['<from_src>']
    destination = args['<to_repository>']

    sys.stderr.write(
        'Uploading {source} to {destination}\n'.format(**locals()))

    upload_count = nexus_client.upload(
                    source, destination,
                    flatten=args.get('--flatten'),
                    recurse=(not args.get('--norecurse')))

    _cmd_up_down_errors(upload_count, 'upload')

    file = PLURAL('file', upload_count)
    sys.stderr.write(
        'Uploaded {upload_count} {file} to {destination}\n'.format(**locals()))
    return 0


def cmd_download(args):
    """Performs ``nexus3 download``"""
    nexus_client = get_client()
    source = args['<from_repository>']
    destination = args['<to_dst>']

    sys.stderr.write(
        'Downloading {source} to {destination}\n'.format(**locals()))

    download_count = nexus_client.download(
                        source, destination,
                        flatten=args.get('--flatten'),
                        nocache=args.get('--nocache'))

    _cmd_up_down_errors(download_count, 'download')

    file_word = PLURAL('file', download_count)
    sys.stderr.write(
        'Downloaded {download_count} {file_word} to '
        '{destination}\n'.format(**locals()))
    return 0


def cmd_delete(options):
    """
    Performs `nexus3 delete`"""
    nexus_client = get_client()
    repository_path = options['<repository_path>']
    delete_count = nexus_client.delete(repository_path)

    _cmd_up_down_errors(delete_count, 'delete')

    file_word = PLURAL('file', delete_count)
    sys.stderr.write(
        'Deleted {delete_count} {file_word}\n'.format(**locals()))
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
    elif arguments.get('download') or arguments.get('dl'):
        cmd_download(arguments)
    elif arguments.get('delete') or arguments.get('del'):
        cmd_delete(arguments)
    else:
        raise NotImplementedError
