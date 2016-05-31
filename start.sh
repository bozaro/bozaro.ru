#!/bin/bash -ex
cd `dirname $0`
./build.sh server -w -b http://localhost/
