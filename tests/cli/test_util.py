from nexuscli.cli import util


def test_get_client(mocker):
    """
    Ensure the method returns the object created by NexusClient() and that the
    configuration loaded via config.load()
    """
    nexus_config_mock = mocker.patch('nexuscli.cli.util.NexusConfig')
    nexus_client_mock = mocker.patch('nexuscli.cli.util.NexusClient')
    nexus_client = util.get_client()

    nexus_config_mock.return_value.load.assert_called_once()
    nexus_client_mock.assert_called_once()
    assert nexus_client == nexus_client_mock.return_value
