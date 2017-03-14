#!/usr/bin/env python

import pyaudio
import rtmidi_python as rtmidi
import struct
from math import ceil, log
import time
import collections
import sys
import os
from A_weighting import A_weighting
from scipy.signal import lfilter
import numpy as np


DYNAMICS = collections.OrderedDict([
    ('p4', 10),   # pppp
    ('p3', 23),   # ppp
    ('pp', 36),   # pp
    ('p',  49),   # p
    ('mp', 62),   # mp
    ('mf', 75),   # mf
    ('f',  88),   # f
    ('ff', 101),  # ff
    ('f3', 114),  # fff
    ('f4', 127),  # ffff
])

DOUBLING_TO_DB = 3  # doubling signal leads to 3dB increase

EXPECTED_RMS = {
    #                 p4   p3   pp    p   mp   mf    f   ff   f3  f4
    'strings':      [-30, -27, -24, -21, -18, -15, -12,  -9,  -6, -3],
    'winds':        [-30, -27, -24, -21, -19, -17, -15, -12,  -9, -6],
    'quiet brass':  [-30, -27, -24, -21, -18, -15, -12,  -9,  -6, -3],
    'brass':        [-30, -27, -24, -21, -17, -13,  -9,  -6,  -3,  0],
}

MAX_RMS_ERROR = 0.5  # dB
AUDIO_RMS_OFFSET = -42

MIDI_DEVICE_NAME = "IAC Driver VEP 1"
MIDI_OUT = None
MIDI_CHANNEL = 0

VOL = 127

LIBRARY = None
INSTRUMENT = None
INSTRUMENT_TYPE = None
SECTION_SIZE = None
ART = None

PYAUD = None
STREAM = None
CHUNK = 1024
WIDTH = 3
CHANNELS = 2
RATE = 48000

RMS_MIN = float('-inf')
RMS_WINDOW_SIZE = 1.0
SAMPLES = []


def clear_rms():
    global SAMPLES
    SAMPLES = []


def get_recent_rms():
    rms_values = []

    for i in xrange(0, len(SAMPLES), CHUNK):
        if (i+RMS_WINDOW_SIZE) < len(SAMPLES):
            window = np.asarray(SAMPLES[i:i+int(RMS_WINDOW_SIZE*RATE)])
            b, a = A_weighting(RATE)
            window = lfilter(b, a, window, 0)
            rms = np.sqrt(np.mean(window**2))
            if rms:
                rms_values.append(20 * np.log10(rms /
                                                (2**(WIDTH*8-1) - 1)) + 3)
            else:
                rms_values.append(RMS_MIN)
    current = RMS_MIN
    for i in rms_values:
        if i == RMS_MIN and current != RMS_MIN:
            break
        current = max(i, current)
    return round(current, 1)


def audio_callback(in_data, frame_count, time_info, status):
    global SAMPLES

    for j in xrange(CHUNK):
        d = in_data[j*CHANNELS*WIDTH:(j+1)*CHANNELS*WIDTH]
        if WIDTH == 2:
            l = struct.unpack("<h", d[:WIDTH])[0]
            r = struct.unpack("<h", d[WIDTH:])[0]
        if WIDTH == 3:
            l = struct.unpack("<i", d[:WIDTH] +
                              ('\x00' if d[:WIDTH][-1] < '\x80'
                               else '\xff'))[0]
            r = struct.unpack("<i", d[WIDTH:] +
                              ('\x00' if d[WIDTH:][-1] < '\x80'
                               else '\xff'))[0]
        SAMPLES.append((l, r))
    return (None, pyaudio.paContinue)


def send_cc(cc_num, val):
    MIDI_OUT.send_message([0xB0 + MIDI_CHANNEL, cc_num, val])


def send_note(note_num, velo, sleep=0.25):
    MIDI_OUT.send_message([0x90 + MIDI_CHANNEL, note_num, velo])
    time.sleep(sleep)
    MIDI_OUT.send_message([0x90 + MIDI_CHANNEL, note_num, 0])


def patch_change(patch_num):
    MIDI_OUT.send_message([0xC0 + MIDI_CHANNEL, patch_num])


def try_guess(exp, velo, notes, vol, sleep=0.25):
    send_cc(7, vol)
    send_cc(11, exp)
    send_cc(1, velo)
    clear_rms()
    STREAM.start_stream()
    for j in notes:
        send_note(j, velo, sleep)
    STREAM.stop_stream()
    send_cc(120, 127)  # all sounds off
    time.sleep(0.05)
    return get_recent_rms()


def sound_check():
    global RMS_WINDOW_SIZE
    correct_rms_ws = RMS_WINDOW_SIZE
    send_cc(7, 127)
    send_cc(11, 127)
    send_cc(1, 127)
    clear_rms()
    STREAM.start_stream()
    for i in xrange(24, 100):
        MIDI_OUT.send_message([0x90 + MIDI_CHANNEL, i, 127])
    time.sleep(0.25)
    for i in xrange(24, 100):
        MIDI_OUT.send_message([0x90 + MIDI_CHANNEL, i, 0])
    STREAM.stop_stream()
    send_cc(120, 127)
    time.sleep(3)
    RMS_WINDOW_SIZE = correct_rms_ws
    return get_recent_rms()


# find notes that works
def find_notes():
    global RMS_WINDOW_SIZE
    correct_rms_ws = RMS_WINDOW_SIZE
    RMS_WINDOW_SIZE = 0.3
    notes = []
    print 'looking for notes...'
    for i in xrange(24, 100):
        output_rms = try_guess(127, 64, [i], 127)
        if output_rms > -90:  # != RMS_MIN:
            print 'found working note: %d (at %f)' % (i, output_rms)
            notes.append(i)
    RMS_WINDOW_SIZE = correct_rms_ws
    print 'working notes: %s' % str(notes)
    return notes


def section_size():
    if INSTRUMENT == 'winds' and SECTION_SIZE == 'ensemble':
        return 10
    if SECTION_SIZE[0] == 'a':  # e.g., a2
        return int(SECTION_SIZE[1:])
    if SECTION_SIZE[0] == 'd':  # to cut section sizes for string divs
        return -int(SECTION_SIZE[1:])
    return 1  # e.g., solo, section
    

def config(fn):
    global PYAUD, STREAM, MIDI_OUT, MIDI_CHANNEL, LIBRARY, INSTRUMENT, \
        SECTION_SIZE, INSTRUMENT_TYPE

    config_line = fn.split('/')[-1].split('.txt')[0]
    config_line = config_line.split('-')

    MIDI_CHANNEL = int(config_line[0]) - 1

    if MIDI_CHANNEL == 0:
        audio_device = 'Loopback Audio'
    else:
        audio_device = 'Loopback Audio %d' % (MIDI_CHANNEL + 1)

    LIBRARY = fn.split('/')[-2]
    INSTRUMENT = config_line[1]

    if 'cinewinds' in LIBRARY:
        INSTRUMENT_TYPE = 'winds'
    if 'woodwinds' in LIBRARY:
        INSTRUMENT_TYPE = 'winds'
    if LIBRARY == 'spitfire_brass':
        INSTRUMENT_TYPE = 'brass'
    if 'lass' in LIBRARY:
        INSTRUMENT_TYPE = 'strings'
    if LIBRARY == 'spitfire_chamber_strings':
        INSTRUMENT_TYPE = 'strings'
    if INSTRUMENT_TYPE == 'brass' and 'horn' in INSTRUMENT:
        INSTRUMENT_TYPE = 'quiet brass'

    SECTION_SIZE = config_line[2] if len(config_line) > 2 else 'solo'

    PYAUD = pyaudio.PyAudio()

    for i in xrange(PYAUD.get_device_count()):
        if audio_device == PYAUD.get_device_info_by_index(i)['name']:
            audio_device = i
            break

    STREAM = PYAUD.open(format=PYAUD.get_format_from_width(WIDTH),
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=audio_device,
                        stream_callback=audio_callback,
                        frames_per_buffer=CHUNK)

    MIDI_OUT = rtmidi.MidiOut()

    for i, port in enumerate(MIDI_OUT.ports):
        if MIDI_DEVICE_NAME == port:
            midi_device = i
            break

    MIDI_OUT.open_port(midi_device)
    STREAM.stop_stream()


def close():
    STREAM.close()
    PYAUD.terminate()
    

def takespread(sequence, num):
    length = float(len(sequence))
    for i in range(num):
        yield sequence[int(ceil(i * length / num))]


def midi_cap(v):
    return min(max(v, 1), 127)


def get_target(i):
    if section_size() >= 0:
        target = EXPECTED_RMS[INSTRUMENT_TYPE][i] + \
             DOUBLING_TO_DB * log(section_size(), 2) + AUDIO_RMS_OFFSET
    else:  # negative
        target = EXPECTED_RMS[INSTRUMENT_TYPE][i] + \
             DOUBLING_TO_DB * section_size() + AUDIO_RMS_OFFSET
    if 'pizz' in ART:
        target -= 6
    return target


def set_gain(notes):
    global VOL
    VOL, exp, target, output_rms = binary_search(
        64, get_target(5), [notes[len(notes)/2]], True)
    print 'Set gain: DONE using %d, wanted %f, got %f (diff:%f)' % \
        (VOL, target, output_rms, abs(target - output_rms))


def binary_search(velo, target, notes, find_vol=False):
    vol = VOL
    first = -30
    last = 150
    results = {}
    while first <= last:
        midpoint = (first + last) / 2
        if find_vol:
            exp = 64
            vol = midpoint
            if vol < 0 or vol > 127:
                vol = midi_cap(vol)
                break
        else:
            exp = midpoint
            if exp < 0:
                vol = VOL + exp
            elif exp > 127:
                vol = VOL + (exp - 127)
            else:
                vol = VOL
        output_rms = try_guess(midi_cap(exp), velo, notes, vol)
        results[(vol, midi_cap(exp), output_rms)] = abs(output_rms - target)
        print '%d: tried vol %d, exp %d, wanted %f, got %f' % (
            velo, vol, midi_cap(exp), target, output_rms)
        if abs(output_rms - target) < MAX_RMS_ERROR:
            break
        if output_rms < target:
            first = midpoint + 1
        else:
            last = midpoint - 1
    (vol, exp, output_rms), _ = min(results.items(), key=lambda x: x[1])
    return (vol, exp, target, output_rms)


def main():
    global ART
    if len(sys.argv) < 2:
        print 'usage: %s config.txt' % sys.argv[0]
        sys.exit(-1)

    config(sys.argv[1])
    config_lines = open(sys.argv[1]).read().split('\n')[:-1]
    
    for patch, ART in enumerate(config_lines):
        if ART[0] == '#':
            continue

        if section_size() > 1:
            file_path = '%s/%s_%s/%s.emap' % (LIBRARY,
                                              INSTRUMENT, SECTION_SIZE, ART)
        else:
            file_path = '%s/%s/%s.emap' % (LIBRARY, INSTRUMENT, ART)

        print 'working on %s' % file_path

        patch_change(patch)

        print 'sound checking...'
        if sound_check() < -90:
            print "No sound... audio not working?"
            continue
        print 'sound check okay...'

        print 'finding notes'
        notes = find_notes()
        if len(notes) == 0:
            print "couldn't find any notes... audio not working?"
            continue

        if len(notes) > 4:
            notes = list(takespread(notes, 4))
        print 'pared notes down to %s' % str(notes)

        set_gain(notes)

        expression_map = collections.OrderedDict()
        for i, velo in enumerate(DYNAMICS.values()):
            expression_map[velo] = emd = binary_search(velo, get_target(i), notes)
            print '%d: DONE using %d, %d, wanted %f, got %f (diff:%f)' % \
                (velo, emd[0], emd[1], emd[2], emd[3], abs(emd[2]-emd[3]))

        # mute this patch now that we're done.
        send_cc(7, 0)
        send_cc(11, 0)

        if not os.path.exists(os.path.split(file_path)[0]):
            os.makedirs(os.path.split(file_path)[0])
        ofp = open(file_path, 'w')
        for k, v in expression_map.items():
            ofp.write('%d\t%s\n' % (k, str(v)))
        ofp.close()
    close()


if __name__ == "__main__":
    main()
