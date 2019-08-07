Groovy Scripts
==============

This package makes use of Groovy scripts to perform actions that are not
available through the Nexus 3 REST API.

All scripts added have names starting with ``nexus3-cli-``.

.. code-block:: console
   :emphasize-lines: 1

    $ nexus3 script list
    Name (type)
    nexus3-cli-cleanup-policy (groovy)
    nexus3-cli-repository-create (groovy)


You can delete them all by running:

.. code-block:: console
   :emphasize-lines: 1

    $ nexus3 script list | awk '{ print $1 }' | xargs --no-run-if-empty -n1 nexus3 script del
    Name (type)

To increase verbosity of logging for the scripts, create a new logger
(e.g.: http://localhost:8081/#admin/support/logging) with logger name
``org.sonatype.nexus.script.plugin.internal.rest.ScriptResource`` and logging
level ``DEBUG`` or ``TRACE``.
