#!/bin/bash
#
# check-rtltcp.sh - health check for rtl_tcp, meant to be called by
# the `watchdog` daemon as its `test-binary`.
#
# rtl_tcp only services ONE client at a time (it blocks in accept()
# until the current client disconnects), so we can't open a second
# TCP connection to probe it -- that just hangs behind whatever's
# already connected (e.g. rtlamr). Instead we watch the journal for
# the USB/i2c failure signature that shows up when the dongle drops
# off the bus (rtlsdr_demod_*_reg failed with -4, r82xx_* failed=-4,
# etc).
#
# Exit 0 = healthy, exit nonzero = unhealthy (watchdog stops petting
# the hardware watchdog device -> reboot after watchdog-timeout
# unless something else recovers first).

SERVICE_NAME="rtl_tcp"        # adjust to your systemd unit name if different
STATE_FILE="/var/run/check-rtltcp.last"
ERROR_THRESHOLD=5             # how many failed=-4 style lines within the window counts as unhealthy

# 1. Is rtl_tcp even running?
if ! pgrep -x rtl_tcp >/dev/null 2>&1; then
    echo "rtl_tcp process not found" >&2
    exit 1
fi

# 2. Figure out the time window to scan: since the last time this
#    script ran (falls back to "10 minutes ago" on first run).
if [ -f "$STATE_FILE" ]; then
    since=$(cat "$STATE_FILE")
else
    since=$(date -d '10 minutes ago' '+%Y-%m-%d %H:%M:%S')
fi
now=$(date '+%Y-%m-%d %H:%M:%S')
echo "$now" > "$STATE_FILE"

# 3. Count USB/i2c failure lines from rtl_tcp's journal output in
#    that window. journalctl -u only works if rtl_tcp runs as a
#    systemd unit and logs via the standard journal; adjust the
#    grep source if you're logging elsewhere (e.g. a plain logfile).
error_count=$(journalctl -u "$SERVICE_NAME" --since "$since" --until "$now" 2>/dev/null \
    | grep -Ec 'failed=-4|failed with -4|Failed to submit transfer')

if [ "$error_count" -ge "$ERROR_THRESHOLD" ]; then
    echo "rtl_tcp logged $error_count USB failure lines since $since" >&2
    exit 1
fi

exit 0
