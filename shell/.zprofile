#!/usr/bin/env zsh

if [ -z "$WAYLAND_DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec uwsm start hyprland.desktop
fi

