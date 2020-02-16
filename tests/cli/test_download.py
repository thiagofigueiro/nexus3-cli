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
        x_local_path = x_local_path.replace('_TMP_', str(tmpdir) + os.sep)

    with tmpdir.as_cwd():
        local_path = nexus._remote_path_to_local(
            remote, destination, FLATTEN, create=False)

    assert str(local_path) == x_local_path


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
