#!/bin/sh
echo "STABLE_GIT_COMMIT $(git rev-parse HEAD)"
echo "BUILD_TIME $(date --utc --iso-8601=seconds)"
