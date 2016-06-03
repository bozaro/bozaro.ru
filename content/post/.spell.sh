#!/bin/bash
cat $1 | perl -0pe 's/```(.|\n)*?```//g' | hunspell -d ru_RU,en_US -p .words -l | sort -u
