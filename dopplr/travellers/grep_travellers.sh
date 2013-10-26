#!/bin/sh

find -iname "*.warc.gz" | \
    parallel gzip --decompress --stdout "{}" | \
    grep -o -P "www\.dopplr\.com/traveller/[a-zA-Z0-9_.-]+" | \
    sort -u
