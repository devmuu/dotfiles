#!/usr/bin/env bash

source ~/.userenv

WTTR="https://wttr.in/${CURRENT_CITY}?format=%m/%M+|+%c%t"

DATA=$(curl -s "${WTTR}" | tr -d ' ')
echo "${DATA}"
