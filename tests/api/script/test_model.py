import pytest

from nexuscli import exception


def test_get_error(script_collection, faker, contains):
    """Ensure the method raises an exception on unexpected API response"""
    x_name = faker.pystr()

    with pytest.raises(exception.NexusClientAPIError):
        script_collection.get(x_name)

    script_collection._client.http_get.assert_called_with(contains(x_name))


@pytest.mark.parametrize('status_code, x_result', [
    (200, 'resp.json'),
    (404, None),
])
def test_get(status_code, x_result, script_collection):
    """
    Ensure the method returns the response associated with API status codes
    """
    x_resp = script_collection._client.http_get.return_value
    x_resp.status_code = status_code
    x_resp.json.return_value = x_result

    result = script_collection.get('dummy')

    assert result == x_result


def test_list_error(script_collection):
    """Ensure the method raises an exception on unexpected API response"""
    with pytest.raises(exception.NexusClientAPIError):
        script_collection.list()

    script_collection._client.http_get.assert_called_with('script')


def test_list(script_collection):
    """Ensure the method returns the expected value on success"""
    x_resp = script_collection._client.http_get.return_value
    x_resp.status_code = 200

    result = script_collection.list()

    assert result == x_resp.json.return_value
