from nexuscli import exception


class ScriptCollection(object):
    """
    A class representing a Nexus 3 script.
    """
    def __init__(self, client=None):
        """
        :param client: client instance
        :type client:  nexuscli.nexus_client.NexusClient
        """
        self.client = client

    def get(self, name):
        resp = self.client._get('script/{}'.format(name))
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            raise exception.NexusClientAPIError(resp.content)

    def list(self):
        resp = self.client._get('script')
        if resp.status_code != 200:
            raise exception.NexusClientAPIError(resp.content)

        return resp.json()

    def create_if_missing(self, script_dict):
        name = script_dict.get('name')
        if name is None:
            raise ValueError('script_dict must have a name')
        # FIXME: use head?
        script = self.get(name)
        if script is None:
            self.create(script_dict)

    def create(self, script_dict):
        resp = self.client._post('script', json=script_dict)
        if resp.status_code != 204:
            raise exception.NexusClientAPIError(resp.content)

    def run(self, script_name, data=''):
        headers = {'content-type': 'text/plain'}
        endpoint = 'script/{}/run'.format(script_name)
        resp = self.client._post(endpoint, headers=headers, data=data)
        if resp.status_code != 200:
            raise exception.NexusClientAPIError(resp.content)

        return resp.json()

    def delete(self, script_name):
        endpoint = 'script/{}'.format(script_name)
        resp = self.client._delete(endpoint)
        if resp.status_code != 204:
            raise exception.NexusClientAPIError(resp.reason)


class Script(object):
    pass
