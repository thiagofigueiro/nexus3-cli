# nexus3-cli

A python-based command-line interface and API client for Sonatype's [Nexus
OSS 3](https://www.sonatype.com/download-oss-sonatype).

[![Build Status](https://travis-ci.org/thiagofigueiro/nexus3-cli.svg?branch=master)](https://travis-ci.org/thiagofigueiro/nexus3-cli)
[![CodeFactor](https://www.codefactor.io/repository/github/thiagofigueiro/nexus3-cli/badge)](https://www.codefactor.io/repository/github/thiagofigueiro/nexus3-cli)
[![codecov](https://codecov.io/gh/thiagofigueiro/nexus3-cli/branch/master/graph/badge.svg)](https://codecov.io/gh/thiagofigueiro/nexus3-cli)
[![Documentation Status](https://readthedocs.org/projects/nexus3-cli/badge/?version=latest)](https://nexus3-cli.readthedocs.io/en/latest/?badge=latest)

**NOTICE**: version 2.0.0 of nexus3-cli has been released and it includes **breaking changes**. If your application uses `nexuscli` and was affected, you should:

* pin your requirements (e.g.: `'nexus3-cli>=1.0.2,<2`); and
* have a look at the changes on the [2.0.0 branch](https://github.com/thiagofigueiro/nexus3-cli/tree/release/2.0.0) in preparation for the upgrade.

Development and support for 1.0.x versions will no longer be provided (at least not by me - I'm happy to review contributions for 1.x).

## Features

1. Compatible with [Nexus 3 OSS](https://www.sonatype.com/download-oss-sonatype)
1. Python API and command-line support
1. Artefact management: list, delete, bulk upload and download.
1. Repository management:
   1. Create hosted and proxy.
   1. Create bower, maven, npm, nuget, pypi, raw, rubygems, yum.
   1. Content type validation, version and write policy.
   1. Delete.
1. Groovy script management: list, upload, delete, run.

The actions above are performed using the Nexus REST API if the endpoint is
available, otherwise a groovy script is used.

Please note that some Nexus 3 features are not currently supporter. Assistance
implementing missing support is very welcome. Please have a look at the
[issues](https://github.com/thiagofigueiro/nexus3-cli/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
and [contribution guidelines](https://github.com/thiagofigueiro/nexus3-cli/blob/develop/CONTRIBUTING.md).

## Installation

The nexus3-cli package is available on PyPi. You can install using pip/pip3:

```bash
pip install nexus3-cli
```

## Usage

### Command line

For a quick start, use the [sonatype/nexus3 Docker image](https://hub.docker.com/r/sonatype/nexus3/):

```bash
docker run -d --rm -p 127.0.0.1:8081:8081 --name nexus sonatype/nexus3
```

Nexus will take a little while to start-up the first time you run it. You can
tell when it's available by looking at the Docker instance logs or browsing to
[http://localhost:8081](http://localhost:8081).

On older versions of the nexus3 Docker image, the default `admin` password is
`admin123`; on newer versions it's automatically generated and you can find it
by running `docker exec nexus cat /nexus-data/admin.password`.

The `login` command will store the service URL and your credentials in
`~/.nexus-cli` (warning: restrictive file permissions are set but the contents
are saved in plain-text).

Setup CLI credentials:

```bash
$ nexus3 login
Nexus OSS URL (http://localhost:8081):
Nexus admin username (admin):
Nexus admin password (admin123):
Verify server certificate (True):

Configuration saved to /Users/thiago/.nexus-cli
```

List repositories:

```bash
$ nexus3 repository list
Name              Format   Type     URL
maven-snapshots   maven2   hosted   http://localhost:8081/repository/maven-snapshots
maven-central     maven2   proxy    http://localhost:8081/repository/maven-central
nuget-group       nuget    group    http://localhost:8081/repository/nuget-group
nuget.org-proxy   nuget    proxy    http://localhost:8081/repository/nuget.org-proxy
maven-releases    maven2   hosted   http://localhost:8081/repository/maven-releases
nuget-hosted      nuget    hosted   http://localhost:8081/repository/nuget-hosted
maven-public      maven2   group    http://localhost:8081/repository/maven-public
```

Create a repository:

```bash
nexus3 repository create hosted raw reponame
```

Do a recursive directory upload:

```bash
$ mkdir -p /tmp/some/deep/test/path
$ touch /tmp/some/deep/test/file.txt /tmp/some/deep/test/path/other.txt
$ cd /tmp; nexus3 up some/ reponame/path/
Uploading some/ to reponame/path/
[################################] 2/2 - 00:00:00
Uploaded 2 files to reponame/path/
```

Nota Bene: nexus3-cli interprets a path ending in `/` as a directory.

List repository contents:

```bash
$ nexus3 ls reponame/path/
path/some/deep/test/path/other.txt
path/some/deep/test/file.txt
```

For all commands, subcommands and options, run `nexus3 -h`.
[CLI documentation](https://nexus3-cli.readthedocs.io/en/latest/cli.html)

### API

See [API documentation](https://nexus3-cli.readthedocs.io/en/latest/api.html).

#### Upgrade from 1.0.x

Version 2.0.0 has significant API changes from 1.0.0. In summary:

* Introduce a `NexusConfig` class to keep the service configuration separate
  from the client.
* `NexusClient` no long accepts configuration keyword arguments; instead it
  takes a `NexusConfig` instance.
* Moved all CLI code to the `cli` package and API code to the `api` package.
* The `Repository` class has been rewritten to make it easier to add support
  for all repositories. Have a look at the manual pages for 2.x linked above.
* Repository upload methods have been moved to their own module in
  `nexuscli.api.repository.upload` to, again, make it easier to support all
  repositories.
* Documentation has been reviewed to include new topics and to automatically
  include any new classes in the html output that lives in
  [read the docs](https://readthedocs.org/projects/nexus3-cli/).
* Unit tests have been refactored and re-organised to more closely match the
  `src` structure.

## Development

The automated tests are configured in `.travis.yml`. To run tests locally,
install the package with test dependencies and run pytest:

```bash
pip install [--user] -e .[test]
pip install [--user] pytest faker
pytest -m 'not integration'
```

Integration tests require a local Nexus instance listening on 8081 or as
configured in `~/.nexus-cli`; the example configuration used for tests is in
`tests/fixtures/dot-nexus-cli`.

```bash
docker run -d --rm -p 127.0.0.1:8081:8081 --name nexus sonatype/nexus3
./tests/wait-for-nexus.sh  # the Nexus instance takes a while to be ready
# use the random admin password generated by the Nexus container to login
./tests/nexus-login $(docker exec nexus cat /nexus-data/admin.password)
pytest -m integration
docker kill nexus
```

Nota Bene: if you re-run integration tests without re-creating or cleaning-up the
dev Nexus instance, test will fail because some objects created during tests will
already exist.

Pull requests are welcome; please see [CONTRIBUTING.md](CONTRIBUTING.md).
