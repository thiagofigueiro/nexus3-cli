"""
Usage:
  nexus3 repository list
  nexus3 repository show <repo_name>
  nexus3 repository (delete|del) <repo_name> [--force]
  nexus3 repository create hosted (bower|npm|nuget|pypi|raw|rubygems|docker)
         <repo_name>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--write=<w_policy>]
  nexus3 repository create proxy (bower|npm|nuget|pypi|raw|rubygems|yum)
         <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--remote_auth_type=<remote_auth_type>]
         [--remote_username=<username>] [--remote_password=<password>]
  nexus3 repository create hosted maven
         <repo_name>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--write=<w_policy>]
         [--version=<v_policy>] [--layout=<l_policy>]
  nexus3 repository create proxy maven
         <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--version=<v_policy>] [--layout=<l_policy>]
         [--remote_auth_type=<remote_auth_type>]
         [--remote_username=<username>] [--remote_password=<password>]
  nexus3 repository create hosted yum
         <repo_name>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--write=<w_policy>]
         [--depth=<repo_depth>]
  nexus3 repository create proxy docker
         <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--v1_enabled]
         [--force_basic_auth]
         [--index_type=<index_type>]
         [--http_port=<http_port>]
         [--https_port=<https_port>]
         [--remote_auth_type=<remote_auth_type>]
         [--remote_username=<username>] [--remote_password=<password>]
  nexus3 repository create hosted docker
         <repo_name>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--write=<w_policy>]
         [--v1_enabled]
         [--force_basic_auth]
         [--http_port=<http_port>]
         [--https_port=<https_port>]
    nexus3 repository create hosted apt
         <repo_name>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--write=<w_policy>] [--gpg=<gpg-file-path>]
         [--passphrase=passphrase] [--distribution=<distribution>]
    nexus3 repository create proxy apt
         <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--write=<w_policy>]
         [--remote_auth_type=<remote_auth_type>]
         [--remote_username=<username>] [--remote_password=<password>]
         [--flat] [--distribution=<distribution>]

Options:
  --blob=<store_name>                   Use this blob with new repository  [default: default]  # noqa: E501
  --depth=<repo_depth>                  Depth (0-5) where repodata folder(s) exist [default: 0]
  --layout=<l_policy>                   Accepted: strict, permissive [default: strict]
  --strict-content                      Enable strict content type validation
  --version=<v_policy>                  Accepted: release, snapshot, mixed [default: release]
  --write=<w_policy>                    Accepted: allow, allow_once, deny [default: allow_once]
  --cleanup=<c_policy>                  Accepted: an existing Cleanup Policy name
  -f --force                            Do not ask for confirmation before deleting
  --v1_enabled                          Enable v1 registry [default: False]
  --index_type=<index_type>             Accepted: registry, hub, custom [default: registry]
  --force_basic_auth                    Force to use basic authentication against this docker repo
  --remote_auth_type=<remote_auth_type> Accepted: username [default: None]
  --remote_username=<remote_username>   Remote username
  --remote_password=<remote_password>   Remote password
  --gpg=<gpg-file-path>                 gpg file [default: ./public.gpg.key]
  --passphrase=<passphrase>             passphrase for the given gpg [default: ]
  --distribution=<distribution>         filter distributions [default: buster]
  --flat                                flat repository [default: False]

Commands:
  repository create  Create a repository using the format and options provided
  repository delete  Delete a repository.
  repository list    List all repositories available on the server
  repository show    Show the configuration for a repository as JSON.
"""
import json
from docopt import docopt
from texttable import Texttable

from nexuscli import exception
from nexuscli.api import repository
from nexuscli.cli import util


def cmd_list(nexus_client, _):
    """Performs ``nexus3 repository list``"""
    repositories = nexus_client.repositories.raw_list()

    table = Texttable(max_width=util.TTY_MAX_WIDTH)
    table.add_row(['Name', 'Format', 'Type', 'URL'])
    table.set_deco(Texttable.HEADER)
    for repo in repositories:
        table.add_row(
            [repo['name'], repo['format'], repo['type'], repo['url']])

    print(table.draw())
    return exception.CliReturnCode.SUCCESS.value


def _args_to_repo_type(args):
    # docopt guarantees only one is True
    for type_name in ['hosted', 'proxy', 'group']:
        if args.get(type_name) is True:
            return type_name


def _args_to_recipe_name(args):
    for class_ in repository.model.__all__:
        for recipe_name in class_.RECIPES:
            if args.get(recipe_name) is True:
                return recipe_name


def cmd_create(nexus_client, args):
    """Performs ``nexus3 repository create`` commands"""
    recipe_name = _args_to_recipe_name(args)
    repo_type = _args_to_repo_type(args)

    kwargs = {
        'nexus_client': nexus_client,
        'recipe': recipe_name,
        'blob_store_name': args.get('--blob'),
        'strict_content_type_validation': args.get('--strict-content'),
        'cleanup_policy': args.get('--cleanup'),
    }

    # TODO: find better home for these
    if repo_type == 'hosted':
        kwargs.update({'write_policy': args.get('--write').upper()})

    if repo_type == 'proxy':
        kwargs.update({'remote_url': args.get('<remote_url>'),
                       'remote_auth_type': args.get('--remote_auth_type'),
                       'remote_username': args.get('--remote_username'),
                       'remote_password': args.get('--remote_password')
                       })

        if recipe_name == 'docker':
            kwargs.update({'index_type': args.get('--index_type').upper(),
                           'use_trust_store_for_index_access':
                               args.get('--use_trust_store_for_index_access'),
                           'index_url': args.get('--index_url')})

    if recipe_name == 'yum':
        kwargs.update({'depth': int(args.get('--depth'))})

    if recipe_name.startswith('maven'):
        kwargs.update({
            'version_policy': args.get('--version').upper(),
            'layout_policy': args.get('--layout').upper()})

    if recipe_name == 'docker':
        kwargs.update({'http_port': args.get('--http_port'),
                       'https_port': args.get('--https_port'),
                       'v1_enabled': args.get('--v1_enabled'),
                       'force_basic_auth': args.get('--force_basic_auth')})

    if recipe_name == 'apt':
        kwargs.update({'distribution': args.get('--distribution')})

        if repo_type == 'hosted':
            # TODO maybe generage the gpg key?
            kwargs.update({'gpg': args.get('--gpg'),
                           'passphrase': args.get('--passphrase')})

        if repo_type == 'proxy':
            kwargs.update({'flat': args.get('--flat')})

    Repository = repository.collection.get_repository_class({
        'recipeName': f'{recipe_name}-{repo_type}'})

    r = Repository(args.get('<repo_name>'), **kwargs)

    nexus_client.repositories.create(r)

    return exception.CliReturnCode.SUCCESS.value


def cmd_del(*args, **kwargs):
    """Alias for :func:`cmd_delete`"""
    return cmd_delete(*args, **kwargs)


def cmd_delete(nexus_client, args):
    """Performs ``nexus3 repository delete``"""
    if not args.get('--force'):
        util.input_with_default(
            'Press ENTER to confirm deletion', 'ctrl+c to cancel')
    nexus_client.repositories.delete(args.get('<repo_name>'))
    return exception.CliReturnCode.SUCCESS.value


def cmd_show(nexus_client, args):
    """Performs ``nexus3 repository show"""
    repo_name = args.get('<repo_name>')
    try:
        configuration = nexus_client.repositories.get_raw_by_name(repo_name)
    except exception.NexusClientInvalidRepository:
        print(f'Repository not found: {repo_name}')
        return exception.CliReturnCode.REPOSITORY_NOT_FOUND.value

    print(json.dumps(configuration, indent=2))

    return exception.CliReturnCode.SUCCESS.value


def main(argv=None):
    """Entrypoint for ``nexus3 repository`` subcommand."""
    arguments = docopt(__doc__, argv=argv)
    command_method = util.find_cmd_method(arguments, globals())

    return command_method(util.get_client(), arguments)
