#!/bin/sh

# A sample command to quickly search the URLTeam torrent for URLs

find . -name "*.xz" |parallel xzcat|grep -P "bre\.ad"
