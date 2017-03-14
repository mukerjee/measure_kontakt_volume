#!/usr/bin/env python

import sys
import os

tags = {
    'fx_gliss': ['slides'],
    'long_flutter': ['trem', 'long'],
    'long_mariachi': ['mariachi', 'long'],
    'long_muted': ['long', 'muted'],
    'long': ['long'],
    'multitongue': ['short', 'quarter_note', 'multitongue'],
    'marcato_muted': ['short', 'quarter_note', 'hard', 'muted'],
    'marcato': ['short', 'quarter_note', 'hard'],
    'staccato_muted': ['short', '16th_note', 'muted'],
    'staccato': ['short', '16th_note'],
    'tenuto_muted': ['short', '8th_note', 'muted'],
    'tenuto': ['short', '8th_note'],
    'trills_major_2nd': ['long', 'trill_maj2'],
    'trills_minor_2nd': ['long', 'trill_min2'],
    'legato': ['legato'],
    'falls': ['rips'],
    'rips': ['rips'],
    'fall': ['falls'],
    'rip': ['rips'],
    'staccatissimio': ['short', '32nd_note'],
    'trill_major_2nd': ['long', 'trill_maj2'],
    'trill_minor_2nd': ['long', 'trill_min2'],
    'trill_minor_second': ['long', 'trill_min2'],
    'bells_up_crotchet': ['bells_up', 'short', 'quarter_note'],
    'long_bells_up_long': ['bells_up', 'long'],
    'bells_up_quaver': ['bells_up', 'short', '8th_note'],
    'bells_up_staccatissimo': ['bells_up', 'short', '32nd_note'],
    'bells_up_staccato': ['bells_up', 'short', '16th_note'],
    'long_cuivre': ['long', 'brassy'],
    'long_stopped': ['long', 'stopped'],
    'fanfare': ['long', 'fanfare'],
    'performance_legato': ['legato'],
    'long_flutter_muted': ['long', 'trem', 'muted'],
    'cs': ['long', 'muted'],
    'stopped': ['long', 'stopped'],
    'long_alt': ['alternate', 'long'],
    }

maker = sys.argv[1].split('/')[-2]
print 'function spitfire_brass_init()'
print '\tadd_instrument(1, "Horn")'
print '\tadd_instrument(2, "Horn a2")'
print '\tadd_instrument(3, "Horn a6")'
print '\tadd_instrument(4, "Trombone")'
print '\tadd_instrument(5, "Trombone a2")'
print '\tadd_instrument(6, "Bass Trombone")'
print '\tadd_instrument(7, "Bass Trombone a2")'
print '\tadd_instrument(8, "Contrabass Trombone")'
print '\tadd_instrument(9, "Trombone a6")'
print '\tadd_instrument(10, "Trumpet")'
print '\tadd_instrument(11, "Trumpet a2")'
print '\tadd_instrument(12, "Trumpet a6")'
print '\tadd_instrument(13, "Tuba")'
print '\tadd_instrument(14, "Contrabass Tuba")'
print '\tadd_instrument(15, "Cimbasso")'
print '\tadd_instrument(16, "Cimbasso a2")'
print '\tdeclare global emap[10]'
print '\tdeclare global vmap[10]'
print 'end function'
print
print
print
print 'function %s(inst)' % maker
print '\tvibrato_cc_menu := 21'
print '\tinstance_knob := 0'
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
        print '\t\t\tarts_len := %d' % len(lines)
        for i, line in enumerate(lines):
            print '\t\t\t{%s}' % (line)
            print '\t\t\tart_labels[%d] := "%s"' % (i, line)
            for tag in tags[line]:
                print '\t\t\tadd_sample_tag(%d, %s)' % (i+1, tag.upper())
            data = open("emaps/%s/%s/%s.emap" % (maker, instrument, line)).read().split('\n')[:-1]
            exp = []
            vol = []
            for d in data:
                v, e, target, got = eval(d.split('\t')[1])
                exp.append(e)
                vol.append(v)
            for k, e in enumerate(exp):
                print '\t\t\temap[%d] := %d' % (k, e)
            for k, v in enumerate(vol):
                print '\t\t\tvmap[%d] := %d' % (k, v)
            print '\t\t\tinterpolate_expression_map(%d)' % i
            print '\t\t\tinterpolate_volume_map(%d)' % i
            # exp = str(exp).replace("[", "").replace("]", "")
            # print '\t\t\tinterpolate_expression_map(%d, %s)' % (i, exp)
            # vol = str(vol).replace("[", "").replace("]", "")
            # print '\t\t\tinterpolate_volume_map(%d, %s)' % (i, vol)
            print
print '\tend select'
print '\tcall update_ui'
print 'end function'
