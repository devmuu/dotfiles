#!/usr/bin/env python

# ==============================================================================
# Program:       music_brainz
# Description:   Get music data from musicbrainz api
# Software/Tool: python/musicbrainzngs/argparse
# ==============================================================================
"""
Usage:
Get realease id directly from web page or from search option.
For most precisely results is recommended get info from specific release id.
"""

import os
import re
import argparse

import musicbrainzngs

# base client
musicbrainzngs.set_useragent('musicApp', '0.1', 'localhost')

parser = argparse.ArgumentParser(
    description='Get music information by musicbrainzngs.'
)
group = parser.add_mutually_exclusive_group(required=False)
parser.add_argument(
    '-o',
    '--output',
    type=str,
    default=os.getcwd(),
    metavar='output',
    dest='output_dir',
    help='Set output directory',
)
group.add_argument(
    '-r',
    '--release',
    type=str,
    metavar='release',
    dest='release_id',
    help='Set release id',
)
group.add_argument(
    '-s',
    '--search',
    type=str,
    default=False,
    metavar='search',
    dest='search',
    help='Search release',
)
args = parser.parse_args()

if args.output_dir is not None:
    output_dir = args.output_dir


# get image
def get_image(release_id) -> None:
    """get image from release id"""
    print('Search for cover image...')
    cover_exists = os.path.exists(f'{output_dir}/cover.jpg')
    if cover_exists:
        img_file = 'front.jpg'
    else:
        img_file = 'cover.jpg'

    try:
        img_data = musicbrainzngs.get_image_front(release_id)
    except Exception:
        print('No image found for this release')
    else:
        with open(img_file, 'wb') as f:
            f.write(img_data)
        print(f'image saved in {img_file}')


# get release info
def get_release(release_id) -> None:
    """get release info from release id"""
    if release_id:
        try:
            musicbrainzngs.get_release_by_id(release_id)
        except musicbrainzngs.musicbrainz.ResponseError:
            print('Bad release id')
        except Exception as err:
            print(f'Error: {err}')
        else:
            release = musicbrainzngs.get_release_by_id(
                release_id, includes=['artists', 'recordings']
            )
            # using get to prevent error and return None if no value
            release_value = release.get('release')
            artist = release_value.get('artist-credit-phrase')
            album = release_value.get('title')
            n_discs = release_value.get('medium-count')
            y_date = release_value.get('date')
            discs = release_value.get('medium-list')

            print(f'artist: {artist}')
            print(f'album: {album}\n')
            print('Generating data info...')

            # verify existent info file
            info_exists = os.path.exists(f'{output_dir}/info.toml')
            if info_exists:
                data_file = 'data.toml'
            else:
                data_file = 'info.toml'

            with open(data_file, 'wt', encoding='utf-8') as f:
                f.write('[stats]\n')
                f.write('gsid = ""\n')
                f.write(f'mbid = "{release_id}"\n')
                f.write(f'artist = "{artist}"\n')
                f.write(f'album = "{album}"\n')
                f.write('format = ""\n')
                f.write(f'discs = "{n_discs}"\n')
                f.write(f'year = "{y_date}"\n')
                f.write('genre = ""\n')
                f.write('style = ""\n')
                f.write('image = "cover.jpg"\n\n')

                f.write('[tracks]\n')
                for disc in discs:
                    tracks = disc['track-list']
                    for track in tracks:
                        idx_norm = re.sub("^[A-Z]*", "", track['number'])
                        idx = int(idx_norm)
                        title = re.sub('"|`|“|”', "'", track['recording']['title']).title()
                        f.write(f'track{idx:02} = "{title}"\n')
                f.write('\n')

            print(f'data saved in {data_file}')
            get_image(release_id)
    else:
        print('No release id')


# search release
def search_release(search_item) -> None:
    """get release id from search"""
    search_info = musicbrainzngs.search_releases(search_item)
    if search_info['release-count']:
        # get only first result
        release_id = search_info['release-list'][0]['id']
        get_release(release_id)
    else:
        print(f'No results for {search_item}')


# main
def main() -> None:
    """main"""
    if args.release_id:
        release_id = args.release_id
        get_release(release_id)
    elif args.search:
        search_item = args.search
        search_release(search_item)


# run only in self, not in module
if __name__ == '__main__':
    main()
