#!/bin/bash -ex
cd `dirname $0`
./hugo.sh $@
find public -type f -regextype posix-extended -regex ".*\.(js|css|html|xml|csv|py)" -exec gzip -fkn9 {} \;