import os
import pytest
import time

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


def test_upload_directory(faker, mocker, nexus_mock_client, deep_file_tree):
    """
    Ensure the method calls the upload_file method for every file found in the
    given source directory with the correct arguments.
    """
    # _get_upload_subdirectory is tested somewhere else
    x_subdir = faker.pystr()
    nexus_mock_client._get_upload_subdirectory = mocker.Mock(
        return_value=x_subdir)

    x_src_dir, x_file_set = deep_file_tree
    # ensure the repo exists
    x_dst_repo = nexus_mock_client.repositories[0]['name']
    x_dst_dir = faker.uri_path()

    # these are used to verify all the calls made to upload_file
    upload_calls = []
    x_upload_calls = []
    for f in x_file_set:
        x_src_file = os.path.join(x_src_dir, f)
        x_upload_calls.append(tuple([x_src_file, x_dst_repo, x_subdir]))

    # this side-effect of calling upload_file collects the arguments used for
    # later comparison with x_upload_calls
    def upload_file_collect(*args):
        upload_calls.append(tuple(args))

    upload_file_mock = mocker.Mock(side_effect=upload_file_collect)
    mocker.patch.object(nexus_mock_client, 'upload_file', new=upload_file_mock)

    file_count = nexus_mock_client.upload_directory(
        x_src_dir, x_dst_repo, x_dst_dir)

    assert file_count == len(x_file_set)
    nexus_mock_client.upload_file.assert_called()
    assert sorted(upload_calls) == sorted(x_upload_calls)


@pytest.mark.integration
def test_upload_tree(nexus_client, deep_file_tree, faker):
    """
    Create a repository, upload a random file tree to Nexus and check that the
    resulting list of files in nexus corresponds to the uploaded list of files.
    """
    src_dir, x_file_set = deep_file_tree
    repo_name = faker.word()
    dst_dir = faker.uri_path() + '/'
    repo_path = dst_dir[:-1] + src_dir

    argv = ('repo create hosted raw {}'.format(repo_name)).split()
    pytest.helpers.create_and_inspect(argv, repo_name)
    nexus_client.refresh_repositories()

    upload_count = nexus_client.upload_directory(src_dir, repo_name, dst_dir)
    # is looks like nexus needs time to index uploaded files :-/
    time.sleep(1)
    file_set = nexus_client.list(repo_name)

    my_upload_count = 0
    for f in iter(file_set):
        my_upload_count += 1
        assert f[len(repo_path)+1:] in x_file_set
    assert upload_count == my_upload_count
    assert upload_count == len(x_file_set)
