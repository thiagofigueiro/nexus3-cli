"""Handles base/root commands (as opposed to subcommands)"""
import inflect
import sys
import types

from nexuscli import exception, nexus_config
from nexuscli.nexus_client import NexusClient


PLURAL = inflect.engine().plural


def cmd_login(**kwargs):
    """Performs ``nexus3 login``"""
    config = nexus_config.NexusConfig(**kwargs)

    # make sure configuration works before saving
    try:
        NexusClient(config=config)
    except exception.NexusClientInvalidCredentials:
        # the regular message tells the user to try to login, which is what
        # they just did now, so override the msg
        raise exception.NexusClientInvalidCredentials('Invalid credentials')

    sys.stderr.write(f'\nLogin successful.\n')

    config.dump()
    sys.stderr.write(f'Configuration saved to {config.config_file}\n')

    return exception.CliReturnCode.SUCCESS.value


def cmd_list(nexus_client, repository_path):
    """Performs ``nexus3 list``"""
    artefact_list = nexus_client.list(repository_path)

    # FIXME: is types.GeneratorType still used?
    if isinstance(artefact_list, (list, types.GeneratorType)):
        for artefact in iter(artefact_list):
            print(artefact)
        return exception.CliReturnCode.SUCCESS.value
    else:
        return exception.CliReturnCode.UNKNOWN_ERROR.value


def _cmd_up_down_errors(count, action):
    """Print and exit with error if upload/download/delete didn't succeed"""
    if count == 0:
        # FIXME: inflex the action verb to past participle
        sys.stderr.write('WARNING: no files were {}\'ed.'.format(action))
        sys.exit(exception.CliReturnCode.NO_FILES.value)

    if count == -1:
        sys.stderr.write('ERROR during {} operation.'.format(action))
        sys.exit(exception.CliReturnCode.API_ERROR.value)


def cmd_upload(nexus_client, src=None, dst=None, flatten=None, recurse=None):
    """Performs ``nexus3 upload``"""
    sys.stderr.write(f'Uploading {src} to {dst}\n')

    upload_count = nexus_client.upload(
        src, dst, flatten=flatten, recurse=recurse)

    _cmd_up_down_errors(upload_count, 'upload')

    file = PLURAL('file', upload_count)
    sys.stderr.write(f'Uploaded {upload_count} {file} to {dst}\n')
    return exception.CliReturnCode.SUCCESS.value


def cmd_download(nexus_client, src=None, dst=None, flatten=None, cache=None):
    """Performs ``nexus3 download``"""
    sys.stderr.write(f'Downloading {src} to {dst}\n')

    download_count = nexus_client.download(
        src, dst, flatten=flatten, nocache=not cache)

    _cmd_up_down_errors(download_count, 'download')

    file_word = PLURAL('file', download_count)
    sys.stderr.write(
        f'Downloaded {download_count} {file_word} to {dst}\n')
    return exception.CliReturnCode.SUCCESS.value


def cmd_delete(nexus_client, repository_path):
    """Performs ``nexus3 delete``"""
    delete_count = nexus_client.delete(repository_path)

    _cmd_up_down_errors(delete_count, 'delete')

    file_word = PLURAL('file', delete_count)
    sys.stderr.write(f'Deleted {delete_count} {file_word}\n')
    return exception.CliReturnCode.SUCCESS.value
