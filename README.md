# nexus3-cli
A python-based CLI for Sonatype's Nexus OSS 3

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
```

For all commands and options, run `nexus3 -h`.

## To do
1. Finish writing tests
1. Refactor so this can be used as a library
1. Support for upload/download
