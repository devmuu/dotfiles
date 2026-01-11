#!/usr/bin/env python

# ==============================================================================
# Program:       discogs
# Description:   Get music data from discogs api
# Software/Tool: python/discogs_client
# ==============================================================================

import re
import os
import argparse
import requests
import discogs_client
from pathlib import Path
from typing import List, Dict, Tuple, Union
import logging

# setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# discogs client setup
TOKEN = os.environ.get("DISCOGS_TOKEN")
d = discogs_client.Client("ClientApplication/0.1")
auth_search = discogs_client.Client("SearchApplication/0.1", user_token=TOKEN)

# CLI parser
parser = argparse.ArgumentParser(description="Search data from Discogs API.")
group = parser.add_mutually_exclusive_group(required=True)
parser.add_argument("--cover", action="store_true", help="Get album cover")
group.add_argument("-r", "--release", type=str, help="Set release id")
group.add_argument("-s", "--search", type=str, help="Search release")
parser.add_argument("-o", "--output", type=str, default=os.getcwd(), help="Set output folder")
parser.add_argument("-t", "--type", type=str, default="", help="Set release type")
args = parser.parse_args()

# environment
OUTPUT_DIR = Path(args.output)

# ---------------------------
# Helpers
# ---------------------------

# remove invalid chars in path
def sanitize_path_name(name: str) -> str:
    """remove invalid characters for folders/files"""
    return re.sub(r'[\\/:"*?<>|]+', "", name)


# escape broken char in toml file
def toml_escape(value: str) -> str:
    return value.replace('"', '\\"')


# list of items to set as lowercase
def normalize_title(title: str) -> str:
    lower_words = {
        # portuguese
        "o", "as", "os", "um", "uma",
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


# get cover from requests
def get_cover(front_url: str, output_path: Path) -> None:
    """download cover image"""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(front_url, headers=headers)
    cover_file = output_path / "folder-tmp.jpg"

    with open(cover_file, "wb") as f:
        f.write(response.content)


# create and move files to album folder if it not exists
def move_files(info_file: Path, cover_file: Path, album_path: Path):
    """move info and cover files into album folder"""
    if album_path.exists():
        logging.warning(f"Folder already exists → {album_path}")
        return

    album_path.mkdir(parents=True, exist_ok=True)
    info_file.rename(album_path / "info.toml")
    if args.cover and cover_file.exists():
        cover_file.rename(album_path / "cover.jpg")


# ---------------------------
# Processor Class
# ---------------------------
FEAT_RE = re.compile(r"\((feat\.|ft\.) ([^)]+)\)", re.I)

class DiscogsReleaseProcessor:
    def __init__(self, release, output_dir: Path):
        self.release = release
        self.output_dir = output_dir
        self.release_artists = [artist.name for artist in release.artists]
        self.metadata = self._extract_metadata()
        self.multi_artist, self.tracks = self._extract_tracks()


    def _track_artist_signature(self, track) -> frozenset:
        artists = set(self.release_artists)
        if track.artists:
            artists = {a.name for a in track.artists}

        extraartists = getattr(track, "extraartists", [])
        artists |= {a.name for a in extraartists if "feat" in a.role.lower()}

        # Detect feat in track title
        feat_match = FEAT_RE.search(track.title)
        if feat_match:
            artists.add(feat_match.group(2))

        return frozenset(artists)


    def _format_artist(self, signature: frozenset) -> str:
        return "; ".join(sorted(signature))


    def _extract_metadata(self) -> dict:
        return {
            "artist": "; ".join(self.release_artists),
            "album": self.release.title,
            "format": self.release.formats[0]["name"] if self.release.formats else "",
            "discs": self.release.formats[0]["qty"] if self.release.formats else "",
            "year": self.release.year or "",
            "genre": self.release.genres[0] if self.release.genres else "",
            "style": "; ".join(self.release.styles) if self.release.styles else "",
        }


    def _extract_tracks(self) -> Tuple[bool, List[Dict[str, Union[int, str]]]]:
        # detect multiple artist in tracks
        signatures = [self._track_artist_signature(track) for track in self.release.tracklist]
        has_multiple = len(set(signatures)) > 1

        tracks = []
        for idx, (track, sig) in enumerate(zip(self.release.tracklist, signatures), start=1):
            tracks.append({
                "number": idx,
                "title": normalize_title(track.title),
                "artist": self._format_artist(sig)
            })

        return has_multiple, tracks


    def write_info_file(self):
        info_file = self.output_dir / "info.toml"
        logging.info(f"Creating info.toml for: {self.metadata['album']}")
        logging.info(f"Artist: {self.metadata['artist']}")
        logging.info(f"Album: {self.metadata['album']}")
        logging.info(f"Year: {self.metadata['year']}")

        with open(info_file, "w", encoding="utf-8") as f:
            f.write("[stats]\n")
            f.write(f'gsid = "{self.release.id}"\n')
            f.write('mbid = ""\n')
            for key, value in self.metadata.items():
                f.write(f'{key} = "{value}"\n')
            f.write('image = "cover.jpg"\n\n')

            if self.multi_artist:
                for track in self.tracks:
                    f.write("[[tracks]]\n")
                    f.write(f'title = "{toml_escape(track["title"])}"\n')
                    f.write(f'artist = "{toml_escape(track["artist"])}"\n')
                    f.write(f'tracknumber = "{track["number"]:02}"\n\n')
            else:
                f.write("[tracks]\n")
                for track in self.tracks:
                    f.write(f'track{track["number"]:02} = "{track["title"]}"\n')


    def download_cover(self):
        if not self.release.images:
            logging.error(f"No cover for: {self.metadata['album']}")
            return
        logging.info(f"Downloading cover for: {self.metadata['album']}")
        get_cover(self.release.images[0]["uri"], self.output_dir)


    def move_files(self):
        album_name = f"{self.metadata['year']} - {self.metadata['album']}"
        album_name = sanitize_path_name(album_name)
        album_path = self.output_dir / album_name
        move_files(self.output_dir / "info.toml", self.output_dir / "folder-tmp.jpg", album_path)


# ---------------------------
# Functions to get releases
# ---------------------------
# get release from given id
def get_tags(release_id: str):
    try:
        release = auth_search.release(release_id)
        _ = release.status
        logging.info(f"Good release id → {release_id}")
    except discogs_client.exceptions.HTTPError:
        logging.error(f"Bad release id → {release_id}")
        return

    processor = DiscogsReleaseProcessor(release, OUTPUT_DIR)

    if args.cover:
        processor.download_cover()
        return

    processor.write_info_file()
    processor.move_files()


# search release from text
def search_id(search_item: str):
    try:
        auth_search.search(search_item)
    except discogs_client.exceptions.HTTPError:
        logging.error("Bad release search")
        return
    except Exception as err:
        logging.error(err)
        return

    result = auth_search.search(search_item, type="release", format=args.type)
    if result.count:
        release = result[0]
        logging.info(f"Match: {release.title}")
        get_tags(release.id)
    else:
        logging.info(f"No results for {search_item}")


# ---------------------------
# Main
# ---------------------------
def main():
    if args.release:
        get_tags(args.release)
    if args.search:
        search_id(args.search)
    logging.info("DONE")


if __name__ == "__main__":
    main()

