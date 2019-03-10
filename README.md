# nexus3-cli
A python-based command-line interface and API client for Sonatype's [Nexus 
OSS 3](https://www.sonatype.com/download-oss-sonatype).

[![Build Status](https://travis-ci.org/thiagofigueiro/nexus3-cli.svg?branch=master)](https://travis-ci.org/thiagofigueiro/nexus3-cli)
[![CodeFactor](https://www.codefactor.io/repository/github/thiagofigueiro/nexus3-cli/badge)](https://www.codefactor.io/repository/github/thiagofigueiro/nexus3-cli)
[![codecov](https://codecov.io/gh/thiagofigueiro/nexus3-cli/branch/master/graph/badge.svg)](https://codecov.io/gh/thiagofigueiro/nexus3-cli)
[![Documentation Status](https://readthedocs.org/projects/nexus3-cli/badge/?version=latest)](https://nexus3-cli.readthedocs.io/en/latest/?badge=latest)

## Features

1. Compatible with [Nexus 3 OSS](https://www.sonatype.com/download-oss-sonatype)
1. Python API and command-line support
1. Artefact management: list, upload, download, delete. 
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
docker run -d --rm -p 8081:8081 sonatype/nexus3
```

Nexus will take a little while to start-up the first time you run it. You can
tell when it's available by looking at the Docker instance logs or browsing to
[http://localhost:8081](http://admin:admin123@localhost:8081).

If you haven't changed the default Nexus credentials, you can use it straight 
away; here's the list of default repositories:

```bash
$ nexus3 repo list
Name                                     Format  Type    URL
----                                     ------  ----    ---
maven-snapshots                          maven2  hosted  http://localhost:8081/repository/maven-snapshots
maven-central                            maven2  proxy   http://localhost:8081/repository/maven-central
nuget-group                              nuget   group   http://localhost:8081/repository/nuget-group
nuget.org-proxy                          nuget   proxy   http://localhost:8081/repository/nuget.org-proxy
maven-releases                           maven2  hosted  http://localhost:8081/repository/maven-releases
nuget-hosted                             nuget   hosted  http://localhost:8081/repository/nuget-hosted
maven-public                             maven2  group   http://localhost:8081/repository/maven-public
```

The `login` command will store the service URL and your credentials in 
`~/.nexus-cli` (warning: restrictive file permissions are set but the contents
are saved in plain-text).

```bash
$ nexus3 login
Nexus OSS URL (http://localhost:8081):
Nexus admin username (admin):
Nexus admin password (admin123):
```

Create a Yum repository with read-only access:
```bash
$ nexus3 repo create hosted yum my-yum-repository --write=deny
Created repository: my-yum-repository
```

The CLI output can be filtered using standard *nix tools, e.g. using `grep`:
```bash
$ nexus3 repo list | grep my-yum-repository
Name                                     Format  Type    URL
----                                     ------  ----    ---
my-yum-repository                        yum     hosted  http://localhost:8081/repository/my-yum-repository
```

For all commands and options, run `nexus3 -h`.

### API

See [API documentation](https://nexus3-cli.readthedocs.io/en/latest/api.html).

## Development

The automated tests are configured in `.travis.yml`. To run tests locally,
install the package with test dependencies and run pytest:

```bash
pip install -e .[test]
pytest -m 'not integration'
```

Integration tests require a local Nexus instance listening on 8081 or as
configured in `~/.nexus-cli`; the example configuration used for tests is in
`tests/fixtures/dot-nexus-cli`.

```bash
docker run -d --rm -p 127.0.0.1:8081:8081 --name nexus sonatype/nexus3
./tests/wait-for-nexus.sh  # the Nexus instance takes a while to be ready
pytest -m integration
docker kill nexus
```

Nota Bene: if you re-run integration tests without re-creating or cleaning-up the 
dev Nexus instance, test will fail because objects created during tests will 
already exist. 

Pull requests are welcome; please see [CONTRIBUTING.md](CONTRIBUTING.md).
