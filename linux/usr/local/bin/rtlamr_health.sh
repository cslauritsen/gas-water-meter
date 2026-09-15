#!/bin/bash
# Check if the rtlamr process is publishing data to MQTT
# If not, reboot the pi

set -euo pipefail

threshold=300  # 5 minutes in seconds
tmp=$(mktemp -d)
# Temporary file to track last message time
timestamp_file="$tmp/rtlamr_last_msg"

echo "Starting rtlamr health check. Monitoring MQTT messages..."

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
          msg="RTLAMR HEALTH CHECK: No MQTT messages in ${threshold}s. Triggering reboot."
          echo "$msg"
          logger -t rtlamr-health -p user.crit "$msg"
          reboot
        else
          echo "Last MQTT message received $((current_time - last_msg)) seconds ago."
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
    echo "Received message: $publication"
  done
