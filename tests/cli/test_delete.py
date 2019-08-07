import pytest


def test_delete(faker, nexus_mock_client, mocker):
    """
    Given a repository_path and a response from the service, ensure that the
    method deletes the expected artefacts.
    """
    nexus = nexus_mock_client
    x_repository = faker.uri_path()
    x_count = faker.random_int(20, 100)
    # list with random count of artefact paths without the leading /
    x_artefacts = [
        faker.file_path(
            depth=faker.random_int(2, 10))[1:] for _ in range(x_count)
    ]

    # Use list instead of generator so we can inspect contents
    raw_response = [
        a for a in pytest.helpers.nexus_raw_response(x_artefacts)
    ]
    nexus.list_raw = mocker.Mock(return_value=raw_response)

    ResponseMock = pytest.helpers.get_ResponseMock()
    nexus.http_delete = mocker.Mock(return_value=ResponseMock(204, 'All OK'))

    # call actual method being tested
    delete_count = nexus.delete(x_repository)

    assert delete_count == x_count
    nexus.list_raw.assert_called_with(x_repository)
    nexus.http_delete.assert_called()
