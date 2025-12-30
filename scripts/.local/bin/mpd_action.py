#!/usr/bin/env python

# ==============================================================================
# Program:       mpd-cover-notify
# Description:   Get file cover metadata
# Software/Tool: python3.10.0/eyed3/toml
# ==============================================================================

import os
import subprocess
import dbus
import re
import time
import argparse
import logging
import musicpd
import eyed3
from eyed3.id3.frames import ImageFrame

# variables
HOME_ENV = os.environ.get('HOME')
AUDIO_DIR = os.environ.get('AUDIO_DIR')
GENERIC_THUMB = f'{AUDIO_DIR}/metadata/cover.jpg'
GENERIC_FOLDER = f'{AUDIO_DIR}/metadata/folder.jpg'

THUMB_NAME = '/tmp/cover.jpg'

# settints
logging.getLogger().setLevel('ERROR')

parser = argparse.ArgumentParser(description="Send notification and get current cover art album.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    "--artist",
    action="store_true",
    default=False,
    help="Show current artist cover",
)
group.add_argument(
    "--cover",
    action="store_true",
    default=False,
    help="Show current album cover",
)
group.add_argument(
    "--notify",
    action="store_true",
    default=False,
    help="Send system notification",
)
args = parser.parse_args()


# send notification via dbus
def send_notify() -> None:
    # get current song values
    song_info = get_song_info()

    if song_info == {''}:
        artist = "mpd stopped"
        title = "No current song in mpd"
        IMG = GENERIC_THUMB
    else:
        artist = song_info['artist']
        title = song_info['title']
        IMG = THUMB_NAME

    notification_id = 0
    image_uri = f"file://{THUMB_NAME}"

    # TODO: Update to libnotify only (maybe not work in gnome)

    # D-BUS notification service
    notify_server = "org.freedesktop.Notifications"
    # notification server path
    notify_path = "/"+notify_server.replace('.', '/')
    # get notification object
    notify = dbus.Interface(dbus.SessionBus().get_object(notify_server, notify_path), notify_server)

    # send notification (name/ID/icon/summary/body/actions/hints/timeout)
    # work in mako, not in gnome
    # notify.Notify("mpd", 0, IMG, artist, title, [], {"urgency": 1, "category": "mpd"}, 1000)

    notify.Notify("mpd", notification_id, "music-app", title, artist, [],
              {"urgency": 1, "category": "mpd", "image-path": image_uri},
              1000)


# get info of current song
def get_song_info() -> list:
    # connet to mpd client to get current song info
    client = musicpd.MPDClient()
    client.connect()

    if client.status()['state'] == 'stop':
        output = {''}
    else:
        filename = client.currentsong()["file"]
        title = client.currentsong()["title"]
        artist = client.currentsong()["artist"]

        # if multiple artist, show only first
        if isinstance(artist, list):
            artist = artist[0]

        output = {'artist': artist, 'title': title, 'file': filename}

    # disconnect from client and send list
    client.disconnect()
    return output


# get split size from stty
def get_term_size() -> str:
    x,y = os.get_terminal_size()
    return f'{x}x{y}'


# show album or artist image in terminal using kitty icat
def show_image() -> None:
    size_value = get_term_size()
    song_info = get_song_info()

    if song_info == {''}:
        if args.artist:
            IMG = GENERIC_FOLDER
        else:
            IMG = GENERIC_THUMB
    else:
        if args.artist:
            IMG = f'{AUDIO_DIR}/metadata/Artists/{song_info["artist"]}/folder.jpg'
        else:
            save_embedded_cover()
            IMG = THUMB_NAME

    subprocess.Popen(['clear'])
    icat_cmd = ['kitten', 'icat', '--clear', '-n', '--transfer-mode=file', '--place',
            f'{size_value}@0x0', '--align=center', f'{IMG}']
    subprocess.Popen(icat_cmd)


# get embedded album cover from mp3 file and save it
def save_cover() -> None:
    info = get_song_info()

    if info == {''}:
        filename = ''
    else:
        filename = get_song_info()["file"]

    if  filename:
        song_file = re.sub('\n', '', f'{AUDIO_DIR}/{filename}')
        tag_file = eyed3.load(song_file)
        audioImage = [data.image_data for data in tag_file.tag.images]

        # Save current image
        with open(THUMB_NAME, "wb") as handler:
            handler.write(audioImage[0])


def save_embedded_cover() -> None:
    # connet to mpd client to get current song info
    client = musicpd.MPDClient()
    client.connect()

    # get filename and image data
    filename = client.currentsong()["file"]
    file_img = client.readpicture(filename, 0)

    if not file_img:
        print("No image")
        sys.exit(1)

    size = int(file_img['size'])
    done = int(file_img['binary'])

    with open(THUMB_NAME, 'wb') as cover:
        cover.write(file_img['data'])

        while size > done:
            file_img = client.readpicture(filename, done)
            done += int(file_img['binary'])
            cover.write(file_img['data'])

    # disconnect from client and send list
    client.disconnect()


def main() -> None:
    """main"""

    # check mode option
    if args.notify:
        save_embedded_cover()
        send_notify()
    else:
        # show current image first
        show_image()
        # create mpd client instance
        cli = musicpd.MPDClient()

        try:
            cli.connect()
            while True:
                # save current song id
                if cli.currentsong() == {} or cli.status()['state'] == 'stop':
                    song_id = -1
                    show_image()
                else:
                    song_id = cli.currentsong()['id']

                # send idle event to fetch
                cli.send_idle()

                # wait change status after send idle event
                if cli.fetch_idle():
                    currentsong = cli.currentsong()
                    # only change image if different song
                    if currentsong != {}:
                        current_id = currentsong['id']
                        if current_id != song_id:
                            show_image()
        except (OSError, musicpd.MPDError) as err:
            if cli._sock is not None:
                cli.disconnect()
        except KeyboardInterrupt:
            pass


# run only in self, not in module
if __name__ == "__main__":
    main()
