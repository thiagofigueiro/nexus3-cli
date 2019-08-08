import pytest

from nexuscli.api import script


@pytest.fixture
def script_collection(mocker):
    """A ScriptCollection with the nexus_client mocked"""
    fixture = script.ScriptCollection(client=mocker.Mock())
    # return_value is the mocked "request.response" object
    fixture._client.http_get.return_value.status_code = mocker.PropertyMock()
    return fixture


@pytest.fixture
def contains():
    """
    This is useful when you need to verify a partial match in a method patched
    with mocker's (Mock) assert_called_with() method.

        >>> def test_mytest(contains, mocker):
        >>>     mocker.patch('some_module.some_method')
        >>>     some_module.some_method('argument')
        >>>     some_module.some_method.assert_called_with(contains('gum'))
        >>> # PASS
    """
    class ShouldContain(str):
        def __eq__(self, other):
            return self in other

    return ShouldContain
