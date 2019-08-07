import os

from nexuscli.api.repository.validations import REMOTE_PATH_SEPARATOR


def get_files(src_dir, recurse=True):
    """
    Walks the given directory and collects files to be uploaded. If
    recurse option is False, only the files on the root of the directory
    will be returned.

    :param src_dir: location of files
    :param recurse: If false, only the files on the root of src_dir
                    are returned
    :return: file set to be used with upload_directory
    :rtype: set
    """
    source_files = set()
    for dirname, dirnames, filenames in os.walk(src_dir):
        if not recurse:
            del dirnames[:]

        source_files.update(
            os.path.relpath(os.path.join(dirname, f), src_dir)
            for f in filenames)

    return source_files


def get_upload_subdirectory(dst_dir, file_path, flatten=False):
    """
    Find the destination subdirectory based on given parameters. This is mostly
    so the `flatten` option is honoured.

    :param dst_dir: destination directory
    :param file_path: file path, using REMOTE_PATH_SEPARATOR as the directory
        separator.
    :param flatten: when True, sub_directory will be flattened (ie: file_path
        structure will not be present in the destination directory)
    :type flatten: bool
    :return: the appropriate sub directory in the destination directory.
    :rtype: str
    """
    # empty dst_dir because most repo formats, aside from raw, allow it
    sub_directory = dst_dir or ''
    if flatten:
        return sub_directory

    sep = REMOTE_PATH_SEPARATOR
    dirname = os.path.dirname(file_path)
    if sub_directory.endswith(sep) or dirname.startswith(sep):
        sep = ''
    sub_directory += f'{sep}{dirname}'

    return sub_directory
