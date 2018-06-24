import pytest

from nexuscli import exception, nexus_client


@pytest.mark.parametrize(
    'format_', nexus_client.SUPPORTED_FORMATS_FOR_UPLOAD + ['unsupported'])
def test_upload_file(format_, mocker, nexus_mock_client, file_upload_args):
    """
    Ensure the method calls the right upload method for the given repository
    format; also verify that an unsupported repository raises an exception.
    """
    x_method = '_upload_file_' + format_
    x_src_file, x_repo_name, x_dst_dir, x_dst_file = file_upload_args
    x_args = [x_src_file, x_repo_name, x_dst_dir, x_dst_file]

    nexus = nexus_mock_client
    x_values = nexus_mock_client._request.return_value._json

    # ensure a repo of the needed format exists
    x_values.append(
        pytest.helpers.nexus_repository(name=x_repo_name, format_=format_)
    )

    if format_ == 'unsupported':
        with pytest.raises(NotImplementedError):
            nexus.upload_file(*x_args)
    else:
        mocker.patch.object(nexus, x_method)
        nexus.upload_file(*x_args)
        x_method_object = getattr(nexus, x_method)

        x_method_object.assert_called_with(*x_args)


def test_upload_file_no_repository(faker, nexus_mock_client):
    """
    Ensure the method raises an error when the target repository doesn't exist.
    """
    x_missing_repo = faker.pystr()

    with pytest.raises(exception.NexusClientInvalidRepository) as e:
        nexus_mock_client.upload_file(
            faker.file_path(), x_missing_repo, faker.uri_path())

    assert x_missing_repo in str(e.value)


@pytest.mark.parametrize('dst_dir', [None, '/', '/anything', '/a/n/y/'])
def test_upload_file_raw_no_directory(
        dst_dir, mocker, faker, nexus_mock_client):
    """
    Ensure the method raises an error when the target directory isn't provided
    or starts with /.
    """
    nexus_mock_client.get_repository_by_name = mocker.Mock(
        return_value=pytest.helpers.nexus_repository(
            name=faker.uri_page(), format_='raw'))

    with pytest.raises(exception.NexusClientInvalidRepositoryPath) as e:
        nexus_mock_client.upload_file(faker.file_path(), 'dummy', dst_dir)

    assert 'Destination path does not contain a directory' in str(e.value)


def test_upload_file_yum_error(
        faker, nexus_mock_client, file_upload_args, tmpdir):
    """
    Ensure the method makes a PUT request passing the file data and that the
    status_code is checked for errors.
    """
    x_src_file, x_repo_name, x_dst_dir, x_dst_file = file_upload_args
    x_args = [x_src_file, x_repo_name, x_dst_dir, x_dst_file]
    x_content = faker.binary(length=100)
    x_values = nexus_mock_client._request.return_value
    x_values.status_code = 999
    # force name match on the first repo from the mocked object
    nexus_mock_client.repositories[0]['name'] = x_repo_name
    nexus_mock_client.repositories[0]['format'] = 'yum'

    with tmpdir.as_cwd():
        tmpdir.join(x_src_file).write(bytes(x_content), mode='wb', ensure=True)

        with pytest.raises(exception.NexusClientAPIError) as e:
            nexus_mock_client.upload_file(*x_args)

    nexus_mock_client._request.assert_called()
    assert x_repo_name in str(e.value)
    assert x_dst_dir in str(e.value)
    assert x_dst_file in str(e.value)
    assert x_values.reason in str(e.value)
