#!/usr/bin/env bash

: "${1:?usage: wait-for-nexus.sh host [port]}"

function nexus_ready {
  [[ "200" == $(curl -o /dev/null -s -w "%{http_code}\n" $1:$2) ]]
}

count=0
until nexus_ready $1 ${2:8081}
do
  count=$((count+1))
  if [ ${count} -gt 180 ]
  then
    echo 'Timeout-out waiting for nexus container'
    docker logs nexus
    docker ps
    exit 1
  fi
  sleep 1
done
