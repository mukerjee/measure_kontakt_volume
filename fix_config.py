#!/usr/bin/env python

import sys

lines = open(sys.argv[1]).read().split('\n')[:-1]
fp = open(sys.argv[1], 'w')
for line in lines:
    l = line.split('.nki')[0].strip().lower().replace(' ', '_').replace('-', '_')
    print l
    fp.write(l + '\n')
