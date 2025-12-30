#!/usr/bin/env bash

IME=$(fcitx5-remote -n)

case "$IME" in
  keyboard-us) echo "🇺🇸" ;;
  *) echo "🇧🇷" ;;
esac
