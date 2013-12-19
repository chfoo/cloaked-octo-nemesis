#!/usr/bin/python
'''Deploys ArchiveTeam Massive Train Warrior Pipeline Launcher System.

Edit script to fit your needs.
'''
import subprocess


if __name__ == '__main__':
    procs = []

    for i in range(1, 255):
        ip = 'bind_address=192.168.1.' + str(i)
        print('IP:', ip)
        proc = subprocess.Popen([
            'run-pipeline',
            'pipeline.py',
            'YOURNICKHERE',
            '--context-value', ip,
            '--disable-web-server',
            ],
        )
        procs.append(proc)

    for proc in procs:
        proc.wait()
