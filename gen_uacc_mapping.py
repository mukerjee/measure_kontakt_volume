#!/usr/bin/env python

import sys
import os

uacc = {
    'fx_gliss': 90,
    'long_flutter': 11,
    'long_mariachi': 16,
    'long_muted': 7,
    'long': 1,
    'multitongue': 75,
    'marcato_muted': 53,
    'marcato': 52,
    'staccato_muted': 47,
    'staccato': 40,
    'tenuto_muted': 51,
    'tenuto': 50,
    'trills_major_2nd': 71,
    'trills_minor_2nd': 72,
    'legato': 20,
    'falls': 101,
    'rips': 100,
    'fall': 101,
    'rip': 100,
    'staccatissimio': 42,
    'trill_major_2nd': 71,
    'trill_minor_2nd': 72,
    'trill_minor_second': 72,
    'bells_up_crotchet': 44,
    'long_bells_up_long': 18,
    'bells_up_quaver': 60,
    'bells_up_staccatissimo': 49,
    'bells_up_staccato': 41,
    'long_cuivre': 9,
    'long_stopped': 7,
    'fanfare': 41,
    'performance_legato': 40,
    'long_flutter_muted': 12,
    'cs': 7,
    'stopped': 7,
    'long_alt': 2,
    
    }

maker = sys.argv[1].split('/')[-2]
print 'function %s(inst)' % maker
print '\tselect(inst)'
j = 0
for filename in os.listdir(sys.argv[1]):
    if filename.endswith(".txt"):
        j += 1
        instrument = filename.split('.txt')[0].split('-')[1:]
        if len(instrument) > 1:
            if instrument[1] == 'solo':
                instrument = instrument[0]
            else:
                instrument = '_'.join(instrument)
        else:
            instrument = instrument[0]
        print '\t\tcase %d:  {%s}' % (j, instrument)
        lines = open(sys.argv[1] + filename).read().split('\n')[:-1]
        for i, line in enumerate(lines):
            print '\t\t\tuacc_mapping[%d] := %d  {%s}' % (i, uacc[line], line)
            data = open("emaps/%s/%s/%s.emap" % (maker, instrument, line)).read().split('\n')[:-1]
            exp = []
            vol = []
            for d in data:
                v, e, target, got = eval(d.split('\t')[1])
                exp.append(e)
                vol.append(v)
            exp = str(exp).replace("[", "").replace("]", "")
            print '\t\t\tinterpolate_expression_map(%d, %s)' % (i, exp)
            vol = str(vol).replace("[", "").replace("]", "")
            print '\t\t\tinterpolate_volume_map(%d, %s)' % (i, vol)
            print
print '\tend select'
print 'end function'
