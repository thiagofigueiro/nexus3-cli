# nexus3-cli
A python-based CLI for Sonatype's Nexus OSS 3

[![Build Status](https://travis-ci.org/thiagofigueiro/nexus3-cli.svg?branch=master)](https://travis-ci.org/thiagofigueiro/nexus3-cli)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e76864ccc6f244cfbc1c735f6d3d6944)](https://www.codacy.com/app/thiagocsf/nexus3-cli?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=thiagofigueiro/nexus3-cli&amp;utm_campaign=Badge_Grade)
[![CodeFactor](https://www.codefactor.io/repository/github/thiagofigueiro/nexus3-cli/badge)](https://www.codefactor.io/repository/github/thiagofigueiro/nexus3-cli)
[![codecov](https://codecov.io/gh/thiagofigueiro/nexus3-cli/branch/master/graph/badge.svg)](https://codecov.io/gh/thiagofigueiro/nexus3-cli)

## Usage

```bash
$ pip install nexus3-cli
$ docker run -d --rm -p 8081:8081 sonatype/nexus3
# (wait for nexus to start-up)

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

$ nexus3 repo create hosted yum my-yum-repository --write=deny
Created repository: my-yum-repository

$ nexus3 repo list | grep my-yum-repository
Name                                     Format  Type    URL
----                                     ------  ----    ---
my-yum-repository                        yum     hosted  http://localhost:8081/repository/my-yum-repository
```

For all commands and options, run `nexus3 -h`.

## To do
1. Finish writing unit tests
1. Refactor so this can be used as a library
1. Support for upload/download
