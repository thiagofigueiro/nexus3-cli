"""
Usage:
  nexus3 repository --help
  nexus3 repository create hosted maven <repo_name>
         [--blob=<store_name>] [--version=<v_policy>]
         [--layout=<l_policy>] [--strict-content]
         [--write=<w_policy>] [--cleanup=<c_policy>]
  nexus3 repository create hosted (bower|npm|nuget|pypi|raw|rubygems)
         <repo_name> [--blob=<store_name>] [--write=<w_policy>]
        [--strict-content] [--cleanup=<c_policy>]
  nexus3 repository create hosted yum <repo_name>
         [--blob=<store_name>] [--write=<w_policy>]
         [--depth=<repo_depth>] [--strict-content] [--cleanup=<c_policy>]
  nexus3 repository create proxy maven <repo_name> <remote_url>
         [--blob=<store_name>] [--version=<v_policy>]
         [--layout=<l_policy>] [--strict-content] [--cleanup=<c_policy>]
  nexus3 repository create proxy (bower|npm|nuget|pypi|raw|rubygems|yum)
         <repo_name> <remote_url>
         [--blob=<store_name>] [--strict-content] [--cleanup=<c_policy>]
  nexus3 repository list
  nexus3 repository (delete|del) <repo_name> [--force]

Options:
  -h --help             This screen
  --blob=<store_name>   Use this blob with new repository  [default: default]
  --depth=<repo_depth>  Depth (0-5) where repodata folder(s) exist [default: 0]
  --layout=<l_policy>   Accepted: strict, permissive [default: strict]
  --strict-content      Enable strict content type validation
  --version=<v_policy>  Accepted: release, snapshot, mixed [default: release]
  --write=<w_policy>    Accepted: allow, allow_once, deny [default: allow_once]
  --cleanup=<c_policy>  Accepted: an existing Cleanup Policy name
  -f --force            Do not ask for confirmation before deleting

Commands:
  repository create  Create a repository using the format and options provided
  repository list    List all repositories available on the server
  repository delete  Delete a repository.
"""
from docopt import docopt
from texttable import Texttable

from nexuscli.api import repository
from nexuscli.cli import errors, util


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
    return errors.CliReturnCode.SUCCESS.value


def _args_to_repo_format(args):
    # docopt guarantees only one is True
    for format_name in repository.validations.KNOWN_FORMATS:
        if args.get(format_name) is True:
            return format_name


def _args_to_repo_type(args):
    # docopt guarantees only one is True
    for type_name in repository.validations.KNOWN_TYPES:
        if args.get(type_name) is True:
            return type_name


def cmd_create(nexus_client, args):
    """Performs ``nexus3 repository create`` commands"""
    r = repository.Repository(
        nexus_client,
        type=_args_to_repo_type(args),
        ignore_extra_kwargs=True,
        name=args.get('<repo_name>'),
        format=_args_to_repo_format(args),
        blob_store_name=args.get('--blob'),
        depth=int(args.get('--depth')),
        remote_url=args.get('<remote_url>'),
        strict_content_type_validation=args.get('--strict-content'),
        version_policy=args.get('--version'),
        write_policy=args.get('--write'),
        layout_policy=args.get('--layout'),
        cleanup_policy=args.get('--cleanup'),
    )
    nexus_client.repositories.create(r)
    return errors.CliReturnCode.SUCCESS.value


def cmd_del(*args, **kwargs):
    """Alias for :func:`cmd_delete`"""
    return cmd_delete(*args, **kwargs)


def cmd_delete(nexus_client, args):
    """Performs ``nexus3 repository delete``"""
    if not args.get('--force'):
        util.input_with_default(
            'Press ENTER to confirm deletion', 'ctrl+c to cancel')
    nexus_client.repositories.delete(args.get('<repo_name>'))
    return errors.CliReturnCode.SUCCESS.value


def main(argv=None):
    """Entrypoint for ``nexus3 repository`` subcommand."""
    arguments = docopt(__doc__, argv=argv)
    command_method = util.find_cmd_method(arguments, globals())
    return command_method(util.get_client(), arguments)
