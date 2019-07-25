"""
Usage:
  nexus3 script --help
  nexus3 script create <script_name> <script_path> [--script_type=<type>]
  nexus3 script list
  nexus3 script run <script_name> [<script_args>]
  nexus3 script (delete|del) <script_name>

Options:
  -h --help             This screen
  --script_type=<type>  Script type [default: groovy]

Commands:
  script create  Create or update a script using the <script_path> file
  script list    List all scripts available on the server
  script del     Remove existing <script_name>
  script run     Run the existing <script_name> with optional <script_args>
"""
from docopt import docopt
from texttable import Texttable

from nexuscli.cli import errors, util


def cmd_list(nexus_client, _):
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
    return errors.CliReturnCode.SUCCESS.value


def cmd_create(nexus_client, args):
    script_content = open(args.get('<script_path>')).read()
    nexus_client.scripts.create(
        args.get('<script_name>'), script_content, args.get('--script_type'))
    return errors.CliReturnCode.SUCCESS.value


def cmd_del(nexus_client, args):
    nexus_client.scripts.delete(args.get('<script_name>'))
    return errors.CliReturnCode.SUCCESS.value


def cmd_delete(nexus_client, args):
    return cmd_del(nexus_client, args)


def cmd_run(nexus_client, args):
    resp = nexus_client.scripts.run(
        args.get('<script_name>'), args.get('<script_args>'))
    print(resp)
    return errors.CliReturnCode.SUCCESS.value


def main(argv=None):
    arguments = docopt(__doc__, argv=argv)
    command_method = util.find_cmd_method(arguments, globals())
    return command_method(util.get_client(), arguments)
