import itertools
import pytest
from semver import VersionInfo

from nexuscli.api.repository import model


@pytest.mark.parametrize(
    'repo_class',
    pytest.helpers.repositories_by_type(['hosted', 'proxy', 'group']))
def test_repository_recipe(repo_class, faker):
    """
    For repository classes that accept multiple recipes, ensure the recipe
    given is supported. For other repositories, ensure the recipe given is
    ignored.
    """
    accepts_multiple = bool((len(repo_class.RECIPES)-1))
    missing_recipe = faker.pystr()

    # TODO: DRY-UP this pattern
    kwargs = {'recipe': missing_recipe}
    if repo_class.TYPE == 'proxy':
        kwargs['remote_url'] = faker.url()

    if accepts_multiple:
        with pytest.raises(ValueError):
            repo_class(faker.word(), **kwargs)
    else:
        repo = repo_class(faker.word(), **kwargs)
        assert repo.recipe_name != missing_recipe


@pytest.mark.parametrize(
    'repo_class', pytest.helpers.repositories_by_type('hosted'))
def test_upload_file(repo_class, mocker, file_upload_args, faker):
    """
    Ensure all hosted repositories have an upload_file method that calls the
    right helper from the upload module.
    """
    src_file, _, dst_dir, dst_file = file_upload_args

    repo = repo_class(faker.word())

    x_upload_method_name = f'upload_file_{repo.recipe_name}'
    upload_method = mocker.Mock()
    # inject mock upload method into upload module
    mock_upload = mocker.patch('nexuscli.api.repository.model.upload')
    mocker.patch.object(mock_upload, x_upload_method_name, upload_method)

    repo.upload_file(src_file, dst_dir, dst_file)

    upload_method.assert_called_with(repo, src_file, dst_dir, dst_file)


@pytest.mark.parametrize(
    'repo_class', pytest.helpers.repositories_by_type(['proxy', 'group']))
def test_upload_missing(repo_class, faker):
    """
    Ensure that no proxy, group repositories have upload_* methods
    """
    kwargs = {}
    if repo_class.TYPE == 'proxy':
        kwargs['remote_url'] = faker.url()

    repo = repo_class(faker.word(), **kwargs)

    with pytest.raises(AttributeError):
        repo.upload_file()

    with pytest.raises(AttributeError):
        repo.upload_directory()


@pytest.mark.parametrize(
    'repo_class, recurse, flatten', itertools.product(
        pytest.helpers.repositories_by_type('hosted'),  # repo_class
        [True, False],                                  # recurse
        [True, False]))                                 # flatten
def test_upload_directory(repo_class, recurse, flatten, mocker, faker):
    """
    Ensure the method calls upload_file with parameters based on the quantity
    of files in a given directory.
    """
    src_dir = model.upload.REMOTE_PATH_SEPARATOR.join(faker.words())
    dst_dir = model.upload.REMOTE_PATH_SEPARATOR.join(faker.words())
    x_subdirectory = faker.pystr()
    x_file_path = faker.pystr()

    util = mocker.patch('nexuscli.api.repository.model.util')
    util.get_files.return_value = faker.pylist(10, True, str)
    util.get_upload_subdirectory.return_value = x_subdirectory
    mocker.patch('os.path.join', return_value=x_file_path)

    x_get_upload_subdirectory_calls = [
        mocker.call(dst_dir, x_file_path, flatten)
        for _ in util.get_files.return_value  # just need the count of calls
    ]

    repo = repo_class(faker.word())
    repo.upload_file = mocker.Mock()

    repo.upload_directory(src_dir, dst_dir, recurse=recurse, flatten=flatten)

    util.get_files.assert_called_with(src_dir, recurse)
    util.get_upload_subdirectory.assert_has_calls(
        x_get_upload_subdirectory_calls)
    repo.upload_file.assert_called_with(x_file_path, x_subdirectory)


@pytest.mark.parametrize(
    'repo_class',
    pytest.helpers.repositories_by_type(['hosted', 'proxy', 'group']))
def test_repository_configuration(
        repo_class, mock_nexus_client, faker, gpg_key_as_cwd):
    x_name = faker.word()
    x_cleanup_policy = faker.word()
    x_blob_store_name = faker.word()
    x_remote_url = faker.url()
    x_strict = faker.pybool()

    kwargs = {
        'nexus_client': mock_nexus_client,
        'cleanup_policy': x_cleanup_policy,
        'blob_store_name': x_blob_store_name,
        'strict_content_type_validation': x_strict,
    }

    if repo_class.TYPE == 'proxy':
        kwargs['remote_url'] = x_remote_url

    repo = repo_class(x_name, **kwargs)
    configuration = repo.configuration
    attributes = configuration['attributes']

    assert configuration['name'] == x_name
    assert attributes['cleanup']['policyName'] == [x_cleanup_policy]
    assert attributes['storage']['blobStoreName'] == x_blob_store_name
    assert attributes['storage']['strictContentTypeValidation'] == x_strict

    if repo.TYPE and repo.TYPE == 'proxy':
        assert attributes['proxy']['remoteUrl'] == x_remote_url


@pytest.mark.parametrize(
    'yum_repo',
    pytest.helpers.yum_repos()
)
def test_yum_repository_configuration(yum_repo, mock_nexus_client, faker):
    x_name = faker.word()
    x_depth = faker.pyint()

    kwargs = {
        'nexus_client': mock_nexus_client,
        'depth': x_depth
    }

    if yum_repo.TYPE == 'proxy':
        kwargs['remote_url'] = faker.url()

    repo = yum_repo(x_name, **kwargs)

    assert repo.configuration['attributes']['yum']['repodataDepth'] == x_depth


@pytest.mark.parametrize('version,xpolicy', [
    (None, lambda x: [x]),
    (model.CLEANUP_SET_MIN_VERSION, lambda x: [x]),
    (VersionInfo(0, 0, 0), lambda x: x)
])
def test_cleanup_policy(version, xpolicy, mocker, mock_nexus_client, faker):
    """
    From CLEANUP_SET_MIN_VERSION, Nexus takes a set of policy names instead
    of a single policy. Ensure the method returns the right type according to
    the version.
    https://github.com/thiagofigueiro/nexus3-cli/issues/77
    """
    policy = faker.word()

    mock_nexus_client.server_version = version
    repository = model.Repository(
        'myrepo', nexus_client=mock_nexus_client, cleanup_policy=policy)

    assert repository.cleanup_policy == xpolicy(policy)
