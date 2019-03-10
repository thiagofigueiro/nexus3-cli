Examples
--------

Here are some basic operations to get you started. The CLI implementation in
``src/nexuscli/cli.py`` is another good source of examples.

In all examples below you will need to instantiate a client:

>>> import nexuscli
>>> nexus_client = nexuscli.nexus_client.NexusClient()
>>> # update the local list of repositories on the client
>>> nexus_client.repositories.refresh()
>>> # retrieve the list of repositories
>>> repositories = nexus_client.repositories.raw_list()
>>> repositories[0]
{'name': 'maven-snapshots',
 'format': 'maven2',
 'type': 'hosted',
 'url': 'http://localhost:8081/repository/maven-snapshots'}

Whenever you see ``nexus_client`` being used, remember to copy the first two
lines of code above as well.

Create a repository
^^^^^^^^^^^^^^^^^^^

>>> r = nexuscli.repository.Repository(
>>>     'hosted',
>>>     name='my-repository',
>>>     format='raw',
>>>     blob_store_name='default',
>>>     strict_content_type_validation=False,
>>>     write_policy='allow',
>>> )
>>> nexus_client.repositories.create(r)
>>> nexus_client.repositories.get_raw_by_name('my-repository')
{'name': 'my-repository',
 'format': 'raw',
 'type': 'hosted',
 'url': 'http://localhost:8081/repository/my-repository'}


Delete a repository
^^^^^^^^^^^^^^^^^^^

>>> nexus_client.repositories.delete('my-repository')


Upload a file
^^^^^^^^^^^^^

>>> repository = nexus_client.repositories.get_by_name('my-repository')
>>> upload_count = repository.upload('/etc/passwd', '/etc/passwd')
>>> print(upload_count)
1
