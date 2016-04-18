#!/bin/bash -ex
HUGO=0.15
if [ ! -f .build/hugo_${HUGO}_linux_amd64/hugo_${HUGO}_linux_amd64 ]; then
  mkdir -p .build
  tar -xzvf .jenkins/distrib/hugo_${HUGO}_linux_amd64.tar.gz -C .build
fi
.build/hugo_${HUGO}_linux_amd64/hugo_${HUGO}_linux_amd64 server -t beg -w -b http://localhost/
