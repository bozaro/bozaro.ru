#!/bin/sh -ex
cd `dirname $0`
set +e
HUGO=""
set -e
if [ "${HUGO}" = "" ]; then
  HUGO_VER=0.82.1
  if [ ! -f .build/hugo_${HUGO_VER}_linux_amd64/hugo_${HUGO_VER}_linux_amd64 ]; then
    HUGO_TGZ=.jenkins/distrib/hugo_${HUGO_VER}_Linux-64bit.tar.gz
    if [ ! -f $HUGO_TGZ ]; then
      curl -fL -o ${HUGO_TGZ}~ https://github.com/gohugoio/hugo/releases/download/v${HUGO_VER}/hugo_${HUGO_VER}_Linux-64bit.tar.gz
      mv ${HUGO_TGZ}~ ${HUGO_TGZ}
    fi
    mkdir -p .build/hugo_${HUGO_VER}_linux_amd64
    tar -xzvf ${HUGO_TGZ}  -C .build/hugo_${HUGO_VER}_linux_amd64
  fi
  HUGO=".build/hugo_${HUGO_VER}_linux_amd64/hugo"
fi
${HUGO} $@
