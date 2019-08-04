"""
Usage:
  nexus3 cleanup_policy --help
  nexus3 cleanup_policy create <policy_name> [--format=<format>]
         [--downloaded=<days>] [--updated=<days>]
  nexus3 cleanup_policy list

Options:
  -h --help             This screen
  --format=<format>     Accepted: all or a repository format [default: all]
  --downloaded=<days>   Cleanup criteria; last downloaded in this many days.
  --updated=<days>      Cleanup criteria; last updated in this many days.


Commands:
  cleanup_policy create  Create or update the cleanup policy <policy_name>
  cleanup_policy list    List all existing cleanup policies.
"""
from docopt import docopt
from texttable import Texttable

from nexuscli.api import cleanup_policy
from nexuscli.cli import errors, util


def cmd_list(nexus_client, _):
    """Performs ``nexus3 cleanup_policy list``"""
    policies = nexus_client.cleanup_policies.list()
    if len(policies) == 0:
        return errors.CliReturnCode.POLICY_NOT_FOUND.value

    table = Texttable(max_width=util.TTY_MAX_WIDTH)
    table.add_row(['Name', 'Format', 'lastDownloaded', 'lastBlobUpdated'])
    table.set_deco(Texttable.HEADER)
    for policy in policies:
        p = policy.configuration
        table.add_row([
            p['name'], p['format'],
            p['criteria'].get('lastDownloaded', 'null'),
            p['criteria'].get('lastBlobUpdated', 'null')])

    print(table.draw())
    return errors.CliReturnCode.SUCCESS.value


def cmd_create(nexus_client, args):
    """Performs ``nexus3 cleanup_policy create``"""
    criteria = {}
    if args.get('--downloaded'):
        criteria['lastDownloaded'] = args.get('--downloaded')
    if args.get('--updated'):
        criteria['lastBlobUpdated'] = args.get('--updated')

    policy = cleanup_policy.CleanupPolicy(
        None,
        name=args.get('<policy_name>'),
        format=args.get('--format'),
        mode='delete',
        criteria=criteria,
    )

    nexus_client.cleanup_policies.create_or_update(policy)
    return errors.CliReturnCode.SUCCESS.value


def main(argv=None):
    """Entrypoint for ``nexus3 cleanup_policy`` subcommand."""
    arguments = docopt(__doc__, argv=argv)
    command_method = util.find_cmd_method(arguments, globals())
    return command_method(util.get_client(), arguments)
