import click
import pkg_resources
from nexuscli.cli import (
    errors, root_commands, util, subcommand_repository,
    subcommand_cleanup_policy, subcommand_script)

PACKAGE_VERSION = pkg_resources.get_distribution('nexus3-cli').version
HELP_OPTIONS = dict(help_option_names=['-h', '--help'])


# TODO: auto_envvar_prefix='NEXUS_CLI' for username, password etc
@click.group(cls=util.AliasedGroup, context_settings=HELP_OPTIONS)
@click.version_option(version=PACKAGE_VERSION, message='%(version)s')
def nexus_cli():
    pass


#############################################################################
# root commands
@nexus_cli.command()
# TODO: @click.option('--password', '-P', prompt=True, hide_input=True,
#               confirmation_prompt=True)
#   --username etc
def login():
    """
    Login to Nexus server, saving settings to ~/.nexus-cli
    """
    root_commands.cmd_login()


@nexus_cli.command(name='list')
@click.argument('repository_path')
@util.with_nexus_client
def list_(ctx: click.Context, repository_path):
    """
    List all files within REPOSITORY_PATH.

    REPOSITORY_PATH must start with a repository name.
    """
    root_commands.cmd_list(ctx.obj, repository_path)


@nexus_cli.command()
@click.argument('repository_path')
@util.with_nexus_client
def delete(ctx: click.Context, repository_path):
    """
    Recursively delete all files under REPOSITORY_PATH.

    REPOSITORY_PATH must start with a repository name.
    """
    root_commands.cmd_delete(ctx.obj, repository_path)


@nexus_cli.command()
@click.argument('src')
@click.argument('dest')
@click.option('--flatten/--no-flatten', default=False,
              help='Flatten DEST directory structure')
@click.option('--recurse/--no-recurse', default=True,
              help='Process all SRC subdirectories')
@util.with_nexus_client
def upload(ctx: click.Context, src, dest, flatten, recurse):
    """
    Upload local SRC to remote DEST.  If either argument ends with a `/`, it's
    assumed to be a directory.

    DEST must start with a repository name and optionally be followed by the
    path where SRC is to be uploaded to.
    """
    root_commands.cmd_upload(ctx.obj, src, dest, flatten, recurse)


@nexus_cli.command()
@click.argument('src')
@click.argument('dest')
@click.option('--flatten/--no-flatten', default=False,
              help='Flatten DEST directory structure')
@click.option('--cache/--no-cache', default=True,
              help='Do not download if a local copy is already up-to-date')
@util.with_nexus_client
def download(ctx: click.Context, src, dest, flatten, cache):
    """
    Download remote SRC to local DEST.  If either argument ends with a `/`,
    it's assumed to be a directory.

    SRC must start with a repository name and optionally be followed by a path
    to be downloaded.
    """
    root_commands.cmd_download(ctx.obj, src, dest, flatten, not cache)


#############################################################################
# repository sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def repository():
    """
    Manage repositories
    """
    pass


@repository.command(name='list')
@util.with_nexus_client
def repository_list(ctx: click.Context):
    """
    List all repositories
    """
    subcommand_repository.cmd_list(ctx.obj)


@repository.command(name='show')
@click.argument('repository_name')
@util.with_nexus_client
def repository_show(ctx: click.Context, repository_name):
    """
    Show the configuration for REPOSITORY_NAME as JSON.
    """
    subcommand_repository.cmd_show(ctx.obj, repository_name)


@repository.command(name='delete')
@click.argument('repository_name')
@click.confirmation_option()
@util.with_nexus_client
def repository_show(ctx: click.Context, repository_name):
    """
    Delete REPOSITORY_NAME (but not its blobstore).
    """
    subcommand_repository.cmd_delete(ctx.obj, repository_name)


#############################################################################
# cleanup_policy sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def cleanup_policy():
    """
    Manage clean-up policies
    """
    pass


#############################################################################
# script sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def script():
    """
    Manage scripts
    """
    pass
