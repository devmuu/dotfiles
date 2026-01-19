#!/usr/bin/env bash

OPT=$1

VOL_ICON=""
MUTE_ICON="󰝟"

MASTER_SINK=$(pactl list short sinks | grep -v mono_sink | awk '{print $2}')

VOL_VALUE=$(pactl get-sink-volume ${MASTER_SINK} | awk '{print $5}' | head -n1)
MUTE_STATE=$(pactl get-sink-mute ${MASTER_SINK} | awk '{print $2}')


case "${OPT}" in
  value)
      if [[ ${MUTE_STATE} == "no" ]]; then
          echo "${VOL_ICON} ${VOL_VALUE}"
      else
          echo "${MUTE_ICON} ${VOL_VALUE}"
      fi
  ;;
  *) echo "" ;;
esac
