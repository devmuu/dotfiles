#!/usr/bin/env bash

OPTION=$1

STYLE="default"
CONFIG_FILE="config"
WAYBAR_DIR="$HOME/.config/waybar"

stop_all(){
    killall waybar > /dev/null 2>&1
}

start(){
    if [[ ${XDG_CURRENT_DESKTOP} == "Hyprland" ]]; then
        waybar -s "${WAYBAR_DIR}/style.css" -c "${WAYBAR_DIR}/bars/hypr.jsonc" > /dev/null 2>&1 &
    else
        echo "Unknown desktop";
    fi
}

case ${OPTION} in
    start)
        stop_all
        start
    ;;
    stop)
        stop_all
    ;;
    *)
        echo "Restarting waybar in ${XDG_CURRENT_DESKTOP}"
        stop_all
        start
    ;;
esac
