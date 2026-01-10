#!/usr/bin/env bash

YAZI_DIR=$1
NORM_DIR=$(echo "${YAZI_DIR}" | sed "s/^'//; s/'$//; s/''//")
WORK_DIR=$(echo "${NORM_DIR}" | sed 's/music\/\(archived\|disposable\|main\|review\)/metadata/g')
WORK_DIR=$(echo "${WORK_DIR}" | sed "s|\\\||")

kitty -d "$WORK_DIR" nvim info.toml
