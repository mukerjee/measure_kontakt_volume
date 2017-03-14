#!/usr/bin/env python

import sys
import os
import string

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

to_tag_set = {
    "generic": "note_type",
    "alternate": "note_type",
    "fx": "note_type",
    "rips": "note_type",
    "falls": "note_type",
    "runs": "note_type",
    "arcs": "note_type",
    "slides": "note_type",
    "normal_technique": "technique",
    "alt_technique": "technique",
    "pizz": "technique",
    "col_lengo": "technique",
    "harmonic": "technique",
    "brassy": "technique",
    "mariachi": "technique",
    "fanfare": "technique",
    "bells_up": "technique",
    "no_length": "general_length",
    "length_null": "general_length",
    "long": "general_length",
    "short": "general_length",
    "legato": "general_length",
    "generic_length": "specific_length",
    "specific_length_null": "specific_length",
    "32nd_note": "specific_length",
    "16th_note": "specific_length",
    "8th_note": "specific_length",
    "quarter_note": "specific_length",
    "half_note": "specific_length",
    "whole_note": "specific_length",
    "legato_fast": "specific_length",
    "legato_slow": "specific_length",
    "legato_runs": "specific_length",
    "legato_detache": "specific_length",
    "no_mute": "mute",
    "muted": "mute",
    "harmon_mute": "mute",
    "straight_mute": "mute",
    "cup_mute": "mute",
    "plunger_mute": "mute",
    "bucket_mute": "mute",
    "stopped": "mute",
    "no_trem": "trem",
    "trem": "trem",
    "no_trill": "trill",
    "trill": "trill",
    "trill_min2": "trill",
    "trill_maj2": "trill",
    "trill_min3": "trill",
    "trill_maj3": "trill",
    "trill_p4": "trill",
    "no_sync": "sync",
    "sync": "sync",
    "sync120": "sync",
    "sync150": "sync",
    "sync180": "sync",
    "no_div": "div",
    "div": "div",
    "div_small": "div",
    "octave": "div",
    "no_multitongue": "multitongue",
    "multitongue": "multitongue",
    "double_tongue": "multitongue",
    "triple_tongue": "multitongue",
    "normal_bow_pos": "bow_pos",
    "alternate_bow_pos": "bow_pos",
    "sul_pont": "bow_pos",
    "sul_tasto": "bow_pos",
    "strings_normal": "string",
    "single_string": "string",
    "sul_e": "string",
    "sul_a": "string",
    "sul_d": "string",
    "sul_g": "string",
    "sul_c": "string",
    "medium": "dyn",
    "dynamics_null": "dyn",
    "soft": "dyn",
    "hard": "dyn",
    "cres": "dyn",
    "dim": "dyn",
    "vib": "vib",
    "vibrato_null": "vib",
    "no_vib": "vib",
    "moto_vib": "vib",
}

maker = sys.argv[1].split('/')[-2]
j = -1
arts_lens = []
arts_labels = []
arts_tags = []
arts_emaps = []
arts_vmaps = []
for filename in os.listdir(sys.argv[1]):
    if filename.endswith(".txt"):
        j += 1
        arts_labels.append([])
        arts_tags.append([])
        arts_emaps.append([])
        arts_vmaps.append([])
        instrument = filename.split('.txt')[0].split('-')[1:]
        if len(instrument) > 1:
            if instrument[1] == 'solo':
                instrument = instrument[0]
            else:
                instrument = '_'.join(instrument)
        else:
            instrument = instrument[0]
        lines = open(sys.argv[1] + filename).read().split('\n')[:-1]
        arts_lens.append(len(lines))
        for i, line in enumerate(lines):
            arts_labels[j].append(line)
            arts_tags[j].append([])
            arts_emaps[j].append([])
            arts_vmaps[j].append([])
            for tag in tags[line]:
                arts_tags[j][i].append(tag)
            data = open("emaps/%s/%s/%s.emap" % (maker, instrument, line)).read().split('\n')[:-1]
            exp = []
            vol = []
            for d in data:
                v, e, target, got = eval(d.split('\t')[1])
                exp.append(e)
                vol.append(v)
            arts_emaps[j][i] = exp
            arts_vmaps[j][i] = vol

print "        ["
for c in arts_tags:
    print "        ["
    for a in c:
        s = "        TagSet("
        for b in a:
            s += "%s = %s, " % (to_tag_set[b],
                                string.capwords(b.replace("_", " ")).replace(" ", ""))
        s = s[:-2]
        s += "),"
        print s
    print "        ],"
    print
print "        ]"
#print "ARTS_LEN = " + str(arts_lens)
#print "ARTS_LABELS = " + str(arts_labels)
#print "TAGS = " + str(arts_tags)
#print "EMAPS = " + str(arts_emaps)
#print "VMAPS = " + str(arts_vmaps)
