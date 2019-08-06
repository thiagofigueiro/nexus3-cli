import pytest

from nexuscli import exception
from nexuscli.api import repository
from nexuscli.api.repository.model import upload


@pytest.mark.parametrize('repo_class', repository.model.__all__)
def test_upload_file(repo_class, mocker, file_upload_args, faker):
    """
    Ensure the method calls the right upload method for the given repository
    """
    src_file = upload.REMOTE_PATH_SEPARATOR.join(faker.words())
    dst_dir = upload.REMOTE_PATH_SEPARATOR.join(faker.words())
    dst_file = faker.word()

    kwargs = {}
    if repo_class.TYPE == 'proxy':
        kwargs['remote_url'] = faker.url()

    repo = repo_class(faker.word(), **kwargs)

    x_upload_method_name = f'upload_file_{repo.recipe_name}'
    upload_method = mocker.Mock()
    # inject mock upload method into upload module
    setattr(upload, x_upload_method_name, upload_method)

    repo.upload_file(src_file, dst_dir, dst_file)

    upload_method.assert_called_with(repo, src_file, dst_dir, dst_file)


@pytest.mark.skip('needs refactoring')
def test_upload_file_unsupported(nexus_raw_repo, faker):
    """
    Ensure the method calls the right upload method for the given repository
    format; also verify that an unsupported repository raises an exception.
    """
    repo_format = faker.pystr()  # won't match supported formats
    # Just in case
    assert repo_format not in LegacyRepository.SUPPORTED_FORMATS_FOR_UPLOAD

    # change repo format to the unsupported format above
    nexus_raw_repo._raw['format'] = repo_format

    with pytest.raises(NotImplementedError):
        nexus_raw_repo.upload_file(faker.file_name(), faker.uri_path())


@pytest.mark.parametrize('dst_dir', [None, '/', '/anything', '/a/n/y/'])
@pytest.mark.skip('needs refactoring')
def test_upload_file_raw_no_directory(dst_dir, faker, nexus_raw_repo):
    """
    Ensure the method raises an error when the target directory isn't provided
    or starts with /.
    """
    with pytest.raises(exception.NexusClientInvalidRepositoryPath) as e:
        nexus_raw_repo.upload_file(faker.file_path(), dst_dir)

    assert 'Destination path does not contain a directory' in str(e.value)


@pytest.mark.skip('needs refactoring')
def test_upload_file_yum_error(
        faker, nexus_yum_repo, file_upload_args, tmpdir):
    """
    Ensure the method makes a PUT request passing the file data and that the
    status_code is checked for errors.
    """
    x_src_file, _, x_dst_dir, x_dst_file = file_upload_args
    x_args = [x_src_file, x_dst_dir, x_dst_file]
    x_content = faker.binary(length=100)
    x_values = nexus_yum_repo._client.http_request.return_value
    x_values.status_code = 999

    with tmpdir.as_cwd():
        tmpdir.join(x_src_file).write(bytes(x_content), mode='wb', ensure=True)

        with pytest.raises(exception.NexusClientAPIError) as e:
            nexus_yum_repo.upload_file(*x_args)

    nexus_yum_repo._client.http_request.assert_called()
    assert nexus_yum_repo.name in str(e.value)
    assert x_dst_dir in str(e.value)
    assert x_dst_file in str(e.value)
    assert x_values.reason in str(e.value)
