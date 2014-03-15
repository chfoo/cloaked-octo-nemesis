#!/bin/sh

wpull --input-file urls.txt --warc-file mochimedia-games --delete-after \
-e "robots=off" --no-cookies --tries inf --waitretry 600 --retry-connrefused \
--warc-header "operator: Archive Team" --timeout 60
