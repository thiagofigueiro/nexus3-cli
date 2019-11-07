"""Methods to implement upload for specific repository formats (recipes)"""
import os

from nexuscli import exception
from nexuscli.api.repository.validations import REMOTE_PATH_SEPARATOR


def upload_file_raw(repository, src_file, dst_dir, dst_file):
    """
    Upload a single file to a raw repository.

    :param repository: repository instance used to access Nexus 3 service.
    :type repository: nexuscli.api.repository.model.Repository
    :param src_file: path to the local file to be uploaded.
    :param dst_dir: directory under dst_repo to place file in. When None,
        the file is placed under the root of the raw repository
    :param dst_file: destination file name.
    :raises exception.NexusClientInvalidRepositoryPath: invalid repository
        path.
    :raises exception.NexusClientAPIError: unknown response from Nexus API.
    """
    dst_dir = os.path.normpath(dst_dir or REMOTE_PATH_SEPARATOR)

    params = {'repository': repository.name}
    files = {'raw.asset1': open(src_file, 'rb').read()}
    data = {
        'raw.directory': dst_dir,
        'raw.asset1.filename': dst_file,
    }

    response = repository.nexus_client.http_post(
        'components', files=files, data=data, params=params, stream=True)

    if response.status_code != 204:
        raise exception.NexusClientAPIError(
            f'Uploading to {repository.name}. Reason: {response.reason}')


def upload_file_yum(repository, src_file, dst_dir, dst_file):
    """
    Upload a single file to a yum repository.

    :param repository: repository instance used to access Nexus 3 service.
    :type repository: nexuscli.api.repository.model.Repository
    :param src_file: path to the local file to be uploaded.
    :param dst_dir: directory under dst_repo to place file in.
    :param dst_file: destination file name.
    :raises exception.NexusClientAPIError: unknown response from Nexus API.
    """
    dst_dir = dst_dir or REMOTE_PATH_SEPARATOR
    repository_path = REMOTE_PATH_SEPARATOR.join(
        ['repository', repository.name, dst_dir, dst_file])

    with open(src_file, 'rb') as fh:
        response = repository.nexus_client.http_put(
            repository_path, data=fh, stream=True,
            service_url=repository.nexus_client.config.url)

    if response.status_code != 200:
        raise exception.NexusClientAPIError(
            f'Uploading to {repository_path}. Reason: {response.reason}')
