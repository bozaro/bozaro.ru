#!/bin/sh -ex
cd `dirname $0`
./hugo.sh --buildDrafts=true $@
./hugo.sh $@
find public -type f -regex ".*\.\(js\|css\|html\|xml\|csv\|py\)" -exec gzip -fkn9 {} \;
