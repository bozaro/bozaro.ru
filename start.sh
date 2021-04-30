#!/bin/bash -ex
cd `dirname $0`
./hugo.sh server --buildDrafts=true -w -b http://localhost/
