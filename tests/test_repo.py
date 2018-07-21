import pytest


@pytest.mark.integration
def test_repo_list(nexus_client):
    repositories = nexus_client.repositories.raw_list()

    assert isinstance(repositories, list)
    assert all(r.get('name') for r in repositories)
    assert all(r.get('format') for r in repositories)
    assert all(r.get('type') for r in repositories)
    assert all(r.get('url') for r in repositories)
