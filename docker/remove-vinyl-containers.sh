#!/usr/bin/env bash
#
# The local vinyldns setup used for testing relies on the
# following docker images:
#   mysql:5.7
#   vinyldns/bind9
#   vinyldns/api
#
# This script with kill and remove containers associated
# with these names and/or tags
#
# Note: this will not remove the actual images from your
# machine, just the running containers

IDS=$(docker ps -a | grep -e 'mysql:5.7' -e 'vinyldns'  | awk '{print $1}')

echo "killing..."
echo $(echo "$IDS" | xargs -I {} docker kill {})
echo

echo "removing..."
echo $(echo "$IDS" | xargs -I {} docker rm -v {})
echo

echo "pruning network..."
docker network prune -f
