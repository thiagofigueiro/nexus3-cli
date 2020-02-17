from texttable import Texttable

from nexuscli import exception
from nexuscli.api import cleanup_policy
from nexuscli.cli import util


def cmd_list(nexus_client):
    """Performs ``nexus3 cleanup_policy list``"""
    policies = nexus_client.cleanup_policies.list()
    if len(policies) == 0:
        return exception.CliReturnCode.POLICY_NOT_FOUND.value

    table = Texttable(max_width=util.TTY_MAX_WIDTH)
    table.add_row(
        ['Name', 'Format', 'Downloaded', 'Updated', 'Regex'])
    table.set_deco(Texttable.HEADER)
    for policy in policies:
        p = policy.configuration
        table.add_row([
            p['name'], p['format'],
            p['criteria'].get('lastDownloaded', 'null'),
            p['criteria'].get('lastBlobUpdated', 'null'),
            p['criteria'].get('regex', 'null')],
        )

    print(table.draw())
    return exception.CliReturnCode.SUCCESS.value


def cmd_create(nexus_client, **kwargs):
    """Performs ``nexus3 cleanup_policy create``"""
    policy = cleanup_policy.CleanupPolicy(None, **kwargs)
    nexus_client.cleanup_policies.create_or_update(policy)

    return exception.CliReturnCode.SUCCESS.value
