#!/bin/sh

# A sample command to quickly search the URLTeam torrent for URLs
# Requires XZ utils and GNU Parallel

find . -name "*.xz" |parallel xzcat|grep -P "bre\.ad"
