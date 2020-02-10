import click
import pkg_resources

from nexuscli.api.repository.model import (
    DockerRepository, MavenRepository, Repository, YumRepository)
from nexuscli.cli import (
    errors, root_commands, util, subcommand_repository,
    subcommand_cleanup_policy, subcommand_script)

PACKAGE_VERSION = pkg_resources.get_distribution('nexus3-cli').version
HELP_OPTIONS = dict(help_option_names=['-h', '--help'])
REPOSITORY_COMMON_OPTIONS = [
    click.option('--blob-store-name', default='default',
                  help='Blobstore name to use with new repository'),
    click.option('--strict-content/--no-strict-content', default=False,
                  help='Toggle strict content type validation'),
    click.option('--cleanup-policy',
                  help='Name of existing clean-up policy to use'),
]
REPOSITORY_COMMON_HOSTED_OPTIONS = [
    click.argument('repository_name'),
    click.option(
        '--write-policy', help='Write policy to use', default='allow',
        type=click.Choice(['allow', 'allow_once', 'deny'],
                          case_sensitive=False))
] + REPOSITORY_COMMON_OPTIONS


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
    Login to Nexus server, saving settings to ~/.nexus-cli.
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
@click.argument('dst')
@click.option('--flatten/--no-flatten', default=False,
              help='Flatten DST directory structure')
@click.option('--recurse/--no-recurse', default=True,
              help='Process all SRC subdirectories')
@util.with_nexus_client
def upload(ctx: click.Context, **kwargs):
    """
    Upload local SRC to remote DST.  If either argument ends with a `/`, it's
    assumed to be a directory.

    DEST must start with a repository name and optionally be followed by the
    path where SRC is to be uploaded to.
    """
    root_commands.cmd_upload(ctx.obj, **kwargs)


@nexus_cli.command()
@click.argument('src')
@click.argument('dst')
@click.option('--flatten/--no-flatten', default=False,
              help='Flatten DEST directory structure')
@click.option('--cache/--no-cache', default=True,
              help='Do not download if a local copy is already up-to-date')
@util.with_nexus_client
def download(ctx: click.Context, **kwargs):
    """
    Download remote SRC to local DEST.  If either argument ends with a `/`,
    it's assumed to be a directory.

    SRC must start with a repository name and optionally be followed by a path
    to be downloaded.
    """
    root_commands.cmd_download(ctx.obj, **kwargs)


#############################################################################
# repository sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def repository():
    """
    Manage repositories.
    """
    pass


@repository.command(name='list')
@util.with_nexus_client
def repository_list(ctx: click.Context):
    """
    List all repositories.
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
def repository_delete(ctx: click.Context, repository_name):
    """
    Delete REPOSITORY_NAME (but not its blobstore).
    """
    subcommand_repository.cmd_delete(ctx.obj, repository_name)


#############################################################################
# repository create sub-commands
@repository.group(cls=util.AliasedGroup, name='create')
def repository_create():
    """
    Create a repository.
    """
    pass


@repository_create.command(
    cls=util.mapped_commands({
        'docker': DockerRepository.RECIPES,
        'maven': MavenRepository.RECIPES,
        'recipe': Repository.RECIPES,
        'yum': YumRepository.RECIPES,
    }),
    name='hosted')
def repository_create_hosted():
    """
    Created a hosted repository.
    """
    pass


@repository_create_hosted.command(name='recipe')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@util.with_nexus_client
def repository_create_hosted_recipe(ctx: click.Context, **kwargs):
    """
    Create a hosted repository.
    """
    # when we're called from another recipe (docker, maven), we want to use
    # their name because our own `info_name` will be `recipe`.
    recipe = ctx.info_name
    if ctx.parent.info_name != 'hosted':
        recipe = ctx.parent.info_name

    kwargs.update({
        'write_policy': kwargs['write_policy'].upper(),
        'recipe': recipe,
    })

    subcommand_repository.cmd_create(ctx, repo_type='hosted', **kwargs)


@repository_create_hosted.command(name='maven')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@click.option(
    '--version-policy', help='Version policy to use', default='release',
    type=click.Choice(['release', 'snapshot', 'mixed'],
                      case_sensitive=False))
@click.option(
    '--layout-policy', help='Layout policy to use', default='strict',
    type=click.Choice(['strict', 'permissive'],
                      case_sensitive=False))
@util.with_nexus_client
def repository_create_hosted_maven(ctx: click.Context, **kwargs):
    """
    Create a hosted maven repository.
    """
    kwargs.update({
        'layout_policy': kwargs['layout_policy'].upper(),
        'version_policy': kwargs['version_policy'].upper(),
    })

    ctx.invoke(repository_create_hosted_recipe, **kwargs)


@repository_create_hosted.command(name='yum')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@click.option(
    '--depth', help='Depth where repodata folder(s) exist', default=0,
    type=click.IntRange(min=0, max=5, clamp=False))
@util.with_nexus_client
def repository_create_hosted_yum(ctx: click.Context, **kwargs):
    """
    Create a hosted yum repository.
    """
    ctx.invoke(repository_create_hosted_recipe, **kwargs)


@repository_create_hosted.command(name='docker')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@click.option(
    '--v1-enabled/--no-v1-enabled', help='Enable v1 registry', default=False)
@click.option(
    '--force-basic-auth/--no-force-basic-auth',
    help='Force use of basic authentication', default=False)
@click.option('--http-port', type=click.INT, help='Port for HTTP service')
@click.option('--https-port', type=click.INT, help='Port for HTTPS service')
@util.with_nexus_client
def repository_create_hosted_docker(ctx: click.Context, **kwargs):
    """
    Create a hosted docker repository.
    """
    ctx.invoke(repository_create_hosted_recipe, **kwargs)


# TODO: use mapped_commands instead of click.Choice
@repository_create.command(name='proxy')
@click.argument(
    'recipe', metavar='RECIPE',
    type=click.Choice([
        'bower', 'npm', 'nuget', 'pypi', 'raw', 'rubygems', 'yum'],
        case_sensitive=False))
@click.argument('repository_name')
@click.argument('remote_url')
@util.add_options(REPOSITORY_COMMON_OPTIONS)
@click.option('--remote-auth-type',
              help='Only username is supported',
              type=click.Choice(['username'], case_sensitive=False))
@click.option('--remote-username',
              help='Username for remote URL')
@click.option('--remote-password',
              help='Password for remote URL')
@util.with_nexus_client
def repository_create_hosted(ctx: click.Context, **kwargs):
    """
    Create a proxy repository of type RECIPE.
    """
    subcommand_repository.cmd_create(ctx, **kwargs)


#############################################################################
# cleanup_policy sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def cleanup_policy():
    """
    Manage clean-up policies.
    """
    pass


#############################################################################
# script sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def script():
    """
    Manage scripts.
    """
    pass
