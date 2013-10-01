#!/bin/sh

python3 zapd_url_grab.py --sequential --threads 5 --average-rate 5 --log-dir /tmp/ --database-dir db/
