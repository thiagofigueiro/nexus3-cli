#!/usr/bin/env bash
function nexus_ready {
  [[ "200" == $(curl -o /dev/null -s -w "%{http_code}\n" nexus:8081) ]]
}

count=0
until nexus_ready
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
