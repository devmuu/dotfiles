#!/usr/bin/env bash

BLUETOOTH_STATE=$(bluetoothctl show | grep PowerState | awk '{print $2}')
NOTIFY_STATUS="-u low -c bluetooth"
ACTIVE_BLUETOOTH="/usr/share/icons/AdwaitaLegacy/48x48/status/bluetooth-active.png"
DISABLED_BLUETOOTH="/usr/share/icons/AdwaitaLegacy/48x48/status/bluetooth-disabled.png"

if [[ "${BLUETOOTH_STATE}" == "off" ]]; then
    notify-send ${NOTIFY_STATUS} -i ${ACTIVE_BLUETOOTH} "bluetoothctl" "bluetooth on"
    bluetoothctl power on
else
    notify-send ${NOTIFY_STATUS} -i ${DISABLED_BLUETOOTH} "bluetoothctl" "bluetooth off"
    bluetoothctl power off
fi
