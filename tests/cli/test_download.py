import itertools
import os
import pytest

from faker import Faker


@pytest.mark.parametrize('flatten, remote, destination, x_local_path', [
    # no rename (file to dir)
    (False, 'file', '.',            '_TMP_file'),
    (False, 'file', './',           '_TMP_file'),
    (False, 'file', '..',           '_TMP_../file'),
    (False, 'file', '../',          '_TMP_../file'),
    (False, 'file', '/',            '/file'),
    (False, 'file', '/dir/',        '/dir/file'),
    (False, 'file', 'dir/',         '_TMP_dir/file'),
    (False, 'file', 'dir/sub/',     '_TMP_dir/sub/file'),
    (False, 'file', '/dir/sub/',    '/dir/sub/file'),

    # rename (file to file)
    (False, 'file', 'file2',        '_TMP_file2'),
    (False, 'file', './file2',      '_TMP_file2'),
    (False, 'file', '/file2',       '/file2'),
    (False, 'file', '/dir/file2',   '/dir/file2'),
    (False, 'file', 'dir/file2',    '_TMP_dir/file2'),

    # remote has directory, no rename
    (False, 'dir/file', '.',         '_TMP_dir/file'),
    (True,  'dir/file', '.',         '_TMP_file'),
    (False, 'dir/file', './',        '_TMP_dir/file'),
    (True,  'dir/file', './',        '_TMP_file'),
    (False, 'dir/file', '..',        '_TMP_../dir/file'),
    (True,  'dir/file', '..',        '_TMP_../file'),
    (False, 'dir/file', '../',       '_TMP_../dir/file'),
    (True,  'dir/file', '../',       '_TMP_../file'),
    (False, 'dir/file', '/',         '/dir/file'),
    (True,  'dir/file', '/',         '/file'),
    (False, 'dir/file', '/dir/',     '/dir/dir/file'),
    (True,  'dir/file', '/dir/',     '/dir/file'),
    (False, 'dir/file', 'dir/',      '_TMP_dir/dir/file'),
    (True,  'dir/file', 'dir/',      '_TMP_dir/file'),
    (False, 'dir/file', 'dir/sub/',  '_TMP_dir/sub/dir/file'),
    (True,  'dir/file', 'dir/sub/',  '_TMP_dir/sub/file'),
    (False, 'dir/file', '/dir/sub/', '/dir/sub/dir/file'),
    (True,  'dir/file', '/dir/sub/', '/dir/sub/file'),

    # remote has directory, rename
    (False, 'dir1/file', 'file2',      '_TMP_dir1/file2'),
    (True,  'dir1/file', 'file2',       '_TMP_file2'),
    (False, 'dir1/file', './file2',     '_TMP_dir1/file2'),
    (True,  'dir1/file', './file2',     '_TMP_file2'),
    (False, 'dir1/file', '/file2',      '/dir1/file2'),
    (True,  'dir1/file', '/file2',      '/file2'),
    (False, 'dir1/file', '/dir2/file2', '/dir2/dir1/file2'),
    (True,  'dir1/file', '/dir2/file2', '/dir2/file2'),
    (False, 'dir1/file', 'dir2/file2',  '_TMP_dir2/dir1/file2'),
    (True,  'dir1/file', 'dir2/file2',  '_TMP_dir2/file2'),
])
def test__remote_path_to_local(
        flatten, remote, destination, x_local_path, nexus_mock_client, tmpdir):
    """
    Ensure the method correctly resolves a remote path to a local destination,
    following the instance setting for flatten.
    """
    nexus = nexus_mock_client

    FLATTEN = flatten

    # add cwd to expected result as the fixture gives it as relative but the
    # method always returns an absolute path
    if x_local_path.find('_TMP_') == 0:
        x_local_path = x_local_path.replace('_TMP_', str(tmpdir) + os.path.sep)

    with tmpdir.as_cwd():
        local_path = nexus._remote_path_to_local(
            remote, destination, FLATTEN, create=False)

    assert local_path == os.path.realpath(x_local_path)


@pytest.mark.parametrize('is_dst_dir, flatten',
                         ([False, True], [False, True]))
def test__remote_path_to_create(
        flatten, is_dst_dir, nexus_mock_client, tmpdir):
    """
    Ensure the method correctly resolves a remote path to a local destination,
    following the instance setting for flatten.
    """
    nexus = nexus_mock_client
    fake = Faker()

    # use a relative path as destination; another test covers abs/rel paths
    local_dst = fake.file_path(depth=fake.random_int(2, 10))[1:]
    assert_type = os.path.isfile
    if is_dst_dir:
        assert_type = os.path.isdir
        local_dst += nexus._local_sep

    FLATTEN = flatten

    with tmpdir.as_cwd():
        local_path = nexus._remote_path_to_local(
            'a', local_dst, flatten=FLATTEN, create=True)
        assert assert_type(local_dst)
        assert os.path.isfile(local_path)


@pytest.mark.integration
@pytest.mark.parametrize('dest_dir_end, flatten, nocache',
                         itertools.product(
                            ('download',
                             'download/',
                             'download/intermediate/.',
                             'download/intermediate/..'),
                            (False, True),
                            (False, True)))
def test_download_tree(
        nexus_client, deep_file_tree, dest_dir_end,
        flatten, faker, nocache, tmpdir):
    """
    Create a repository, upload a random file tree to Nexus, download the
    same files and check if expected files are downloaded.

    Ensure that the download works for the destination specified in
    different formats.
    """
    src_dir, x_file_set = deep_file_tree
    repo = faker.pystr()
    dst_dir = faker.uri_path() + '/'
    path = dst_dir[:-1] + src_dir

    argv = ('repository create hosted raw {}'.format(repo)).split()
    pytest.helpers.create_and_inspect(nexus_client, argv, repo)
    nexus_client.repositories.refresh()

    r = nexus_client.repositories.get_by_name(repo)
    count_uploaded = r.upload_directory(src_dir, dst_dir)
    file_set_uploaded = pytest.helpers.repo_list(
                            nexus_client, repo, count_uploaded, path)

    download_dest = '{}{}{}'.format(str(tmpdir), os.path.sep, dest_dir_end)
    source_path = f'{repo}/{dst_dir}'
    count_downloaded = nexus_client.download(
            source_path, download_dest, flatten=flatten, nocache=nocache)

    assert count_uploaded == count_downloaded
    assert file_set_uploaded == x_file_set
