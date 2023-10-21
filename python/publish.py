#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import os
import re
import sys

"""
Class to read Water and Gas meter consumption data from 
bemasher/rtlamr stdout, and publish as MQTT messages using the homie convention.
"""


class MeterReader:
    verbose = False
    client = None

    mqtt_host = '192.168.1.5'
    mqtt_port = 1883
    device_name = 'meter-reader'

    def __init__(self):
        if os.getenv('VERBOSE'):
            self.verbose = True
        else:
            self.verbose = False

        if os.getenv('MQTT_HOST'.upper()):
            self.mqtt_host = os.getenv('MQTT_HOST'.upper())

        if os.getenv('MQTT_PORT'.upper()):
            self.mqtt_port = int(os.getenv('MQTT_PORT'.upper()))

        if os.getenv('device_name'.upper()):
            self.device_name = os.getenv('device_name'.upper())

        self.client = mqtt.Client()
        self.client.will_set(f'homie/{self.device_name}/$state', payload='lost', qos=1, retain=True)
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.client.loop_start()

        self.homie_setup_msgs = [
            (f'homie/{self.device_name}/$homie', '4.0'),
            (f'homie/{self.device_name}/$name', 'RTL AMR Meter Reader'),
            (f'homie/{self.device_name}/$state', 'init'),
            (f'homie/{self.device_name}/$nodes', 'gas-meter,water-meter'),

            (f'homie/{self.device_name}/gas-meter/$name', 'Natural Gas Meter'),
            (f'homie/{self.device_name}/gas-meter/$properties', 'consumption'),
            (f'homie/{self.device_name}/gas-meter/consumption/$name', 'Gas Consumption'),
            (f'homie/{self.device_name}/gas-meter/consumption/$unit', 'Cubic Feet'),
            (f'homie/{self.device_name}/gas-meter/consumption/$datatype', 'integer'),

            (f'homie/{self.device_name}/water-meter/$name', 'Water Meter'),
            (f'homie/{self.device_name}/water-meter/$properties', 'consumption'),
            (f'homie/{self.device_name}/water-meter/consumption/$name', 'Water Consumption'),
            (f'homie/{self.device_name}/water-meter/consumption/$unit', 'Cubic Feet'),
            (f'homie/{self.device_name}/water-meter/consumption/$datatype', 'integer'),
            (f'homie/{self.device_name}/$state', 'ready')
        ]

        for top, msg in self.homie_setup_msgs:
            self.client.publish(top, payload=msg, qos=1, retain=True)

    def publish_gas(self, val):
        self.ready()
        self.client.publish(f'homie/{self.device_name}/gas-meter/consumption', payload=val, qos=1, retain=True);

    def publish_water(self, val):
        self.ready()
        self.client.publish(f'homie/{self.device_name}/water-meter/consumption', payload=val, qos=1, retain=True);

    def ready(self):
        self.client.publish(f'homie/{self.device_name}/$state', payload='ready', qos=1, retain=True);

    def close(self):
        self.client.publish(f'homie/{self.device_name}/$state', payload='disconnected', qos=1, retain=True)
        self.client.loop_stop();
        self.client.disconnect();
        self.client = None

    def __del__(self):
        if self.client:
            self.close()


if __name__ == "__main__":
    mr = None
    exit_code = 0
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
            fs = re.findall(r'^.*?Consumption:\s*(\d+).*$', line)
            if re.match(r'^.*?ID:37968541', line):
                mr.publish_gas(fs[0])
            elif re.match(r'^.*?ID:34763104', line):
                mr.publish_water(fs[0])

    except KeyboardInterrupt:
        print("Interrupted")
        exit_code = 2
    except Exception as e:
        print(e)
        exit_code = 3
    finally:
        if mr:
            mr.close()
        sys.exit(exit_code)
