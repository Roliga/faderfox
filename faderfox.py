#!/bin/python

import pulsectl
import enum
import json
from os import environ
from os.path import exists, abspath
from time import sleep
from rtmidi.midiutil import open_midiinput

# TODO: Handle device disconnects
# TODO: Execute commands on value change
# TODO: Pipe values to sub process?
# TODO: Verbose output for debugging

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

midiin, port_name = open_midiinput(port=device_name, interactive=False)
print(f"Opened MIDI device: {port_name}")

with pulsectl.Pulse('faderfox-driver') as pulse:
    while True:
        msg = midiin.get_message()
        if msg:
            message, deltatime = msg
            status, channel, value = message

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
        else:
            sleep(1.0 / poll_rate) # Sets poll rate per second
