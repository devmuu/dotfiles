#!/usr/bin/env python

# ==============================================================================
# Program:       discogs
# Description:   Get music data from discogs api
# Software/Tool: python/discogs_client/argparse
# ==============================================================================

import os
import re

import argparse
import requests
import discogs_client

# set global variables
TOKEN = os.environ.get('DISCOGS_TOKEN')
# base client
d = discogs_client.Client("ClientApplication/0.1")
# authenticated client (need token)
auth_search = discogs_client.Client("SearchApplication/0.1", user_token=TOKEN)

parser = argparse.ArgumentParser(
    description="Make files from jinja templates."
)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    "-r",
    "--release",
    type=str,
    metavar="release",
    dest="release_id",
    help="Set release id",
)
group.add_argument(
    "-s", "--search",
    type=str,
    metavar="search",
    dest="search",
    help="Search release"
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    default=os.getcwd(),
    metavar="output",
    dest="output_dir",
    help="Set output directory",
)
parser.add_argument(
    "-t",
    "--type",
    type=str,
    default="",
    metavar="type",
    dest="f_type",
    help="Set release type",
)
parser.add_argument(
    "-url",
    "--image-url",
    type=str,
    default=False,
    metavar="image-url",
    dest="image_url",
    help="Show image url",
)
parser.add_argument(
    "-single",
    "--single-artist",
    type=str,
    default=False,
    metavar="single-artist",
    dest="single_artist",
    help="Show only single artist",
)
args = parser.parse_args()

if args.output_dir is not None:
    output_dir = args.output_dir


def normalize_title(m_title):
    """change some words to lower in title"""
    m_title = m_title.title()
    words = ["A", "O", "E", "Uma", "Da", "De",
             "Do", "Das", "Dos", "Pra", "Para",
             "And", "For", "The", "Of", "in"]

    for w in words:
        aux = m_title.replace(f' {w} ', f' {w.lower()} ')
        m_title = aux
    return m_title


def move_files(album_path) -> None:
    """move files"""
    if not os.path.exists(album_path):
        os.makedirs(album_path)
        os.rename('info.toml', f'{album_path}/info.toml')
        os.rename('folder-tmp.jpg', f'{album_path}/cover.jpg')


def get_cover(front_url) -> None:
    """get cover file from url"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    front_data = requests.get(front_url, headers=headers).content

    # verify existent cover file
    cover_exists = os.path.exists(f"{output_dir}/folder-tmp.jpg")
    cover_file = "folder-tmp.jpg"

    with open(f"{output_dir}/{cover_file}", "wb") as handler:
        handler.write(front_data)

    print(f"cover: {cover_file}")

    if args.image_url:
        print(f"url_image: {cover_url}")


def get_tags(release_id) -> None:
    """get tags from api and create info file"""
    release = auth_search.release(release_id)
    try:
        release.status
    except discogs_client.exceptions.HTTPError:
        print("Bad release id")
    except Exception as err:
        print(f"Error {err}")
    else:
        # if release it's ok
        artists = [artist.name for artist in release.artists]
        if len(artists) > 1:
            artist = '; '.join(artists)
        else:
            artist = artists[0]

        album = release.title
        release_format = release.formats[0]["name"]
        discs = release.formats[0]["qty"]
        release_year = release.year
        genre = release.genres[0]

        try:
            len(release.styles)
        except:
            style = release.styles
        else:
            if len(release.styles) > 1:
                style = '; '.join(release.styles)
            else:
                # view if styles are empty
                if release.styles == []:
                    style = ""
                else:
                    style = release.styles[0]

        front_cover = release.images[0]["uri"]

        # get trackname and position from root tracklist
        track_name = [track.title for track in release.tracklist]
        track_position = [track.position for track in release.tracklist]
        track_artist = [track.artists for track in release.tracklist]

        # get index value from position list
        track_idx = [idx[0] + 1 for idx in enumerate(track_position)]

        # credits = [credits.credits for credits in release.tracklist]

        print(f"release: {album}")
        print(f"artist: {artist}")
        if front_cover:
            get_cover(front_cover)

        # verify existent info file
        info_file = "info.toml"

        print(f"Info: {info_file}")

        with open(f'{output_dir}/{info_file}', 'wt', encoding='utf-8') as f:
            # write stats
            f.write("[stats]\n")
            f.write(f'gsid = "{release_id}"\n')
            f.write('mbid = ""\n')
            f.write(f'artist = "{artist}"\n')
            f.write(f'album = "{album}"\n')
            f.write(f'format = "{release_format}"\n')
            f.write(f'discs = "{discs}"\n')
            f.write(f'year = "{release_year}"\n')
            f.write(f'genre = "{genre}"\n')
            f.write(f'style = "{style}"\n')
            f.write('image = "cover.jpg"\n\n')

            # write tracks
            if args.single_artist is False:
                # test if has more tha one artist
                list_test = len(track_artist[0])

                # single artist
                if list_test == 0:
                    f.write("[tracks]\n")
                    for idx, track in zip(track_idx, track_name):
                        track = normalize_title(track)
                        track_sub = re.sub(' *$', '', track)
                        f.write(f'track{idx:02} = "{track_sub}"\n')

                # TODO: Update this comment block to multiple artists

                        # j = idx - 1
                        # credit_names = [name.name for name in release.tracklist[j].credits]
                        # f.write(f'info = "{'; '.join(credit_names)}"\n')
                # multiple artists
                else:
                    # track_artist = [track.artists[0] for track in release.tracklist]
                    # artists_names = [track.name for track in track_artist]
                    #
                    # for artist, idx, track in zip(artists_names, track_idx, track_name):
                    #     f.write("[[tracks]]\n")
                    #     f.write(f'artist = "{artist}"\n')
                    #     track = normalize_title(track)
                    #     f.write(f'title = "{track}"\n')
                    #     f.write(f'tracknumber = "{idx:02}"\n')
                    #     if idx < len(track_artist):
                    #         f.write('\n')

                    track_artist = [track.artists for track in release.tracklist]
                    artists_names = [track_artist for track in track_artist[0]]
                    artist_track = [track_artist for track_artist in artists_names[0]]
                    artist_name = [artist for artist in artist_track]

                    for artist, idx, track in zip(artist_track, track_idx, track_name):
                        f.write("[[tracks]]\n")
                        f.write(f'artist = "{artist}"\n')
                        track = normalize_title(track)
                        f.write(f'title = "{track}"\n')
                        f.write(f'tracknumber = "{idx:02}"\n')
                        if idx < len(track_artist):
                            f.write('\n')

            else:
                f.write("[tracks]\n")
                for idx, track in zip(track_idx, track_name):
                    f.write(f'track{idx:02} = "{track}"\n')

        album_path = f'{release_year} - {album}'
        move_files(album_path)


def search_id(search_item) -> None:
    """get release id from search"""
    try:
        auth_search.search(search_item)
    except discogs_client.exceptions.HTTPError:
        print("Bad release search")
    except Exception as err:
        print(f"Error {err}")
    else:
        result = auth_search.search(search_item, type="release", format=args.f_type)
        if result.count:
            release = result[0]
            print(f"Match: {release.title}")
            release_id = release.id
            get_tags(release_id)
        else:
            print(f"No results for {search_item}")


def main() -> None:
    """main"""
    # check if release id
    if args.release_id:
        release_id = args.release_id
        get_tags(release_id)

    # if search arg is passed proceed to get release id
    elif args.search:
        search_item = args.search
        search_id(search_item)


# run only in self, not in module
if __name__ == "__main__":
    main()
