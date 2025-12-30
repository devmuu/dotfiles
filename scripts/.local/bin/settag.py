#!/usr/bin/env python

# ==============================================================================
# Program:       settag
# Description:   Set audio metadata
# Software/Tool: python3.10.0/eyed3/toml
# ==============================================================================
"""
- mp3 files are biding with track names in a toml file
- all files must begin with two digits track number
"""
import os
import argparse
import re

import toml
import eyed3
from eyed3.id3.frames import ImageFrame

# variables
AUDIO_DIR = os.environ.get('AUDIO_DIR')
METADATA_DIR = f'{AUDIO_DIR}/metadata'


# args
parser = argparse.ArgumentParser(description='Set music tags')
parser.add_argument(
    '-d',
    '--data',
    type=str,
    default='info.toml',
    metavar='data',
    dest='f_data',
    help='Choose toml data file',
)
parser.add_argument(
    '-r',
    '--rename',
    type=str,
    choices=['dash', 'dot', 'cover'],
    metavar='rename',
    dest='rename',
    help='Rename from metadata',
)
parser.add_argument(
    '-f',
    '--format',
    type=str,
    default='mp3',
    choices=['mp3', 'mp4', 'wma'],
    metavar='format',
    dest='file_format',
    help='File format',
)
args = parser.parse_args()


def get_image(data_path, track_list, artist, idx) -> str:
    """get correct image for track"""
    # normalize track index if it is a list
    idx_norm = int(idx)-1

    # default image file
    image = 'cover.jpg'

    # check if covers directory exists
    covers_test = os.path.isdir('covers')
    if covers_test:
        single_img = f'covers/cover{idx_norm+1}.jpg'
        if os.path.isfile(single_img):
            image = single_img

    if isinstance(track_list, list):
        if 'album' and 'year' in track_list[idx_norm]:
            # search album cover in artist path
            album_path = f'{track_list[idx_norm]["year"]} - {track_list[idx_norm]["album"]}'
            album_cover = f'{METADATA_DIR}/Artists/{artist}/{album_path}/cover.jpg'
            album_cover_test = os.path.isfile(album_cover)

            if album_cover_test:
                image = album_cover

        # test track has image key and search for covers folder in data_path
        elif 'image' in track_list[idx_norm]:
            track_cover = f'{data_path}/covers/cover{idx_norm+1}.jpg'
            print(track_cover)

            if os.path.isfile(track_cover):
                image = track_cover

    # image priority:
    """
        1 - cover.jpg in file folder (album thumb)
        2 - cover.jpg in album artist metadada folder (album thumb)
        3 - cover.jpg in artist folder (artist thumb)
        4 - generic cover
    """

    # 1 test if cover.jpg exists in current or in covers directories
    # if file does not exists, search in same path of info.toml
    if not os.path.isfile(image):
        album_cover = f'{data_path}/cover.jpg'
        album_cover_test = os.path.isfile(album_cover)

        # 2 test if cover.jpg exists
        if album_cover_test:
            print(f'ALBUM COVER from metadata was set for track {idx}')
            image = album_cover
        else:
            # get current artist metadata path
            artist_cover = f'{METADATA_DIR}/Artists/{artist}/cover.jpg'
            artist_cover_test = os.path.isfile(artist_cover)

            # 3 search cover.jpg in artist metadata folder
            if artist_cover_test:
                print(f'DEFAULT ARTIST cover was set for track {idx}')
                image = artist_cover
            else:
                # check some artist in multiple tag
                multi_artist = artist.split("; ")
                n_artists = len(multi_artist)

                if n_artists > 1:
                    multi_cover = f'{METADATA_DIR}/Artists/{artist}/cover.jpg'
                    artist_cover_test = os.path.isfile(multi_cover)

                    if not artist_cover_test:
                        for name_artist in multi_artist:
                            single_cover = f'{METADATA_DIR}/Artists/{name_artist}/cover.jpg'
                            single_cover_test = os.path.isfile(single_cover)

                            if single_cover_test:
                                image = single_cover
                                print(f'SINGLE artist cover was set  for track {idx}')
                                break

                        if not single_cover_test:
                            image = f'{METADATA_DIR}/cover.jpg'
                            print(f'GENERIC cover was set  for track {idx}')

                        # check album cover in artist path
                        if 'album' and 'year' in track_list[idx_norm] and single_cover_test:
                            album_path = f'{track_list[idx_norm]["year"]} - {track_list[idx_norm]["album"]}'
                            album_cover = f'{METADATA_DIR}/Artists/{name_artist}/{album_path}/cover.jpg'
                            album_cover_test = os.path.isfile(album_cover)

                            if album_cover_test:
                                image = album_cover

                else:
                    # 4 if no one image found, set a generic cover from metadata dir
                    print(f'GENERIC cover was set  for track {idx}')
                    generic_cover = f'{METADATA_DIR}/cover.jpg'
                    image = generic_cover
    else:
        # if cover.jpg or covers/cover<tracknumber>.jpg exists in mp3 directory
        print(f'DEFAULT album cover was set for track {idx}')

    return image


def write_tag(data_path, idx, file_name) -> None:
    """write tags"""
    toml_data = toml.load(f'{data_path}/{f_data}')
    album_artist = toml_data['stats']['artist']
    album = toml_data['stats']['album']
    disc_num = toml_data['stats']['discs'].split(',')
    year = toml_data['stats']['year']
    genre = toml_data['stats']['genre']
    track_list = toml_data['tracks']
    n_tracks = len(toml_data['tracks'])

    # check if tracks info it is a list
    if isinstance(track_list, list):
        idx_norm = int(idx) - 1
        title = track_list[idx_norm]['title']
        artist = track_list[idx_norm]['artist']
    else:
        title = track_list[f'track{idx}']
        artist = album_artist

    # get image from get_image method
    image = get_image(data_path, track_list, artist, idx)

    tag_file = eyed3.load(file_name)

    if not tag_file.tag:
        tag_file.initTag()

    tag_file.tag.clear()
    tag_file.tag.track_num = (idx, n_tracks)
    tag_file.tag.title = title
    # replace ';' character to null values '\x00' to separate multi artist
    tag_file.tag.artist = artist.replace("; ", '\x00')
    tag_file.tag.album_artist = album_artist.replace("; ", '\x00')
    tag_file.tag.album = album
    tag_file.tag.recording_date = year
    tag_file.tag.release_date = year
    # replace ';' character to null values '\x00' to separate genres
    tag_file.tag.genre = genre.replace("; ", '\x00')

    # tag disc number
    if len(disc_num) > 1:
        tag_file.tag.disc_num = (disc_num[0], disc_num[1])
    else:
        tag_file.tag.disc_num = (disc_num[0], disc_num[0])

    # clean tags with null value
    tag_file.tag.comments.set("null")
    tag_file.tag.publisher = "null"
    tag_file.tag.copyright = "null"

    # remove current images
    audioImageDescriptions = [audioImage.description for audioImage in tag_file.tag.images]

    for description in audioImageDescriptions:
        tag_file.tag.images.remove(description)

    # set image for front cover
    tag_file.tag.images.set(ImageFrame.FRONT_COVER, open(image, 'rb').read(), 'image/jpeg')
    tag_file.tag.save()


def rename_file(file_name, opt) -> None:
    """rename files"""
    # define correct separator and new filename
    sep = ' - ' if opt == 'dash' else '. '
    tag_file = eyed3.load(file_name)
    # bar '/' it's not accepted in filenames
    title_corretion = re.sub('/', '-', tag_file.tag.title)
    # other characters to remove or change
    title_corretion = re.sub('\\?', '', title_corretion)
    title_corretion = re.sub('\\¿', '', title_corretion)
    title_corretion = re.sub('\\!', '', title_corretion)
    title_corretion = re.sub('\\*', '_', title_corretion)
    set_name = f'{tag_file.tag.track_num[0]:02}{sep}{title_corretion}'

    # if new filename is the same current, except IOError
    try:
        tag_file.rename(set_name)
    except IOError as err:
        print(f'[] {err}')
    else:
        print(f'[] {set_name} -> renamed')


def rename_cover(data, filename) -> None:
    """rename cover file"""
    if os.path.isfile(filename):
        COVER_DIR = f'{os.environ.get("HOME")}/Music/musics/.covers/albums'
        toml_data = toml.load(data)
        artist = toml_data['stats']['artist']
        album = toml_data['stats']['album']
        cover_path = ''
        new_name = f'{artist}-{album}'
        new_name = re.sub('\\.', '', new_name)
        new_name = re.sub(';', '', new_name)
        new_name = re.sub(' ', '-', new_name)
        new_name = new_name.lower()
        renamed = f'{COVER_DIR}/{new_name}.jpg'
        os.rename(filename, renamed)
    else:
        print(f'no file named {filename}')


# define f_data from given arg
if args.f_data is not None:
    f_data = args.f_data

if args.file_format is not None:
    file_format = args.file_format


def main() -> None:
    """main"""
    pwd = os.getcwd()

    # not interaction
    if args.rename == 'cover':
        rename_cover(f_data, 'front.jpg')
    else:
        # scan current directory
        with os.scandir(pwd) as entries:
            for entry in entries:
                # get only current type files
                if entry.name.endswith(f'.{file_format}'):
                    # get number track
                    # idx = entry.name.strip()[:2]
                    try:
                        re.findall(r'\b\d+\b', entry.name.strip())[0]
                    except IndexError as err:
                        idx = re.findall(r'\d+', entry.name.strip())[0]
                    else:
                        idx = re.findall(r'\b\d+\b', entry.name.strip())[0]

                    # add 0 left in track number to normalize with toml file pattern
                    if len(idx) < 2:
                        idx = idx.rjust(2,'0')

                    # verify given arg
                    if args.rename:
                        # send file_name and rename arg
                        # files are renamed like own metadata
                        # run settag.py before to pass all data in toml file
                        rename_file(entry.name, args.rename)
                    else:
                        # send file_name and f_data to write_tag
                        data_test = os.path.isfile(f'{pwd}/{f_data}')

                        # try find toml file in current folder, otherwise in metadata dir
                        if data_test:
                            write_tag(pwd, idx, entry.name)
                        else:
                            # try find toml file in metadata directory based on musics, archived or limbo directories
                            meta_folder = re.sub(f'{AUDIO_DIR}/(musics|archived|disposable)', f'{METADATA_DIR}', pwd)
                            data_test = os.path.isfile(f'{meta_folder}/{f_data}')

                            # if file exists, write tags
                            if data_test:
                                write_tag(meta_folder, idx, entry.name)
                            else:
                                # check last 2 folders in path for a pattern artist/album in Artists metadata
                                p_album = os.path.basename(pwd)
                                p_artist = os.path.basename(os.path.dirname(pwd))

                                meta_folder = f'{METADATA_DIR}/Artists/{p_artist}/{p_album}'
                                data_test = os.path.isfile(f'{meta_folder}/{f_data}')

                                # if file exists, write tags, otherwise, break the loop
                                if data_test:
                                    write_tag(meta_folder, idx, entry.name)
                                else:
                                    print("No toml data file in metadata directory.")
                                    break


# run only in self, not in module
if __name__ == '__main__':
    main()
