import pytest

from nexuscli import exception
from nexuscli.api.repository import upload

SEP = upload.REMOTE_PATH_SEPARATOR  # for shorter lines in the tests


@pytest.mark.parametrize('dst_dir', [
    None, SEP, f'{SEP}anything', f'{SEP}a{SEP}n{SEP}y{SEP}'])
def test_upload_file_raw_invalid(dst_dir):
    """Ensure the method raises an exception when dst_dir is invalid"""
    with pytest.raises(exception.NexusClientInvalidRepositoryPath):
        upload.upload_file_raw(None, None, dst_dir, None)


def test_upload_file_raw_error(mocker, tmpdir, faker):
    """Ensure the method raises an exception when the API response is wrong"""
    dst_dir = upload.REMOTE_PATH_SEPARATOR.join(faker.words())
    repository = mocker.Mock()
    src_file = tmpdir.join(faker.file_name()).ensure()

    with pytest.raises(exception.NexusClientAPIError):
        upload.upload_file_raw(repository, src_file, dst_dir, None)

    repository.nexus_client.http_post.assert_called_once()


def test_upload_file_yum_error(mocker, tmpdir, faker):
    """
    Ensure the method makes a PUT request and raises an exception when the API
    response is wrong
    """
    repository = mocker.Mock()
    repository.name = faker.word()
    src_file = tmpdir.join(faker.file_name()).ensure()

    with pytest.raises(exception.NexusClientAPIError):
        upload.upload_file_yum(
            repository, src_file, faker.file_path(), faker.file_path())

    repository.nexus_client.http_put.assert_called_once()
