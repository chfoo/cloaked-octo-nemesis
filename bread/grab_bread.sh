#!/bin/sh

mkdir -p db/
python3 bread_url_grab.py  --threads 25 --average-rate 25 --log-dir /tmp/ --database-dir db/
