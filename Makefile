#!/bin/bash

# ==============================================================================
# Program:       Makefile
# Description:   Makefile to manage dotfiles
# Software/Tool: Makefile
# ==============================================================================

stow:
	stow --no-folding hyprland imv kitty mako mpd mpv nvim pipewire rmpc scripts shell starship udiskie waybar wofi yazi zathura

links:
	mkdir -p ~/.local/share/media
	ln -sf $(AUDIO_DIR)/archived $(HOME)/.local/share/media/archived
	ln -sf $(AUDIO_DIR)/musics $(HOME)/.local/share/media/musics
	ln -sf $(AUDIO_DIR)/playlists/mpd $(HOME)/.local/share/media/playlists

.PHONY: stow links
