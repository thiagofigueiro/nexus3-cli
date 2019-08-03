"""Handles base/root commands (as opposed to subcommands)"""
import getpass
import inflect
import sys
import types
from nexuscli import nexus_config
from nexuscli.nexus_client import NexusClient
from nexuscli.cli import errors, util


PLURAL = inflect.engine().plural
YESNO_OPTIONS = {
    "true": True, "t": True, "yes": True, "y": True,
    "false": False, "f": False, "no": False, "n": False,
}


def _input_yesno(prompt, default):
    """
    Prompts for a yes/true/no/false answer.

    :param prompt: question to be displayed to user
    :param default: default choice, also used for invalid answers
    :return: choice
    :rtype: bool
    """
    try:
        return YESNO_OPTIONS[util.input_with_default(prompt, default).lower()]
    except KeyError:
        return default


def cmd_login(_, __):
    """Performs ``nexus3 login``"""
    nexus_url = util.input_with_default(
        'Nexus OSS URL', nexus_config.DEFAULTS['url'])
    nexus_user = util.input_with_default(
        'Nexus admin username', nexus_config.DEFAULTS['username'])
    nexus_pass = getpass.getpass(
        prompt=f'Nexus admin password ({nexus_config.DEFAULTS["password"]}):')
    if not nexus_pass:
        nexus_pass = nexus_config.DEFAULTS['password']

    nexus_verify = _input_yesno(
        'Verify server certificate', nexus_config.DEFAULTS['x509_verify'])

    config = nexus_config.NexusConfig(
        username=nexus_user, password=nexus_pass, url=nexus_url,
        x509_verify=nexus_verify)

    # make sure configuration works before saving
    NexusClient(config=config)

    config.dump()

    sys.stderr.write(f'\nConfiguration saved to {config.config_file}\n')


def cmd_list(nexus_client, args):
    """Performs ``nexus3 list``"""
    repository_path = args['<repository_path>']
    artefact_list = nexus_client.list(repository_path)

    # FIXME: is types.GeneratorType still used?
    if isinstance(artefact_list, (list, types.GeneratorType)):
        for artefact in iter(artefact_list):
            print(artefact)
        return errors.CliReturnCode.SUCCESS.value
    else:
        return errors.CliReturnCode.UNKNOWN_ERROR.value


def cmd_ls(*args, **kwargs):
    """Alias for :func:`cmd_list`"""
    return cmd_list(*args, **kwargs)


def _cmd_up_down_errors(count, action):
    """Print and exit with error if upload/download/delete didn't succeed"""
    if count == 0:
        # FIXME: inflex the action verb to past participle
        sys.stderr.write('WARNING: no files were {}\'ed.'.format(action))
        sys.exit(errors.CliReturnCode.NO_FILES.value)

    if count == -1:
        sys.stderr.write('ERROR during {} operation.'.format(action))
        sys.exit(errors.CliReturnCode.API_ERROR.value)


def cmd_upload(nexus_client, args):
    """Performs ``nexus3 upload``"""
    source = args['<from_src>']
    destination = args['<to_repository>']

    sys.stderr.write(f'Uploading {source} to {destination}\n')

    upload_count = nexus_client.upload(
                    source, destination,
                    flatten=args.get('--flatten'),
                    recurse=(not args.get('--norecurse')))

    _cmd_up_down_errors(upload_count, 'upload')

    file = PLURAL('file', upload_count)
    sys.stderr.write(f'Uploaded {upload_count} {file} to {destination}\n')
    return errors.CliReturnCode.SUCCESS.value


def cmd_up(*args, **kwargs):
    """Alias for :func:`cmd_upload`"""
    return cmd_upload(*args, **kwargs)


def cmd_download(nexus_client, args):
    """Performs ``nexus3 download``"""
    source = args['<from_repository>']
    destination = args['<to_dst>']

    sys.stderr.write(f'Downloading {source} to {destination}\n')

    download_count = nexus_client.download(
                        source, destination,
                        flatten=args.get('--flatten'),
                        nocache=args.get('--nocache'))

    _cmd_up_down_errors(download_count, 'download')

    file_word = PLURAL('file', download_count)
    sys.stderr.write(
        f'Downloaded {download_count} {file_word} to {destination}\n')
    return errors.CliReturnCode.SUCCESS.value


def cmd_dl(*args, **kwargs):
    """Alias for :func:`cmd_download`"""
    return cmd_download(*args, **kwargs)


def cmd_delete(nexus_client, options):
    """Performs ``nexus3 delete``"""
    repository_path = options['<repository_path>']
    delete_count = nexus_client.delete(repository_path)

    _cmd_up_down_errors(delete_count, 'delete')

    file_word = PLURAL('file', delete_count)
    sys.stderr.write(f'Deleted {delete_count} {file_word}\n')
    return errors.CliReturnCode.SUCCESS.value


def cmd_del(*args, **kwargs):
    """Alias for :func:`cmd_delete`"""
    return cmd_delete(*args, **kwargs)
