from texttable import Texttable

from nexuscli import exception
from nexuscli.cli import util


def cmd_list(nexus_client):
    """Performs ``nexus3 script list``"""
    scripts = nexus_client.scripts.list()

    table = Texttable(max_width=util.TTY_MAX_WIDTH)
    table.add_row(['Name', 'Type', 'Content'])
    table.set_deco(Texttable.HEADER | Texttable.HLINES)
    for script in scripts:
        content = script['content']
        if len(content) > 40:
            content = f'{content[:40]}...'
        table.add_row([script['name'], script['type'], content])

    print(table.draw())
    return exception.CliReturnCode.SUCCESS.value


def cmd_create(nexus_client, name, content, **kwargs):
    """Performs ``nexus3 script create``"""
    nexus_client.scripts.create(name, content, **kwargs)
    return exception.CliReturnCode.SUCCESS.value


def cmd_delete(nexus_client, name):
    """Performs ``nexus3 script delete``"""
    nexus_client.scripts.delete(name)
    return exception.CliReturnCode.SUCCESS.value


def cmd_run(nexus_client, name, arguments):
    """Performs ``nexus3 script run``"""
    resp = nexus_client.scripts.run(name, arguments)
    print(resp)
    return exception.CliReturnCode.SUCCESS.value
