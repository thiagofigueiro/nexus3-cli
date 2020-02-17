import click
import pkg_resources

from nexuscli import nexus_config
from nexuscli.api.repository import model
from nexuscli.cli import (
    root_commands, util, subcommand_repository,
    subcommand_cleanup_policy, subcommand_script)

PACKAGE_VERSION = pkg_resources.get_distribution('nexus3-cli').version
ENV_VAR_PREFIX = 'NEXUS3'
CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'], auto_envvar_prefix=ENV_VAR_PREFIX)


#############################################################################
# root commands
@click.group(cls=util.AliasedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(version=PACKAGE_VERSION, message='%(version)s')
def nexus_cli():
    pass


@nexus_cli.command()
@click.option(
    '--url', '-U', default=nexus_config.DEFAULTS['url'], prompt=True,
    help='Nexus OSS URL', show_default=True, allow_from_autoenv=True)
@click.option(
    '--username', '-u', default=nexus_config.DEFAULTS['username'], prompt=True,
    help='Nexus user', show_default=True, allow_from_autoenv=True)
@click.option(
    '--password', '-p', prompt=True, hide_input=True,
    help='Password for user', allow_from_autoenv=True)
@click.option(
    '--x509_verify/--no-x509_verify', prompt=True,
    default=nexus_config.DEFAULTS['x509_verify'], show_default=True,
    help='Verify server certificate', allow_from_autoenv=True)
def login(**kwargs):
    """
    Login to Nexus server, saving settings to ~/.nexus-cli.
    """
    root_commands.cmd_login(**kwargs)


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
# TODO: use Path for src argument
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


#############################################################################
# repository create hosted sub-commands
@repository_create.command(
    name='hosted',
    cls=util.mapped_commands({
        'apt': model.AptHostedRepository.RECIPES,
        'docker': model.DockerHostedRepository.RECIPES,
        'maven': model.MavenHostedRepository.RECIPES,
        'yum': model.YumHostedRepository.RECIPES,
        # generic, remaining repositories
        'recipe': model.HostedRepository.RECIPES,
    }))
def repository_create_hosted():
    """
    Create a hosted repository.
    """
    pass


def _create_repository(ctx, repo_type, **kwargs):
    # every repository recipe needs these
    kwargs['recipe'] = ctx.info_name
    util.upcase_values(
        kwargs, ['index_type', 'layout_policy', 'version_policy',
                 'write_policy'])

    # these CLI options were shortened for user convenience; fix them now
    util.rename_keys(kwargs, {
        'negative_cache': 'negative_cache_enabled',
        'strict_content': 'strict_content_type_validation',
        'trust_store': 'use_trust_store_for_index_access',
    })

    subcommand_repository.cmd_create(ctx, repo_type=repo_type, **kwargs)


REPOSITORY_COMMON_OPTIONS = [
    click.argument('repository-name'),
    click.option('--blob-store-name', default='default',
                 help='Blobstore name to use with new repository'),
    click.option('--strict-content/--no-strict-content', default=False,
                 help='Toggle strict content type validation'),
    click.option('--cleanup-policy',
                 help='Name of existing clean-up policy to use'),
]

REPOSITORY_COMMON_HOSTED_OPTIONS = REPOSITORY_COMMON_OPTIONS + [
    click.option(
        '--write-policy', help='Write policy to use', default='allow',
        type=click.Choice(['allow', 'allow_once', 'deny'],
                          case_sensitive=False))
]


@repository_create_hosted.command(name='recipe')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@util.with_nexus_client
def repository_create_hosted_recipe(ctx: click.Context, **kwargs):
    """
    Create a hosted repository.
    """
    _create_repository(ctx, 'hosted', **kwargs)


REPOSITORY_COMMON_APT_OPTIONS = [
    click.option(
        '--distribution', required=True,
        help='Distribution to fetch; e.g.: bionic')
]


@repository_create_hosted.command(name='apt')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@util.add_options(REPOSITORY_COMMON_APT_OPTIONS)
@click.option(
    '--gpg-keypair', required=True, type=click.File(),
    default='./private.gpg.key', help='Path to GPG signing key')
@click.option('--passphrase', help='Passphrase for GPG key pair')
@util.with_nexus_client
def repository_create_hosted_apt(ctx: click.Context, **kwargs):
    """
    Create a hosted apt repository.
    """
    kwargs['gpg_keypair'] = kwargs['gpg_keypair'].read()
    _create_repository(ctx, 'hosted', **kwargs)


REPOSITORY_COMMON_DOCKER_OPTIONS = [
    click.option(
        '--v1-enabled/--no-v1-enabled', default=False,
        help='Enable v1 registry'),
    click.option(
        '--force-basic-auth/--no-force-basic-auth', default=False,
        help='Force use of basic authentication'),
    click.option(
        '--http-port', type=click.INT, help='Port for HTTP service'),
    click.option(
        '--https-port', type=click.INT, help='Port for HTTPS service'),
]


@repository_create_hosted.command(name='docker')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@util.add_options(REPOSITORY_COMMON_DOCKER_OPTIONS)
@util.with_nexus_client
def repository_create_hosted_docker(ctx: click.Context, **kwargs):
    """
    Create a hosted docker repository.
    """
    _create_repository(ctx, 'hosted', **kwargs)


REPOSITORY_COMMON_MAVEN_OPTIONS = [
    click.option(
        '--version-policy', help='Version policy to use', default='release',
        type=click.Choice(['release', 'snapshot', 'mixed'],
                          case_sensitive=False)),
    click.option(
        '--layout-policy', help='Layout policy to use', default='strict',
        type=click.Choice(['strict', 'permissive'],
                          case_sensitive=False)),
]


@repository_create_hosted.command(name='maven')
@util.add_options(REPOSITORY_COMMON_HOSTED_OPTIONS)
@util.add_options(REPOSITORY_COMMON_MAVEN_OPTIONS)
@util.with_nexus_client
def repository_create_hosted_maven(ctx: click.Context, **kwargs):
    """
    Create a hosted maven repository.
    """
    _create_repository(ctx, 'hosted', **kwargs)


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
    _create_repository(ctx, 'hosted', **kwargs)


#############################################################################
# repository create proxy sub-commands
@repository_create.command(
    name='proxy',
    cls=util.mapped_commands({
        'apt': model.AptProxyRepository.RECIPES,
        'docker': model.DockerProxyRepository.RECIPES,
        'maven': model.MavenProxyRepository.RECIPES,
        'yum': model.YumProxyRepository.RECIPES,
        # remaining, generic repositories
        'recipe': model.ProxyRepository.RECIPES,
    }))
def repository_create_proxy():
    """
    Create a proxy repository.
    """
    pass


REPOSITORY_COMMON_PROXY_OPTIONS = REPOSITORY_COMMON_OPTIONS + [
    click.argument('remote-url'),
    click.option(
        '--auto-block/--no-auto-block', default=True,
        help='Disable outbound connections on remote-url access errors'),
    click.option(
        '--negative-cache/--no-negative-cache', default=True,
        help='Cache responses for content missing in the remote-url'),
    click.option(
        '--negative-cache-ttl', type=click.INT, default=1440,
        help='Cache time in minutes'),
    click.option(
        '--content-max-age', type=click.INT, default=1440,
        help='Maximum age of cached artefacts'),
    click.option(
        '--metadata-max-age', type=click.INT, default=1440,
        help='Maximum age of cached artefacts metadata'),
    click.option(
        '--remote-auth-type', help='Only username is supported',
        type=click.Choice(['username'], case_sensitive=False)),
    # TODO: require `--remote-auth-type username` when these are specified
    click.option('--remote-username', help='Username for remote URL'),
    click.option('--remote-password', help='Password for remote URL'),
]


@repository_create_proxy.command(name='recipe')
@util.add_options(REPOSITORY_COMMON_PROXY_OPTIONS)
@util.with_nexus_client
def repository_create_proxy_recipe(ctx: click.Context, **kwargs):
    """
    Create a proxy repository.
    """
    _create_repository(ctx, 'proxy', **kwargs)


@repository_create_proxy.command(name='apt')
@util.add_options(REPOSITORY_COMMON_PROXY_OPTIONS)
@util.add_options(REPOSITORY_COMMON_APT_OPTIONS)
@click.option(
    '--flat/--no-flat', default=False, help='Is this repository flat?')
@util.with_nexus_client
def repository_create_proxy_apt(ctx: click.Context, **kwargs):
    """
    Create a proxy apt repository.
    """
    _create_repository(ctx, 'proxy', **kwargs)


@repository_create_proxy.command(name='docker')
@util.add_options(REPOSITORY_COMMON_PROXY_OPTIONS)
@util.add_options(REPOSITORY_COMMON_DOCKER_OPTIONS)
@click.option(
    '--index-type', help='Docker index type', default='registry',
    type=click.Choice(['registry', 'hub', 'custom'],
                      case_sensitive=False))
# TODO: enforce requirement
@click.option('--index-url', help='Required for --index-type custom')
@click.option(
    '--trust-store/--no-trust-store', default=False,
    help='Required for --index-type hub or custom')
@util.with_nexus_client
def repository_create_proxy_docker(ctx: click.Context, **kwargs):
    """
    Create a docker proxy repository.
    """
    _create_repository(ctx, 'proxy', **kwargs)


@repository_create_proxy.command(name='maven')
@util.add_options(REPOSITORY_COMMON_PROXY_OPTIONS)
@util.add_options(REPOSITORY_COMMON_MAVEN_OPTIONS)
@util.with_nexus_client
def repository_create_proxy_maven(ctx: click.Context, **kwargs):
    """
    Create a maven proxy repository.
    """
    _create_repository(ctx, 'proxy', **kwargs)


@repository_create_proxy.command(name='yum')
@util.add_options(REPOSITORY_COMMON_PROXY_OPTIONS)
@util.with_nexus_client
def repository_create_proxy_yum(ctx: click.Context, **kwargs):
    """
    Create a yum proxy repository.
    """
    _create_repository(ctx, 'proxy', **kwargs)


#############################################################################
# cleanup_policy sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def cleanup_policy():
    """
    Manage clean-up policies.
    """
    pass


@cleanup_policy.command(name='create')
@click.argument('name')
@click.option(
    '--format', default='all',
    help='The recipe that this cleanup policy can be applied to',
    type=click.Choice(['all'] + list(model.SUPPORTED_FORMATS)))
@click.option(
    '--downloaded', type=click.IntRange(min=1),
    help='Cleanup criteria; last downloaded in this many days.')
@click.option(
    '--updated', type=click.IntRange(min=1),
    help='Cleanup criteria; last updated in this many days.')
# TODO: validate formats that accept regex
@click.option(
    '--regex',
    help='Cleanup criteria; only cleanup components matching expression')
@click.option(
    '--notes',
    help='Notes about your policy')
@util.with_nexus_client
def cleanup_policy_create(ctx: click.Context, **kwargs):
    """
    Create or update a cleanup policy called NAME.
    """
    # TODO: use a click type for this check?
    criteria_keys = {'downloaded', 'updated', 'regex'}
    util.move_to_key(kwargs, 'criteria', criteria_keys)

    util.rename_keys(kwargs['criteria'], {
        'downloaded': 'lastDownloaded',
        'updated': 'lastBlobUpdated',
    })

    subcommand_cleanup_policy.cmd_create(ctx.obj, **kwargs)


@cleanup_policy.command(name='list')
@util.with_nexus_client
def cleanup_policy_list(ctx: click.Context):
    subcommand_cleanup_policy.cmd_list(ctx.obj)


#############################################################################
# script sub-commands
@nexus_cli.group(cls=util.AliasedGroup)
def script():
    """
    Manage scripts.
    """
    pass


@script.command(name='create')
@click.argument('name')
@click.argument('file', type=click.File())
@click.option('--script-type', default='groovy', help='Script type')
@util.with_nexus_client
def script_create(ctx: click.Context, name, file, **kwargs):
    """
    Create a new script called NAME from FILE.
    """
    subcommand_script.cmd_create(ctx.obj, name, file.read(), **kwargs)


@script.command(name='delete')
@click.argument('name')
@util.with_nexus_client
def script_delete(ctx: click.Context, name):
    """
    Delete the script called NAME.
    """
    subcommand_script.cmd_delete(ctx.obj, name)


@script.command(name='list')
@util.with_nexus_client
def script_list(ctx: click.Context):
    """
    List all scripts.
    """
    subcommand_script.cmd_list(ctx.obj)


@script.command(name='run')
@click.argument('name')
@click.option('--script-arguments', '-a')
@util.with_nexus_client
def script_run(ctx: click.Context, name, script_arguments):
    """
    Run the script called NAME.
    """
    subcommand_script.cmd_run(ctx.obj, name, script_arguments)
