import click
import functools
import os
import sys
from subprocess import CalledProcessError

from nexuscli.nexus_client import NexusClient
from nexuscli.nexus_config import NexusConfig


try:
    _, TTY_MAX_WIDTH = os.popen('stty size', 'r').read().split()
    TTY_MAX_WIDTH = int(TTY_MAX_WIDTH)
except (ValueError, CalledProcessError):
    TTY_MAX_WIDTH = 80


class AliasedGroup(click.Group):
    """
    Implements execution of the first partial match for a command. Fails with a
    message if there are no unique matches.

    See: https://click.palletsprojects.com/en/7.x/advanced/#command-aliases
    """
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


def with_nexus_client(click_command):
    @functools.wraps(click_command)
    @click.pass_context
    def command(ctx: click.Context, **kwargs):
        ctx.obj = get_client()
        return click_command(ctx, **kwargs)

    return command


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


def mapped_commands(command_map: dict):
    """
    TODO: document command_map format

    :param command_map:
    :return:
    """
    class CommandGroup(click.Group):
        def get_command(self, ctx, cmd_name):
            for real_command, aliases in command_map.items():
                if cmd_name in aliases:
                    return click.Group.get_command(self, ctx, real_command)
            return None

        def list_commands(self, ctx):
            return [a for b in command_map.values() for a in b]

    return CommandGroup


def upcase_values(mydict: dict, keys=[]):
    for key in keys:
        value = mydict.get(key)
        if value is not None:
            mydict[key] = value.upper()


def rename_keys(mydict: dict, rename_map: dict):
    for current_name, new_name in rename_map.items():
        if mydict.get(current_name) is not None:
            mydict[new_name] = mydict[current_name]
            del mydict[current_name]


def find_cmd_method(arguments, methods):
    """
    Helper to find the corresponding python method for a CLI command.

    Suitable python methods must be named ``cmd_COMMAND``, where `COMMAND` is
    the CLI command and ``cmd_`` is a hard-coded prefix.

    :param arguments: the return of :py:func:`docopt.docopt`.
    :param methods: the return value from `globals()`, as-is
    :return: the python method corresponding to the given CLI command. None if
        no suitable method is found.
    :rtype: Union[callable, None]
    """
    methods = dict(methods)
    for name, method in methods.items():
        if name.startswith('cmd_'):
            maybe_command = name[4:]  # strip `cmd_`
            if arguments.get(maybe_command):
                return method
    return None


def get_client():
    """
    Returns a Nexus Client instance. Prints a warning if a configuration file
    isn't file.

    :rtype: nexuscli.nexus_client.NexusClient
    """
    config = NexusConfig()
    try:
        config.load()
    except FileNotFoundError:
        sys.stderr.write(
            'Warning: configuration not found; proceeding with defaults.\n'
            'To remove this warning, please run `nexus3 login`\n')
    return NexusClient(config=config)


def input_with_default(prompt, default=None):
    """
    Prompts for a text answer with an optional default choice.

    :param prompt: question to be displayed to user
    :param default: default choice
    :return: user-provided answer or None, if default not provided.
    :rtype: Union[str,None]
    """
    value = input(f'{prompt} ({default}):')
    if value:
        return str(value)

    return str(default)
