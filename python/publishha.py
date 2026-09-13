#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import json
import os
import re
import sys

"""
Class to read Water and Gas meter consumption data from
bemasher/rtlamr stdout, and publish as MQTT messages using
Home Assistant's native MQTT discovery convention.

See: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
"""


class MeterReader:
    verbose = False
    client = None

    mqtt_host = '192.168.1.4'
    mqtt_port = 1883
    device_name = 'meter-reader'
    discovery_prefix = 'homeassistant'

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

        if os.getenv('DISCOVERY_PREFIX'):
            self.discovery_prefix = os.getenv('DISCOVERY_PREFIX')

        mqtt_user = os.getenv('MQTT_USER')
        mqtt_password = os.getenv('MQTT_PASSWORD')
        if not mqtt_password and os.getenv('MQTT_PASSWORD_FILE'):
            with open(os.getenv('MQTT_PASSWORD_FILE'), 'r') as f:
                mqtt_password = f.read().strip()

        self.availability_topic = f'{self.device_name}/status'
        self.gas_state_topic = f'{self.device_name}/gas-meter/consumption'
        self.water_state_topic = f'{self.device_name}/water-meter/consumption'

        self.client = mqtt.Client()
        if mqtt_user:
            self.client.username_pw_set(mqtt_user, mqtt_password)
        self.client.will_set(self.availability_topic, payload='offline', qos=1, retain=True)
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.client.loop_start()

        # Home Assistant MQTT discovery device block, shared across entities.
        device = {
            'identifiers': [self.device_name],
            'name': 'RTL AMR Meter Reader',
            'model': 'rtlamr',
            'manufacturer': 'bemasher',
        }

        gas_config = {
            'name': 'Gas Consumption',
            'unique_id': f'{self.device_name}-gas-meter-consumption',
            'state_topic': self.gas_state_topic,
            'availability_topic': self.availability_topic,
            'payload_available': 'online',
            'payload_not_available': 'offline',
            'unit_of_measurement': 'ft\u00b3',
            'device_class': 'gas',
            'state_class': 'total_increasing',
            'device': device,
        }

        water_config = {
            'name': 'Water Consumption',
            'unique_id': f'{self.device_name}-water-meter-consumption',
            'state_topic': self.water_state_topic,
            'availability_topic': self.availability_topic,
            'payload_available': 'online',
            'payload_not_available': 'offline',
            'unit_of_measurement': 'ft\u00b3',
            'device_class': 'water',
            'state_class': 'total_increasing',
            'device': device,
        }

        self.ha_setup_msgs = [
            (f'{self.discovery_prefix}/sensor/{self.device_name}/gas-meter-consumption/config',
             json.dumps(gas_config)),
            (f'{self.discovery_prefix}/sensor/{self.device_name}/water-meter-consumption/config',
             json.dumps(water_config)),
        ]

        for top, msg in self.ha_setup_msgs:
            self.client.publish(top, payload=msg, qos=1, retain=True)

        self.client.publish(self.availability_topic, payload='online', qos=1, retain=True)

    def publish_gas(self, val):
        self.ready()
        self.client.publish(self.gas_state_topic, payload=val, qos=1, retain=True);

    def publish_water(self, val):
        self.ready()
        self.client.publish(self.water_state_topic, payload=val, qos=1, retain=True);

    def ready(self):
        self.client.publish(self.availability_topic, payload='online', qos=1, retain=True);

    def close(self):
        self.client.publish(self.availability_topic, payload='offline', qos=1, retain=True)
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
