acrea-backup
============

This generates a git repo of Areca's source releases.

The CVS repo vanished from its homepage but it was still accessible and mirrored to https://github.com/chfoo/areca-backup-cvs-mirror

Quick start
===========

1. Install Python 3.
2. Install dependencies: ``pip3 install lxml arrow requests``
3. ``python3 download_releases.py``
4. ``python3 git_fast_import.py > data.txt``
5. ``git init acrea-backup-mirror.git --bare``
6. ``cd acrea-backup-mirror.git/``
7. ``git fast-import < ../data.txt``

