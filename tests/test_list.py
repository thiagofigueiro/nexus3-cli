import pytest

import nexuscli
from nexuscli.nexus_client import NexusClient


@pytest.mark.parametrize(
    'repository_path,response_artefacts,x_count', [
        ('repo',           ['file1', 'dir/file2', 'dir/sub/file3'],    3),
        ('repo/',          ['file1', 'dir/file2', 'dir/sub/file3'],    3),
        ('repo/a',         ['a/a', 'a2/a'],                            0),
        ('repo/a/',        ['a/a', 'a2/a'],                            1),
        ('repo/file',      ['file', 'file2'],                          1),
        ('repo/dir/',      ['dir/file', 'dir/file2'],                  2),
        ('repo/dir/',      ['dir/file', 'dir/file2', 'dir/dir2/file'], 3),
        ('repo/dir/file',  ['dir/file', 'dir/file2'],                  1),
        ('repo/dir/file',  ['dir2/file', 'di2/file2'],                 0),
        ('repo/dir/file/', ['dir/file', 'dir/file2'],                  0),
        ('repo/dir/file/', ['dir2/file', 'dir2/file2'],                0),
        ('repo/dir/sub/',  ['file', 'dir/file', 'dir/sub/file'],       1),
    ]
)
def test_list(
        repository_path, response_artefacts, x_count, mocker):
    """
    Given a repository_path and a response from the service, ensure that the
    method returns the expected number of files.
    """
    raw_response = pytest.helpers.nexus_raw_response(
        response_artefacts, repository_path)

    nexus = NexusClient()
    nexus._get_paginated = mocker.Mock(return_value=raw_response)

    artefacts = []
    for artefact in nexus.list(repository_path):
        artefacts.append(artefact)

    assert len(artefacts) == x_count


@pytest.mark.parametrize('x_partial', [True, False])
def test_list_args(x_partial, file_upload_args, mocker, faker):
    """
    Ensure the method calls the correct upload methods with the right arguments
    and returns a generator that yields the expected results.
    """
    _, x_repo_name, x_dst_dir, x_dst_file = file_upload_args

    # directories are found using a partial match
    if x_partial:
        x_dst_file = None
        x_starts_with = x_dst_dir + '/'
        repository_path = '/'.join([x_repo_name, x_dst_dir])
    else:
        x_starts_with = '/'.join([x_dst_dir, x_dst_file])
        repository_path = '/'.join([x_repo_name, x_dst_dir, x_dst_file])

    nexus = NexusClient()
    nexus.split_component_path = mocker.Mock(
        return_value=(x_repo_name, x_dst_dir, x_dst_file))

    nexus._get_paginated = mocker.Mock()

    mocker.patch(
        'nexuscli.nexus_util.filtered_list_gen',
        return_value=[{'path': faker.file_path()}])

    # collect results into a list for easier comparison
    artefacts = []
    for artefact in nexus.list(repository_path):
        artefacts.append({'path': artefact})

    nexus.split_component_path.assert_called_with(repository_path)
    nexus._get_paginated.assert_called()
    nexuscli.nexus_util.filtered_list_gen.assert_called_with(
        nexus._get_paginated.return_value,
        partial_match=x_partial,
        term=x_starts_with)
    assert artefacts == nexuscli.nexus_util.filtered_list_gen.return_value
