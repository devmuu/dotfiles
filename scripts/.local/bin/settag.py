#!/usr/bin/env python

# ==============================================================================
# Program:       settag
# Description:   Set audio metadata
# Software/Tool: python3.10.0/eyed3/toml
# ==============================================================================

"""
- mp3 files are biding with track names in a toml file
- all files must begin with two digits track number

- image priority:
    1 - cover track defined by cover folder (if track is a list)
    2 - cover file defined by album-year keys in list track (if track is a list)
    3 - cover.jpg in file folder (same mp3 directory)
    4 - cover.jpg in album artist folder (same place toml file)
    5 - cover.jpg in artist folder (metadada folder)
    6 - generic cover in music directory
"""

import os
import argparse
import re
from functools import lru_cache

import toml
import eyed3
from eyed3.id3.frames import ImageFrame

# environment
AUDIO_DIR = os.environ.get('AUDIO_DIR')
METADATA_DIR = f'{AUDIO_DIR}/metadata'

# args
parser = argparse.ArgumentParser(description='Set music tags')
parser.add_argument(
    '-n',
    '--dry-run',
    action='store_true',
    help='Simulate without writing',
)
parser.add_argument(
    '-d',
    '--data',
    type=str,
    default='info.toml',
    help='Choose toml data file',
)
parser.add_argument(
    '-r',
    '--rename',
    type=str,
    choices=['dash', 'dot'],
    help='Rename from metadata',
)
parser.add_argument(
    '-f',
    '--format',
    type=str,
    default='mp3',
    choices=['mp3', 'mp4', 'wma'],
    help='File format',
)
args = parser.parse_args()

"""
Begin Helpers
"""

# get right digits in track name
def normalize_index(filename: str) -> str:
    match = re.match(r'(\d+)', filename)
    if not match:
        raise ValueError("No track number")
    return match.group(1).zfill(2)


# get first artist in multi artist tag
def first_artist(artist_field: str) -> str:
    return artist_field.split(";")[0].strip()


# to load toml file
@lru_cache(maxsize=256)
def load_toml(path: str):
    return toml.load(path)

"""
End Helpers
"""

def get_image(data_path, track_list, artist, idx) -> str:
    """get correct image for track"""

    # check if cover index image exists in same mp3 file folder
    single_img = f'covers/cover{idx}.jpg'
    if os.path.isfile(single_img):
        print(f"[COVER] Single Track Album image → {idx}")
        return single_img

    # block if track session is a list -> [[track]]
    if isinstance(track_list, list):
        idx_norm = int(idx) - 1
        track = track_list[idx_norm]

        # verify if album and year keys exists in current item
        if 'album' and 'year' in track_list[idx_norm]:
            # search album cover in artist path
            album_path = f'{track["year"]} - {track["album"]}'
            album_cover = f'{METADATA_DIR}/Artists/{artist}/{album_path}/cover.jpg'

            if os.path.isfile(album_cover):
                print(f"[COVER] Track Album image → {idx}")
                return album_cover

        # test track has image key and search for covers folder in data_path
        if 'image' in track:
            track_cover = os.path.join(data_path, track["image"])
            if os.path.isfile(track_cover):
                print(f"[COVER] Single track album image → {idx}")
                return track_cover

    # cover file in mp3 dir
    if os.path.isfile('cover.jpg'):
        print(f"[COVER] Directory cover → {idx}")
        return 'cover.jpg'

    # album cover in TOML folder
    album_cover = f"{data_path}/cover.jpg"
    if os.path.isfile(album_cover):
        print(f"[COVER] Album cover → {idx}")
        return album_cover

    # artist cover (first artist)
    primary_artist = first_artist(artist)
    artist_cover = f"{METADATA_DIR}/Artists/{primary_artist}/cover.jpg"
    if os.path.isfile(artist_cover):
        print(f"[COVER] Artist cover ({primary_artist}) → {idx}")
        return artist_cover

    # generic in metadata music path
    print(f"[COVER] Generic → {idx}")
    return f"{METADATA_DIR}/cover.jpg"


def write_tag(data_path, idx, file_name) -> None:
    """write tags"""
    toml_path = f"{data_path}/{f_data}"
    toml_data = load_toml(toml_path)

    stats = toml_data["stats"]
    tracks = toml_data["tracks"]

    album_artist = stats['artist']
    album = stats['album']
    disc = stats['discs'].split(',')
    year = stats['year']
    genre = stats['genre']
    total_tracks = len(tracks)

    # check if tracks info is a list
    if isinstance(tracks, list):
        idx_norm = int(idx) - 1
        track = tracks[idx_norm]
        title = track['title']
        artist = track['artist']
    else:
        title = tracks[f'track{idx}']
        artist = album_artist

    # get image from get_image method
    image = get_image(data_path, tracks, artist, idx)

    tag_file = eyed3.load(file_name)
    if not tag_file.tag:
        tag_file.initTag()

    # clear and set all tags
    tag_file.tag.clear()
    tag_file.tag.track_num = (int(idx), total_tracks)
    tag_file.tag.title = title
    tag_file.tag.album = album
    tag_file.tag.recording_date = year
    tag_file.tag.release_date = year

    # replace ';' character to null values '\x00' to separate multi values
    tag_file.tag.artist = artist.replace("; ", '\x00')
    tag_file.tag.album_artist = album_artist.replace("; ", '\x00')
    tag_file.tag.genre = genre.replace("; ", '\x00')

    # tag disc number
    tag_file.tag.disc_num = (int(disc[0]), int(disc[-1]))

    # clean tags with null value
    tag_file.tag.comments.set("null")
    tag_file.tag.publisher = "null"
    tag_file.tag.copyright = "null"

    # remove current images
    audioImageDescriptions = [audioImage.description for audioImage in tag_file.tag.images]
    for description in audioImageDescriptions:
        tag_file.tag.images.remove(description)

    # set image for front cover
    tag_file.tag.images.set(
        ImageFrame.FRONT_COVER,
        open(image, 'rb').read(),
        'image/jpeg'
    )
    tag_file.tag.save()
    print(f"[UPDATED] TAG → {os.path.basename(file_name)}")


def rename_file(file_name) -> None:
    """rename files"""
    # define correct separator and new filename
    sep = " - " if args.rename == "dash" else ". "
    tag_file = eyed3.load(file_name)
    # bar '/' it's not accepted in filenames
    title_corretion = re.sub('/', '-', tag_file.tag.title)
    # other characters to remove or change (keep this for more control)
    title_corretion = re.sub('\\?', '', title_corretion)
    title_corretion = re.sub('\\¿', '', title_corretion)
    title_corretion = re.sub('\\!', '', title_corretion)
    title_corretion = re.sub('\\*', '_', title_corretion)
    file_renamed = f'{tag_file.tag.track_num[0]:02}{sep}{title_corretion}'

    # only run a test
    if args.dry_run:
        print(f"[DRY-RUN] Would rename → {file_renamed}")
        return

    try:
        tag_file.rename(file_renamed)
    except OSError as err:
        print(f'[RENAMED]  {file_renamed} → exists and will not overwrite')
    else:
        print(f'[RENAMED]  {file_renamed} → renamed')


# define f_data from given arg
if args.data is not None:
    f_data = args.data


def process_file(file_path):
    try:
        idx = normalize_index(os.path.basename(file_path))
        pwd = os.path.dirname(file_path)

        # when rename arg passed
        if args.rename:
            rename_file(file_path)
            return

        # skip next if in dry-run mode
        if args.dry_run:
            return

        # local toml
        if os.path.isfile(f"{pwd}/{f_data}"):
            write_tag(pwd, idx, file_path)
            return
        # metadata mirror
        meta = re.sub(f"{AUDIO_DIR}/music/(archived|disposable|main|review)", METADATA_DIR, pwd)
        if os.path.isfile(f"{meta}/{f_data}"):
            write_tag(meta, idx, file_path)
            return

        print(f"[SKIP] No TOML → {os.path.basename(file_path)}")

    except Exception as e:
        print(f"[ERROR] {os.path.basename(file_path)}: {e}")


def main() -> None:
    # files list will save all music file path in current directory
    files = []

    # scan current dir and save filepath in a list
    for f in os.listdir():
        if f.endswith(f".{args.format}"):
            files.append(os.path.abspath(f))
    print(f"[SCAN] {len(files)} files allowed to work")

    # process each file
    for f in files:
        process_file(f)
    print("[DONE]")


# run only in self, not in module
if __name__ == '__main__':
    main()

