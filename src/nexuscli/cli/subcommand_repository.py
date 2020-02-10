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


def cmd_create(ctx, repo_type=None, repository_name=None, **kwargs):
    """Performs ``nexus3 repository create`` commands"""
    nexus_client = ctx.obj
    recipe = kwargs["recipe"]
    kwargs['nexus_client'] = nexus_client

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
