#!/usr/bin/env bash

IMAGE=${1}
OUT_IMAGE="cover0.jpg"

magick "${IMAGE}" \
    -gravity West -chop ${2}x0 \
    -gravity East -chop ${3}x0 \
    -gravity North -chop 0x${4} \
    -gravity South -chop 0x${5} \
    "${OUT_IMAGE}"
