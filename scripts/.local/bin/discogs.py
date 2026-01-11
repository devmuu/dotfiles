#!/usr/bin/env python

# ==============================================================================
# Program:       discogs
# Description:   Get music data from discogs api
# Software/Tool: python/discogs_client/argparse
# ==============================================================================

import os
import re
from typing import Tuple, List, Dict

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
parser.add_argument(
    '--cover',
    action='store_true',
    help='Get album cover'
)
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


"""
Begin Helpers
"""

def toml_escape(value: str) -> str:
    return value.replace('"', '\\"')

# get set of track artist
def track_artist_signature(track, release_artists):
    if track.artists:
        return frozenset(a.name for a in track.artists)
    return frozenset(release_artists)


def format_artist(signature: frozenset[str]) -> str:
    return "; ".join(sorted(signature))


def extract_release_metadata(release):
    artists = [a.name for a in release.artists]

    return {
        "artist": "; ".join(artists),
        "album": release.title,
        "format": release.formats[0]["name"] if release.formats else "",
        "discs": release.formats[0]["qty"] if release.formats else "",
        "year": release.year or "",
        "genre": release.genres[0] if release.genres else "",
        "style": "; ".join(release.styles) if release.styles else "",
    }


def extract_tracks(release) -> Tuple[bool, List[Dict[str, str]]]:
    release_artists = [a.name for a in release.artists]

    signatures = [
        track_artist_signature(track, release_artists)
        for track in release.tracklist
    ]

    has_multiple_artists = len(set(signatures)) > 1

    tracks = []
    for idx, (track, sig) in enumerate(zip(release.tracklist, signatures), start=1):
        tracks.append({
            "number": idx,
            "title": normalize_title(track.title),
            "artist": format_artist(sig),
        })

    return has_multiple_artists, tracks


def write_info_file(path, release_id, meta, tracks, has_multiple_track_artists):
    with open(path, "w", encoding="utf-8") as f:
        f.write("[stats]\n")
        f.write(f'gsid = "{release_id}"\n')
        f.write('mbid = ""\n')

        for key, value in meta.items():
            f.write(f'{key} = "{value}"\n')

        f.write('image = "cover.jpg"\n\n')

        if has_multiple_track_artists:
            print("[INFO] Release has multiple track artists")
            for track in tracks:
                f.write("[[tracks]]\n")
                f.write(f'artist = "{track["artist"]}"\n')
                f.write(f'title = "{track["title"]}"\n')
                f.write(f'tracknumber = "{track["number"]:02}"\n\n')
        else:
            f.write("[tracks]\n")
            for track in tracks:
                f.write(
                    f'track{track["number"]:02} = "{track["title"]}"\n'
                )

def normalize_title(title: str) -> str:
    lower_words = {
        # portuguese
        "a", "o", "as", "os", "um", "uma",
        "de", "do", "da", "dos", "das",
        "em", "por", "para", "pra",
        "e", "ou", "mas",

        # english
        "a", "an", "the",
        "of", "to", "in", "on", "at", "by", "for",
        "and", "or", "but", "nor"
    }

    words = re.split(r"(\s+)", title.strip())
    result = []

    for i, word in enumerate(words):
        if word.isspace():
            result.append(word)
            continue

        clean = re.sub(r"[^\w’']", "", word, flags=re.UNICODE)
        lower = clean.lower()

        if i == 0 or i == len(words) - 1:
            result.append(word.capitalize())
        elif lower in lower_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())

    return "".join(result)


def move_files(album_path) -> None:
    """move files"""
    if os.path.exists(album_path):
        print(f"[WARN] Folder already exists → {album_path}")
    else:
        os.makedirs(album_path)
        os.rename('info.toml', f'{album_path}/info.toml')
        if args.cover:
            os.rename('folder-tmp.jpg', f'{album_path}/cover.jpg')

"""
End Helpers
"""


def get_cover(front_url) -> None:
    """get cover file from url"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    front_data = requests.get(front_url, headers=headers).content
    cover_file = f"{output_dir}/folder-tmp.jpg"

    with open(cover_file, "wb") as handler:
        handler.write(front_data)

    if args.image_url:
        print(f"url_image: {cover_url}")


def get_tags(release_id):
    try:
        release = auth_search.release(release_id)
        _ = release.status
    except discogs_client.exceptions.HTTPError:
        print(f"[ERROR] Bad release id → {release_id}")
        return

    print(f"[INFO] Good release id → {release_id}")

    meta = extract_release_metadata(release)
    has_multiple_track_artists, tracks = extract_tracks(release)

    print(f"[METADATA] artist: {meta['artist']}")
    print(f"[METADATA] release: {meta['album']}")
    print(f"[METADATA] year: {meta['year']}")

    write_info_file(
        f"{output_dir}/info.toml",
        release_id,
        meta,
        tracks,
        has_multiple_track_artists
    )

    if args.cover and release.images:
        print(f"[COVER] Getting cover → {meta['album']}")
        get_cover(release.images[0]["uri"])

    move_files(f"{meta['year']} - {meta['album']}")


def search_id(search_item) -> None:
    """get release id from search"""
    try:
        auth_search.search(search_item)
    except discogs_client.exceptions.HTTPError:
        print(f"[ERROR] Bad release search")
    except Exception as err:
        print(f"[Error] {err}")
    else:
        print(f"[SEARCH] Item response")
        result = auth_search.search(search_item, type="release", format=args.f_type)
        if result.count:
            release = result[0]
            print(f"[INFO] Match: {release.title}")
            release_id = release.id
            get_tags(release_id)
        else:
            print(f"[INFO] No results for {search_item}")


def main() -> None:
    """main"""
    # check if release id
    if args.release_id:
        release_id = args.release_id
        get_tags(release_id)

    # if search arg is passed proceed to get release id
    if args.search:
        search_item = args.search
        search_id(search_item)

    print("[DONE]")


# run only in self, not in module
if __name__ == "__main__":
    main()

