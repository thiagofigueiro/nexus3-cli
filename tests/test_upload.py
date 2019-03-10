import pytest


@pytest.mark.integration
def test_upload_tree(nexus_client, deep_file_tree, faker):
    """
    Create a repository, upload a random file tree to Nexus and check that the
    resulting list of files in nexus corresponds to the uploaded list of files.
    """
    src_dir, x_file_set = deep_file_tree
    repo_name = faker.pystr()
    dst_dir = faker.uri_path() + '/'
    path = dst_dir[:-1] + src_dir

    argv = ('repo create hosted raw {}'.format(repo_name)).split()
    pytest.helpers.create_and_inspect(nexus_client, argv, repo_name)
    nexus_client.repositories.refresh()

    r = nexus_client.repositories.get_by_name(repo_name)
    count = r.upload_directory(src_dir, dst_dir)
    file_set = pytest.helpers.repo_list(nexus_client, repo_name, count, path)

    assert file_set == x_file_set
