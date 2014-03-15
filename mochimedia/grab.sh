#!/bin/sh

python3 -m wpull --input-file urls.txt --warc-file mochimedia-games \
--delete-after \
--no-robots --no-cookies --tries inf --waitretry 600 --retry-connrefused \
--warc-header "operator: Archive Team" --timeout 60 --retry-dns-error \
--database mochi.db
