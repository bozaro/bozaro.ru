#!/bin/bash -ex
cd `dirname $0`
./hugo.sh $@
find public -regextype posix-extended -regex ".*\.(js|css|html|xml|csv|py)" -exec gzip -fk9 {} \;