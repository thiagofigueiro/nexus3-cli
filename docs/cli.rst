Command-line Interface
======================

Logging level can be configured by setting an environment variable named
``LOG_LEVEL``. Valid values are: ``DEBUG``, ``INFO``, ``WARNING`` (default),
``ERROR``, ``CRITICAL``.


.. click:: nexuscli.cli:nexus_cli
   :prog: nexus3
   :show-nested:
