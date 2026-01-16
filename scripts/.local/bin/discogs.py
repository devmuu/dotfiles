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
from datetime import datetime
import discogs_client
from discogs_client.models import Track
import json
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
parser.add_argument("-b", "--batch", action="store_true", help="Scape directory")
parser.add_argument("-t", "--type", type=str, default="", help="Set release type")
args = parser.parse_args()

# environment
OUTPUT_DIR = Path(args.output)

# ---------------------------
# Helpers
# ---------------------------

FEAT_RE = re.compile(r"\((?:feat\.|ft\.|featuring) ([^)]+)\)", re.I)

# remove invalid chars in path
def sanitize_path_name(name: str) -> str:
    """remove invalid characters for folders/files"""
    return re.sub(r'[\\/:"*?<>|]+', "", name)


# escape broken char in toml file
def toml_escape(value: str) -> str:
    return value.replace('"', '\\"')

def toml_list(lst):
    return "[" + ", ".join([toml_string(i) for i in lst]) + "]"

# normalize toml strings
def toml_string(value: str) -> str:
    if value is None:
        return '""'
    return f'"{value.replace("\"", "\\\"")}"'


# list of items to set as lowercase
def normalize_title(title: str) -> str:
    lower_words = {
        # portuguese
        "o", "as", "os", "um", "uma",
        "de", "do", "da", "dos", "das",
        "em", "por", "para", "pra", "pela",
        "e", "ou", "mas", "ao", "com",
        # spanish
        "que", "un", "uno", "una",
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

def normalize_discogs_tracklist(tracks: List[Track]) -> List[Dict]:
    normalized = []
    counter = 1

    for t in tracks:
        position = t.position.strip() if t.position else ""
        title = t.title.strip() if t.title else ""

        # Ignora separadores
        if title in ("", "-") and position == "":
            continue

        # Adiciona track normalizada
        normalized.append({
            "track": counter,
            "position": position,
            "title": title
        })
        counter += 1

    return normalized


def get_track_artists(track, release_artists) -> dict:
    # init
    primary = set()
    featured = set()

    # add main release artists
    for a in release_artists:
        if a and a.lower() != "various":
            primary.add(normalize_title(a))
    if "Various Artists" in release_artists:
        primary.add("Various Artists")

    # lead artists from tracks
    for a in getattr(track, "artists", []) or []:
        if getattr(a, "name", None):
            name = normalize_title(a.name)
            if name.lower() != "various":
                primary.add(name)

    # extra artists (discogs track.data)
    for a in track.data.get("extraartists", []):
        name = a.get("name")
        role = a.get("role", "").lower()
        if not name:
            continue
        name = normalize_title(name)

        # keys to allow use as featured
        if any(k in role for k in ("feat", "ft", "featuring")):
            featured.add(name)

    # detect features in track title
    title = getattr(track, "title", "")
    for match in FEAT_RE.finditer(title):
        names = [normalize_title(n.strip()) for n in match.group(1).split(",")]
        featured.update(filter(None, names))

    # remove duplicates
    featured -= primary

    # order both lists
    return {
        "primary": sorted(primary),
        "featured": sorted(featured)
    }


# verify if key exists
def safe_get(data, path, default=None):
    try:
        for key in path:
            if isinstance(data, dict):
                data = data.get(key, default)
            elif isinstance(data, list):
                data = data[key] if len(data) > key else default
            else:
                data = getattr(data, key, default)
        return data if data not in [None, 0] else default
    except (IndexError, KeyError, TypeError, AttributeError) as e:
        logging.warning(f"Error accessing {' -> '.join(map(str, path))}: {e}")
        return default


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

    if args.batch:
        return

    album_path.mkdir(parents=True, exist_ok=True)
    info_file.rename(album_path / "info.toml")
    if args.cover and cover_file.exists():
        cover_file.rename(album_path / "cover.jpg")


# ---------------------------
# Processor Class
# ---------------------------
class DiscogsReleaseProcessor:
    def __init__(self, release, output_dir: Path):
        self.release = release
        self.output_dir = output_dir
        self.original_artists_list = [ artist.name for artist in release.artists ]
        self.original_artists = ', '.join(self.original_artists_list)

        print(f'[DISCOGS] Original Artist: {self.original_artists}')

        self.release_artists = [
            artist.name if artist.name != "Various" else "Various Artists"
            for artist in release.artists
        ]

        if len(self.release_artists) > 1 or "Various Artists" in self.release_artists:
            self.album_artist = "Various Artists"
        else:
            self.album_artist = self.release_artists[0]

        self.metadata = self._extract_metadata()
        self.multi_artist, self.tracks = self._extract_tracks()
        self.metadata.update(self._extract_musicbrainz())  # add MB info


    def _get_release_group(self) -> str:
        desc = self.metadata["descriptions"]
        if "Compilation" in desc:
            return "Compilation"
        if "Single" in desc:
            return "Single"
        if "LP" in desc:
            return "LP"
        if "EP" in desc:
            return "EP"
        return "Album"


    def _extract_musicbrainz(self) -> dict:
        import musicbrainzngs
        musicbrainzngs.set_useragent('musicApp', '0.1', 'localhost')

        # Se não tiver artistas ou título, retorna vazio
        if not hasattr(self, "release_artists") or not hasattr(self, "release"):
            return {}

        mb_artist = self.original_artists if self.original_artists else ""
        mb_release = self.release.title if hasattr(self.release, "title") else ""

        if not mb_artist or not mb_release:
            return {}

        try:
            search_info = musicbrainzngs.search_releases(
                artist=mb_artist,
                release=mb_release,
                primarytype="album",
                limit=5
            )
        except Exception as err:
            print(f"[MusicBrainz ERROR] Search failed: {err}")
            return {}

        if search_info.get('release-count', 0) == 0:
            return {}

        release_data = search_info['release-list'][0]
        release_id = release_data.get('id')

        if not release_id:
            return {}

        # Consulta detalhada do release
        try:
            mb_release_full = musicbrainzngs.get_release_by_id(
                release_id, includes=['artists','release-groups']
            )['release']
        except musicbrainzngs.musicbrainz.ResponseError:
            print(f"[MusicBrainz ERROR] Bad release ID: {release_id}")
            return {}
        except Exception as err:
            print(f"[MusicBrainz ERROR] {err}")
            return {}

        # Artist ID
        mb_artistid = None
        artist_credit = mb_release_full.get('artist-credit', [])
        if artist_credit and 'artist' in artist_credit[0]:
            mb_artistid = artist_credit[0]['artist'].get('id')

        # Release Group ID
        mb_releasegroupid = mb_release_full.get('release-group', {}).get('id', '')

        # Release date
        rg = mb_release_full.get('release-group', {})
        release_date = rg.get('first-release-date', None)
        if release_date:
            parts = release_date.split('-')
            if len(parts) == 1:
                release_date = parts[0]          # YYYY
            elif len(parts) == 2:
                release_date = '-'.join(parts)   # YYYY-MM
            elif len(parts) == 3:
                release_date = '-'.join(parts)   # YYYY-MM-DD

        return {
            "release_date": toml_string(release_date) or "",
            "musicbrainz_artistid": toml_string(mb_artistid) or "",
            "musicbrainz_albumid": toml_string(release_id) or "",
            "musicbrainz_releasegroupid": toml_string(mb_releasegroupid) or ""
        }


    def _extract_metadata(self) -> dict:
        return {
            "album_title": toml_string(normalize_title(self.release.title)) or toml_string(normalize_title(self.release.master.title)),
            "release_year": safe_get(self.release, ['year'], safe_get(self.release.master, ['year'], 1900)),
            "total_discs": int(safe_get(self.release, ['formats', 0, 'qty'], 1)),
            "album_artist": toml_string(normalize_title(self.album_artist)),
            "media_format": toml_string(safe_get(self.release, ['formats', 0, 'name'], 'Digital Media')),
            "region": toml_string(safe_get(self.release, ['country'], 'Unknown')),
            "descriptions": safe_get(self.release, ['formats', 0, 'descriptions'], []),
            "genres": self.release.genres if self.release.genres else [],
            "styles": self.release.styles if self.release.styles else [],
            "publishers": [publisher.name for publisher in self.release.labels] if self.release.labels else [],
        }


    def _extract_tracks(self) -> Tuple[bool, List[Dict[str, Union[int, str]]]]:
        default_tracklist = self.release.tracklist or self.release.master.tracklist
        normalized_tracks = normalize_discogs_tracklist(default_tracklist)

        tracks = []
        has_multiple = False

        for t in normalized_tracks:
            position = t["position"]
            title = t["title"]

            # Detect artists for this track
            track_obj = next((tr for tr in self.release.tracklist if (tr.title.strip() == title or tr.position == position)), None)

            if track_obj:
                track_artists = get_track_artists(track_obj, self.release_artists)
            else:
                track_artists = {"primary": self.release_artists, "featured": []}

            # track_artists = list(sig)
            tracks.append({
                "position": t["track"],
                "title": normalize_title(title),
                "artists": track_artists
            })

        # Detecta se existe múltiplos artistas
        has_multiple = len(track_artists) > 1

        return has_multiple, tracks


    def write_info_file(self):
        info_file = self.output_dir / "info_.toml"
        logging.info(f"Creating info.toml for: {self.metadata['album_title']}")
        logging.info(f"Artist: {self.metadata['album_artist']}")
        logging.info(f"Album: {self.metadata['album_title']}")
        logging.info(f"Year: {self.metadata['release_year']}")

        with open(info_file, "w", encoding="utf-8") as f:
            f.write('schema = "music.library.release"\n')
            f.write('schema_version = 1\n')
            f.write('\n')

            f.write("[sources]\n")
            f.write('discogs = true\n')
            f.write('musicbrainz = true\n')
            f.write('\n')

            f.write("[info]\n")
            f.write(f'region = {self.metadata["region"]}\n')
            f.write(f'styles = {self.metadata["styles"]}\n')
            f.write(f'release_notes = {self.metadata["descriptions"]}\n')
            f.write('\n')

            f.write("[assets]\n")
            f.write('cover_art = "album_cover"\n')
            f.write('\n')

            f.write("[release]\n")
            f.write(f'title = {self.metadata["album_title"]}\n')
            f.write(f'artist = {self.metadata["album_artist"]}\n')
            f.write(f'release_type = "{self._get_release_group()}"\n')
            f.write(f'release_year = {self.metadata["release_year"]}\n')
            f.write(f'release_date = {self.metadata["release_date"]}\n')
            f.write(f'publishers = {self.metadata["publishers"]}\n')
            f.write(f'genres = {self.metadata["genres"]}\n')
            f.write('\n')

            f.write("[[disc]]\n")
            f.write(f'index = {self.metadata["total_discs"]}\n')
            f.write(f'media_format = {self.metadata["media_format"]}\n')
            f.write('\n')

            for track in self.tracks:
                f.write("[[tracks]]\n")
                f.write(f'position = {track["position"]}\n')
                f.write(f'title = "{toml_escape(track["title"])}"\n')
                f.write('\n')
                f.write("[tracks.artists]\n")

                f.write(f'primary = {toml_list(track["artists"]["primary"])}\n')
                if len(track["artists"]["featured"]) > 0:
                    f.write(f'featured = {toml_list(track["artists"]["featured"])}\n')

                f.write('\n')

            f.write("[ids.musicbrainz]\n")
            f.write(f'artistid = {self.metadata["musicbrainz_artistid"]}\n')
            f.write(f'albumid = {self.metadata["musicbrainz_albumid"]}\n')
            f.write(f'releasegroupid = {self.metadata["musicbrainz_releasegroupid"]}\n')
            f.write('\n')

            f.write("[ids.discogs]\n")
            f.write(f'artistid = {[artist.id for artist in self.release.artists]}\n')
            f.write(f'releaseid = {self.release.id}\n')
            f.write(f'masterid = { safe_get(self.release.master, ["id"], self.release.id) }\n')
            f.write('\n')

            f.write("[control]\n")
            f.write(f'locker = false\n')
            f.write(f'write_tags = true\n')
            f.write(f'write_cover = true\n')
            f.write(f'write_mode = "overwrite"\n')
            f.write('\n')


    def download_cover(self):
        if not self.release.images:
            logging.error(f"No cover for: {self.metadata['album_title']}")
            return
        logging.info(f"Downloading cover for: {self.metadata['album_title']}")
        get_cover(self.release.images[0]["uri"], self.output_dir)


    def move_files(self):
        album_name = f"{self.metadata['release_year']} - {self.metadata['album_title']}"
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

