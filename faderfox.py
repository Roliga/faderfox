#!/bin/python

import pygame.midi as midi
import pulsectl
import enum
import json
from os import environ
from os.path import exists, abspath
from time import sleep

class PulseType(enum.Enum):
    Sink = 0,
    Source = 1,
    SinkInput = 2,
    SourceOutput = 3,
    Command = 4

def json_pulse_type(dct):
    if 'type' in dct:
        type_str = str(dct['type']).lower().strip('_ ')
        if type_str == 'sink':
            dct['type'] = PulseType.Sink
        elif type_str == 'source':
            dct['type'] = PulseType.Source
        elif type_str == 'sinkinput':
            dct['type'] = PulseType.SinkInput
        elif type_str == 'sourceoutput':
            dct['type'] = PulseType.SourceOutput
    return dct

def get_midi_device(name):
    device_id = 0
    while midi.get_device_info(device_id):
        device_info = midi.get_device_info(device_id)
        if device_info[1].decode('utf-8') == name and device_info[2] == 1:
            return midi.Input(device_id)
        device_id += 1

    print(f"Can't find MIDI device: {name}")
    exit(1)

def set_volume(obj, volume):
    pulse.volume_set_all_chans(obj, float(value) / 127.0)

def match_proplist(search_fields, proplist):
    for prop_name, prop_value in search_fields.items():
        if (prop_name in proplist and proplist[prop_name] == prop_value):
            return True
    return False

def get_config():
    if exists('./config.json'):
        config_path = './config.json'
    else:
        if 'XDG_CONFIG_HOME' in environ:
            config_home = environ['XDG_CONFIG_HOME']
        elif 'HOME' in environ:
            config_home = environ['HOME'] + '/.config'

        config_path = config_home + '/faderfox/config.json'
        print(abspath(config_path))

        if not exists(config_path):
            print('No mapping configuration found')
            exit(1)

    print(f"Using config at: {abspath(config_path)}")

    with open(config_path, 'r') as fp:
        return json.load(fp, object_hook=json_pulse_type)

config = get_config()
poll_rate = config['poll_rate']
device_name = config['device_name']
mappings = config['mappings']

midi.init()
device = get_midi_device(device_name)

with pulsectl.Pulse('faderfox-driver') as pulse:
    while True:
        if device.poll():
            done_channels = []
            events = device.read(100)
            # if (len(events) > 0):
            #     print(events)
            for event in events[::-1]:
                status = event[0][0]
                channel = event[0][1]
                value = event[0][2]
                something = event[0][3]
                timestamp = event[1]

                # Events are processed newest to oldest,
                # so discard any but the most recent event for each channel
                if channel in done_channels:
                    continue
                done_channels.append(channel)

                if status == 176 and str(channel) in mappings:
                    mapping = mappings[str(channel)]

                    pulse_objects = []
                    if mapping['type'] == PulseType.Sink:
                        pulse_objects = pulse.sink_list()
                    elif mapping['type'] == PulseType.Source:
                        pulse_objects = pulse.source_list()
                    elif mapping['type'] == PulseType.SinkInput:
                        pulse_objects = pulse.sink_input_list()
                    elif mapping['type'] == PulseType.SourceOutput:
                        pulse_objects = pulse.source_output_list()

                    for pulse_object in pulse_objects:
                        if ('name_filter' in mapping and
                            pulse_object.name == mapping['name_filter'] or
                            'proplist_filters' in mapping and
                            match_proplist(mapping['proplist_filters'], pulse_object.proplist)):
                                set_volume(pulse_object, value)

        sleep(1.0 / poll_rate) # Sets poll rate per second
