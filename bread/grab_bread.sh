#!/bin/sh

mkdir -p db/
python3 bread_url_grab.py  --threads 13 --average-rate 50 --log-dir /tmp/ --database-dir db/
