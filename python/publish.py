#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import os
import re
import sys

homie_setup_msgs = [
	('homie/meter-reader/$homie' , '4.0'),
	('homie/meter-reader/$name' , 'RTL AMR Meter Reader'),
	('homie/meter-reader/$state' , 'init'),
	('homie/meter-reader/$nodes' , 'gas-meter,water-meter'),

	('homie/meter-reader/gas-meter/$name' , 'Natural Gas Meter'),
	('homie/meter-reader/gas-meter/$properties' , 'consumption'),
	('homie/meter-reader/gas-meter/consumption/$name' , 'Gas Consumption'),
	('homie/meter-reader/gas-meter/consumption/$unit' , 'Cubic Feet'),
	('homie/meter-reader/gas-meter/consumption/$datatype' , 'integer'),

	('homie/meter-reader/water-meter/$name' , 'Water Meter'),
	('homie/meter-reader/water-meter/$properties' , 'consumption'),
	('homie/meter-reader/water-meter/consumption/$name' , 'Water Consumption'),
	('homie/meter-reader/water-meter/consumption/$unit' , 'Cubic Feet'),
	('homie/meter-reader/water-meter/consumption/$datatype' , 'integer'),
	('homie/meter-reader/$state' , 'ready')
]


class MeterReader:
    verbose = False
    client = None

    def __init__(self):
        if os.getenv('HOMIE_RTLAML_VERBOSE'):
            self.verbose = True
        else:
            self.verbose = False
        self.client = mqtt.Client()
        self.client.will_set('homie/meter-reader/$state', payload='lost', qos=1, retain=True)
        self.client.connect('192.168.1.5', 1883, 60)
        self.client.loop_start()
        for top,msg in homie_setup_msgs:
            self.client.publish(top, payload=msg, qos=1, retain=True)

    def publish_gas(self, val):
        self.ready()
        self.client.publish('homie/meter-reader/gas-meter/consumption', payload=val, qos=1, retain=True);

    def publish_water(self, val):
        self.ready()
        self.client.publish('homie/meter-reader/water-meter/consumption', payload=val, qos=1, retain=True);

    def ready(self):
        self.client.publish('homie/meter-reader/$state', payload='ready', qos=1, retain=True);

    def close(self):
        self.client.publish('homie/meter-reader/$state', payload='disconnected', qos=1, retain=True)
        self.client.loop_stop();
        self.client.disconnect();
        self.client = None

    def __del__(self):
        if self.client:
            self.close()

if __name__ == "__main__":
    mr = None
    try:
        mr = MeterReader()
        print('Connected to MQTT')

        # {Time:2021-01-25T15:41:00.452 SCM:{ID:37968541 Type:12 Tamper:{Phy:00 Enc:00} Consumption:  988708 CRC:0xF3CD}}
        # s/^.*?Consumption:\s*(\d+?)\s.*$/$1/;
        # have to call this way to avoid buffering when on on a tty
        for line in iter(sys.stdin.readline, ''):
            line.rstrip()
            if mr.verbose:
                print('INPUT: ', line)
            fs = re.findall('^.*?Consumption:\s*(\d+).*$', line)
            if re.match('^.*?ID:37968541', line):
                mr.publish_gas(fs[0])
            elif re.match('^.*?ID:34763104', line):
                mr.publish_water(fs[0])

    except KeyboardInterrupt:
        print('Interrupted!')
    finally:
        mr.close()
