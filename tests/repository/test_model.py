import itertools
import json
import pytest

from nexuscli import exception, repository
from nexuscli.repository import Repository


def test_collection_delete(nexus_mock_client, faker, mocker):
    """
    Ensure the delete method verifies the groovy script is in place and runs it
    with the name of the repository to be deleted as an argument
    """
    mocker.patch('nexuscli.nexus_client.ScriptCollection')
    x_name = faker.word()

    nexus_mock_client.repositories.delete(x_name)

    nexus_mock_client.scripts.create_if_missing.assert_called_once()
    nexus_mock_client.scripts.run.assert_called_with(
        'nexus3-cli-repository-delete', data=x_name)


def test_create_type_error(repository_collection, faker):
    with pytest.raises(TypeError):
        repository_collection.create(faker.pyiterable())


@pytest.mark.parametrize('repo_type', repository.validations.KNOWN_TYPES)
def test_create_repository_error(repo_type, repository_collection, mocker):
    mocker.patch('json.dumps')
    mocker.patch.object(
        repository.Repository, 'configuration',
        new_callable=mocker.PropertyMock)

    repo = repository.Repository(repo_type)

    with pytest.raises(exception.NexusClientCreateRepositoryError):
        repository_collection.create(repo)


@pytest.mark.parametrize('repo_type, response', itertools.product(
    repository.validations.KNOWN_TYPES,
    [{}, {'result': 'something'}, {'result': 'null'}]))
def test_create_repository(
        repo_type, response, nexus_mock_client, faker, mocker):
    """
    Ensure the delete method verifies the groovy script is in place and runs it
    with the configuration for the repository to be created as argument. Also
    test that the result is correctly interpreted for success/failure.
    """
    x_configuration = faker.pydict()
    mocker.patch('nexuscli.nexus_client.ScriptCollection')
    nexus_mock_client.scripts.run.return_value = response

    mocker.patch('json.dumps')
    json.dumps.return_value = x_configuration

    mocker.patch.object(
        repository.Repository, 'configuration',
        new_callable=mocker.PropertyMock, return_value=x_configuration)

    repo = repository.Repository(repo_type)

    if response.get('result') == 'null':
        nexus_mock_client.repositories.create(repo)
    else:
        with pytest.raises(exception.NexusClientCreateRepositoryError):
            nexus_mock_client.repositories.create(repo)

    nexus_mock_client.scripts.create_if_missing.assert_called_once()
    json.dumps.assert_called_with(repo.configuration)
    nexus_mock_client.scripts.run.assert_called_with(
        'nexus3-cli-repository-create', data=json.dumps.return_value)


def test_refresh_repositories(nexus_mock_client):
    """
    Ensure the method retrieves latest repositories and sets the class
    attribute.
    """
    repositories = nexus_mock_client.repositories.raw_list()
    x_repositories = nexus_mock_client._request.return_value._json

    nexus_mock_client._request.assert_called_with(
        'get', 'repositories', stream=True)
    assert repositories == x_repositories


def test_refresh_repositories_error(nexus_mock_client):
    """
    Ensure the method does't modify the existing repositories attribute when
    the client request fails.
    """
    nexus_mock_client._request.return_value.status_code = 400
    nexus_mock_client.repositories._repositories_json = None

    with pytest.raises(exception.NexusClientAPIError):
        nexus_mock_client.repositories.refresh()

    assert nexus_mock_client.repositories._repositories_json is None


@pytest.mark.parametrize('x_found', [True, False])
def test_get_repository_by_name(
        x_found, nexus_mock_client, faker):
    """Ensure the method returns a repo found by name or raises an exception"""
    nexus = nexus_mock_client
    x_name = faker.pystr()
    x_format = faker.pystr()
    x_repo = None
    x_values = nexus_mock_client._request.return_value._json

    if x_found:
        x_repo = pytest.helpers.nexus_repository(x_name, x_format)
        x_values.append(x_repo)

    nexus.repositories.refresh()

    if x_found:
        assert nexus.repositories.get_raw_by_name(x_name) == x_repo
        assert nexus.repositories.get_raw_by_name(x_name)['name'] == x_name
        assert nexus.repositories.get_raw_by_name(x_name)['format'] == x_format
    else:
        with pytest.raises(IndexError):
            nexus.repositories.get_raw_by_name(x_name)


@pytest.mark.parametrize('format_', Repository.SUPPORTED_FORMATS_FOR_UPLOAD)
def test_upload_file(format_, mocker, nexus_mock_client, file_upload_args):
    """
    Ensure the method calls the right upload method for the given repository
    format; also verify that an unsupported repository raises an exception.
    """
    x_method = '_upload_file_' + format_
    mocker.patch('nexuscli.repository.Repository.' + x_method)
    x_src_file, x_repo_name, x_dst_dir, x_dst_file = file_upload_args
    x_args = [x_src_file, x_dst_dir, x_dst_file]

    x_values = nexus_mock_client._request.return_value._json

    # ensure a repo of the needed format exists
    x_values.append(
        pytest.helpers.nexus_repository(name=x_repo_name, format_=format_)
    )

    r = nexus_mock_client.repositories.get_by_name(x_repo_name)
    x_method_object = getattr(r, x_method)

    r.upload_file(*x_args)

    x_method_object.assert_called_with(*x_args)


def test_upload_file_unsupported(nexus_raw_repo, faker):
    """
    Ensure the method calls the right upload method for the given repository
    format; also verify that an unsupported repository raises an exception.
    """
    repo_format = faker.pystr()  # won't match supported formats
    assert repo_format not in Repository.SUPPORTED_FORMATS_FOR_UPLOAD  # JIC

    # change repo format to the unsupported format above
    nexus_raw_repo._raw['format'] = repo_format

    with pytest.raises(NotImplementedError):
        nexus_raw_repo.upload_file(faker.file_name(), faker.uri_path())


@pytest.mark.parametrize('dst_dir', [None, '/', '/anything', '/a/n/y/'])
def test_upload_file_raw_no_directory(dst_dir, faker, nexus_raw_repo):
    """
    Ensure the method raises an error when the target directory isn't provided
    or starts with /.
    """
    with pytest.raises(exception.NexusClientInvalidRepositoryPath) as e:
        nexus_raw_repo.upload_file(faker.file_path(), dst_dir)

    assert 'Destination path does not contain a directory' in str(e.value)


def test_upload_file_yum_error(
        faker, nexus_yum_repo, file_upload_args, tmpdir):
    """
    Ensure the method makes a PUT request passing the file data and that the
    status_code is checked for errors.
    """
    x_src_file, _, x_dst_dir, x_dst_file = file_upload_args
    x_args = [x_src_file, x_dst_dir, x_dst_file]
    x_content = faker.binary(length=100)
    x_values = nexus_yum_repo._client._request.return_value
    x_values.status_code = 999

    with tmpdir.as_cwd():
        tmpdir.join(x_src_file).write(bytes(x_content), mode='wb', ensure=True)

        with pytest.raises(exception.NexusClientAPIError) as e:
            nexus_yum_repo.upload_file(*x_args)

    nexus_yum_repo._client._request.assert_called()
    assert nexus_yum_repo.name in str(e.value)
    assert x_dst_dir in str(e.value)
    assert x_dst_file in str(e.value)
    assert x_values.reason in str(e.value)
