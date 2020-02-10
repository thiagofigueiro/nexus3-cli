"""
Usage:
  nexus3 repository create proxy maven
         <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
         [--version=<v_policy>] [--layout=<l_policy>]
         [--remote_auth_type=<remote_auth_type>]
         [--remote_username=<username>] [--remote_password=<password>]
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

Options:
  --index_type=<index_type>             Accepted: registry, hub, custom [default: registry]
  --remote_auth_type=<remote_auth_type> Accepted: username [default: None]
  --remote_username=<remote_username>   Remote username
  --remote_password=<remote_password>   Remote password
  --gpg=<gpg-file-path>                 gpg file [default: ./public.gpg.key]
  --passphrase=<passphrase>             passphrase for the given gpg [default: ]
  --distribution=<distribution>         filter distributions [default: buster]
  --flat                                flat repository [default: False]

Commands:
  repository create  Create a repository using the format and options provided
"""
import json
from texttable import Texttable

from nexuscli import exception
from nexuscli.api import repository
from nexuscli.cli import util


def cmd_list(nexus_client):
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


def cmd_create(ctx,
               repo_type=None,
               repository_name=None,
               strict_content=None,
               **kwargs):
    """Performs ``nexus3 repository create`` commands"""
    nexus_client = ctx.obj
    recipe = kwargs["recipe"]

    kwargs.update({
        'nexus_client': nexus_client,
        'strict_content_type_validation': strict_content,
    })
    print('kwargs inside', kwargs)

    # TODO: find better home for these
    # if repo_type == 'proxy':
    #     kwargs.update({'remote_url': args.get('<remote_url>'),
    #                    'remote_auth_type': args.get('--remote_auth_type'),
    #                    'remote_username': args.get('--remote_username'),
    #                    'remote_password': args.get('--remote_password')
    #                    })
    #
    #     if recipe == 'docker':
    #         kwargs.update({'index_type': args.get('--index_type').upper(),
    #                        'use_trust_store_for_index_access':
    #                            args.get('--use_trust_store_for_index_access'),
    #                        'index_url': args.get('--index_url')})

    if recipe_name == 'apt':
        kwargs.update({'distribution': args.get('--distribution')})

        if repo_type == 'hosted':
            # TODO maybe generage the gpg key?
            kwargs.update({'gpg': args.get('--gpg'),
                           'passphrase': args.get('--passphrase')})

        if repo_type == 'proxy':
            kwargs.update({'flat': args.get('--flat')})

    Repository = repository.collection.get_repository_class({
        'recipeName': f'{recipe}-{repo_type}'})

    r = Repository(repository_name, **kwargs)

    nexus_client.repositories.create(r)

    return exception.CliReturnCode.SUCCESS.value


def cmd_delete(nexus_client, repository_name):
    """Performs ``nexus3 repository delete``"""
    nexus_client.repositories.delete(repository_name)
    return exception.CliReturnCode.SUCCESS.value


def cmd_show(nexus_client, repository_name):
    """Performs ``nexus3 repository show"""
    repo_name = repository_name
    try:
        configuration = nexus_client.repositories.get_raw_by_name(repo_name)
    except exception.NexusClientInvalidRepository:
        print(f'Repository not found: {repo_name}')
        return exception.CliReturnCode.REPOSITORY_NOT_FOUND.value

    print(json.dumps(configuration, indent=2))
    return exception.CliReturnCode.SUCCESS.value
