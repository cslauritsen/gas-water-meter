#!/bin/bash
# Check if the rtlamr process is publishing data to MQTT
# If not, reboot the pi

set -euo pipefail

threshold=300  # 5 minutes in seconds
tmp=$(mktemp -d)
# Temporary file to track last message time
timestamp_file="$tmp/rtlamr_last_msg"

date +%s > "$timestamp_file"
# Timeout watcher: check every 60s if >5m since last message
watchdog_pid=
start_watchdog() {
  (
    while sleep 60; do
      if [[ -f "$timestamp_file" ]]; then
        last_msg=$(< "$timestamp_file")
        current_time=$(date +%s)
        if [[ $((current_time - last_msg)) -gt $threshold ]]; then
          echo "No messages received in the last 5 minutes. Rebooting..."
          reboot
        fi
      fi
    done
  ) &
  watchdog_pid=$!
}

start_watchdog

# Listen for messages and update timestamp
mosquitto_sub -v -h ${MQTT_HOST:-192.168.1.4} -u ${MQTT_USER:-rtl} \
  -P ${MQTT_PASSWORD:-$(< ~/secrets/rtl_pass )} \
  -t 'meter-reader/+/consumption' \
  | while read publication
  do
    date +%s > "$timestamp_file"
  done
