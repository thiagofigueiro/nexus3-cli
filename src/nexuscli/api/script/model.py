from nexuscli import exception


class ScriptCollection(object):
    """
    A class to manage Nexus 3 scripts.

    Args:
        client(nexuscli.nexus_client.NexusClient): the client instance that
            will be used to perform operations against the Nexus 3 service. You
            must provide this at instantiation or set it before calling any
            methods that require connectivity to Nexus.

    Attributes:
        client(nexuscli.nexus_client.NexusClient): as per ``client``
            argument of :class:`ScriptCollection`.
    """
    def __init__(self, client=None):
        self._client = client

    def exists(self, name):
        """
        Check if a script exists.

        :param name: of script to verify existence.
        :return: True if it exists, false otherwise
        :rtype: bool
        :raises exception.NexusClientAPIError: if the response from the Nexus
            service isn't recognised; i.e.: any HTTP code other than 200, 404.
        """
        resp = self._client.http_head(f'script/{name}')
        if resp.status_code == 200:
            return True
        elif resp.status_code == 404:
            return False
        else:
            raise exception.NexusClientAPIError(resp.content)

    def get(self, name):
        """
        Get a Nexus 3 script by name.

        :param name: of script to be retrieved.
        :return: the script or None, if not found
        :rtype: dict, None
        :raises exception.NexusClientAPIError: if the response from the Nexus
            service isn't recognised; i.e.: any HTTP code other than 200, 404.
        """
        resp = self._client.http_get(f'script/{name}')
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            raise exception.NexusClientAPIError(resp.content)

    def list(self):
        """
        List of all script names on the Nexus 3 service.

        :return: a list of names
        :rtype: list
        :raises exception.NexusClientAPIError: if the script names cannot be
            retrieved; i.e.: any HTTP code other than 200.
        """
        resp = self._client.http_get('script')
        if resp.status_code != 200:
            raise exception.NexusClientAPIError(resp.content)

        return resp.json()

    def create_if_missing(self, name, content, script_type='groovy'):
        """
        Creates a script in the Nexus 3 service IFF a script with the same name
        doesn't exist. Equivalent to checking if the script exists with
        :meth:`get` and, if not, creating it with :meth:`create`.

        Parameters as per :py:meth:`create`.
        """
        if not self.exists(name):
            self.create(name, content, script_type)

    def create(self, script_name, script_content, script_type='groovy'):
        """
        Create the given script in the Nexus 3 service.

        :param script_name: name of script to be created.
        :type script_name: str
        :param script_content: script code.
        :type script_content: str
        :param script_type: type of script to be created.
        :type script_type: str
        :raises exception.NexusClientAPIError: if the script creation isn't
            successful; i.e.: any HTTP code other than 204.
        """
        script = {
            'type': script_type,
            'name': script_name,
            'content': script_content,
        }

        resp = self._client.http_post('script', json=script)
        if resp.status_code != 204:
            raise exception.NexusClientAPIError(resp.content)

    def run(self, script_name, data=''):
        """
        Runs an existing script on the Nexus 3 service.

        :param script_name: name of script to be run.
        :param data: parameters to be passed to the script, via HTTP POST. If
            the script being run requires a certain format or encoding, you
            need to prepare it yourself. Typically this is `json.dumps(data)`.
        :return: the content returned by the script, if any.
        :rtype: str, dict
        :raises exception.NexusClientAPIError: if the Nexus service fails to
            run the script; i.e.: any HTTP code other than 200.
        """
        headers = {'content-type': 'text/plain'}
        endpoint = 'script/{}/run'.format(script_name)
        resp = self._client.http_post(endpoint, headers=headers, data=data)
        if resp.status_code != 200:
            raise exception.NexusClientAPIError(resp.content)

        return resp.json()

    def delete(self, script_name):
        """
        Deletes a script from the Nexus 3 repository.

        :param script_name: name of script to be deleted.
        :raises exception.NexusClientAPIError: if the Nexus service fails to
            delete the script; i.e.: any HTTP code other than 204.
        """
        endpoint = 'script/{}'.format(script_name)
        resp = self._client.http_delete(endpoint)
        if resp.status_code != 204:
            raise exception.NexusClientAPIError(resp.reason)


# TODO: describe script and use/return from collection methods
class Script(object):
    """A Class representing a Nexus 3 script."""
    pass
