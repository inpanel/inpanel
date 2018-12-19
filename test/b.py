#!/usr/bin/env python

import os
import sys

for dirname in os.listdir('/proc'):
    if dirname == 'curproc':
        continue

    try:
        with open('/proc/{}/cmdline'.format(dirname), mode='rb') as fd:
            content = fd.read().decode().split('\x00')
    except Exception:
        continue

    for i in sys.argv[1:]:
        if i in content[0]:
            print('{0:<12} : {1}'.format(dirname, ' '.join(content)))