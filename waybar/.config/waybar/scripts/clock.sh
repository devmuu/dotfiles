#!/bin/sh

# variables
t=0

# functions
toggle() {
    t=$(((t + 1) % 2))
}

# wait signal to toggle date format
trap "toggle" USR1

# calendar icon
ICON_CAL="🗓️"

# Output
while true; do
    CLOCK=$(date '+%I')
    case "${CLOCK}" in
        "00") ICON_HOUR="🕛" ;;
        "01") ICON_HOUR="🕐" ;;
        "02") ICON_HOUR="🕑" ;;
        "03") ICON_HOUR="🕒" ;;
        "04") ICON_HOUR="🕓" ;;
        "05") ICON_HOUR="🕔" ;;
        "06") ICON_HOUR="🕕" ;;
        "07") ICON_HOUR="🕖" ;;
        "08") ICON_HOUR="🕗" ;;
        "09") ICON_HOUR="🕘" ;;
        "10") ICON_HOUR="🕙" ;;
        "11") ICON_HOUR="🕚" ;;
        "12") ICON_HOUR="🕛" ;;
    esac

    if [ $t -eq 0 ]; then
        echo "${ICON_HOUR} $(date "+%H:%M") ${ICON_CAL} $(date "+%d/%m")"
    else
        echo "${ICON_CAL} $(date "+%A, %d de %B") ${ICON_HOUR} $(date "+%H:%M:%S")"
    fi

    sleep 1 &
    wait
done
