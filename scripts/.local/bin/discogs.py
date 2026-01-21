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
import json
import discogs_client
from discogs_client.models import Track
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
HOME_DIR = Path(os.environ.get('HOME'))
DISCOGS_CACHE_DIR = HOME_DIR / '.cache' / 'discogs'
DISCOGS_CACHE_DIR.mkdir(exist_ok=True)

# ---------------------------
# Helpers
# ---------------------------

FEAT_RE = re.compile(r"\((?:feat\.|ft\.|featuring) ([^)]+)\)", re.I)

# remove invalid chars in path to use year - album_name as path.
def sanitize_path_name(name: str) -> str:
    return re.sub(r'[\\/:"*?<>|]+', "", name)

# remove (idx) from artists names
def sanitize_artist_name(name: str) -> str:
    return re.sub(r"\s*\(\d+\)$", "", name).strip()

# extract release stats safe
def extract_release_stats(release_format: dict) -> dict:
    """
    the default in discogs release if format type is equal to File is to use
    the same value to qty and files.
    """
    release_type = safe_get(release_format, ['name'], 'CD')
    release_descriptions = safe_get(release_format, ['descriptions'], [])

    if release_type == 'File':
        qtd = 1
    else:
        qtd = int(safe_get(release_format, ['qty'], 1))

    # flag to indicate if a release require a multi disc format
    multi_disc_flag = True if release_type == 'CD' and qtd > 1 else False

    return {
        "media_format": release_type,
        "total_discs": qtd,
        "descriptions": release_descriptions,
        "multi_disc_flag": multi_disc_flag,
    }

# sanitize and extrac first digit from origin position in multi-disc release.
def extract_disc_num(position: str) -> int:
    """
    common patterns:
        '1-5', '1:4', '1 5' -> 1
        '2-1', '2:3' -> 2
        '-', '' -> 1 (fallback)
    """
    if not position or position in ("", "-"):
        return 1

    pos = position.strip()
    match = re.match(r"(\d+)", pos)
    if match:
        return int(match.group(1))

    return 1

# return "" if '-' it's defined as position
def normalize_track_position(position: str) -> str:
    if not position:
        return ""

    pos = position.strip()
    if pos in ("", "-"):
        return ""

    pos = re.sub(r"\s*[:]\s*", "-", pos)
    pos = re.sub(r"\s+", "", pos)
    return pos

# list of items to set as lowercase.
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

# get cache file
def cache_get(key: str, max_age_days: int = 7):
    from datetime import datetime, timedelta

    cache_file = DISCOGS_CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(days=max_age_days):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    return None

# create release cache to use
def cache_set(key: str, data):
    cache_file = DISCOGS_CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# export tracklist from original release.tracklist from discogs.
def normalize_discogs_tracklist(tracks: List[Track]) -> List[Dict]:
    normalized = []
    counter = 1

    for t in tracks:
        position = t.position.strip() if t.position else ""
        title = t.title.strip() if t.title else ""

        # ignore separators
        if title in ("", "-") and position == "":
            continue

        # add normalized track
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

    # add main release artists.
    # this block add all or remain default album artists in track.
    # only add primary if tracklist.artists it's empty, and,
    # never when various.
    for a in release_artists:
        if a and a.lower() != "various":
            if track.artists == []:
                primary.add(normalize_title(a))
    if "Various Artists" in release_artists:
        primary.discard("Various Artists")

    # lead artists from tracks
    for a in getattr(track, "artists", []) or []:
        if getattr(a, "name", None):
            name = normalize_title(a.name)
            name = sanitize_artist_name(name).strip()
            if name.lower() != "various":
                primary.add(name)

    # extra artists (discogs track.data)
    for a in track.data.get("extraartists", []):
        name = a.get("name")
        role = a.get("role", "").lower()
        if not name:
            continue
        name = normalize_title(name)
        name = sanitize_artist_name(name).strip()

        # keys to allow use as featured
        if any(k in role for k in ("feat", "ft", "featuring", "vocals")):
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


# verify if key exists.
def safe_get(data, path, default=None):
    try:
        for key in path:
            if isinstance(data, dict):
                data = data.get(key, default)
            elif isinstance(data, list):
                data = data[key] if len(data) > key else default
            else:
                data = getattr(data, key, default)
        return default if data is None else data
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
def create_folder(info_file: Path, cover_file: Path, album_path: Path):
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

class TomlWriter:
    def __init__(self, file):
        self.f = file
        self.started = False

    # -----------------------
    # Helpers
    # -----------------------
    def _newline(self):
        if self.started:
            self.f.write("\n")
        self.started = True

    def _format_value(self, value):
        """Formata string, boolean, int, float ou lista para TOML"""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return "[" + ", ".join([self._format_value(v) for v in value]) + "]"
        elif value is None:
            return '""'
        else:
            # escape quotes
            return f'"{str(value).replace("\"", "\\\"")}"'

    def _write_kv(self, key, value):
        self.f.write(f"{key} = {self._format_value(value)}\n")

    # -----------------------
    # API
    # -----------------------
    def write_block(self, name: str, values: dict):
        """Escreve [block]"""
        self._newline()
        self.f.write(f"[{name}]\n")
        for k, v in values.items():
            self._write_kv(k, v)

    def write_array_block(self, name: str, values: dict):
        """Escreve [[block]]"""
        self._newline()
        self.f.write(f"[[{name}]]\n")
        for k, v in values.items():
            self._write_kv(k, v)

    def write_subblock(self, parent: str, name: str, values: dict):
        """Escreve [parent.child] sempre com linha vazia antes"""
        self._newline()
        self.f.write(f"[{parent}.{name}]\n")
        for k, v in values.items():
            self._write_kv(k, v)

# ---------------------------
# Processor Class
# ---------------------------
class DiscogsReleaseProcessor:
    def __init__(self, release, output_dir: Path):
        self.release = release
        self.output_dir = output_dir
        self.cache_key = f"discogs_{self.release.id}"

        cached = cache_get(self.cache_key)
        if cached:
            self.metadata = cached["metadata"]
            self.tracks = cached["tracks"]
            self.multi_artist = cached["multi_artist"]
            print(f"[DISCOGS] Loaded cached release → {self.release.title}")
            return

        # original release artist in discogs
        self.release_artists = [
            artist.name if artist.name != "Various" else "Various Artists"
            for artist in release.artists
        ]

        # album artist
        if len(self.release_artists) > 1 or "Various Artists" in self.release_artists:
            self.album_artist = "Various Artists"
        else:
            self.album_artist = self.release_artists[0]


        self.metadata = self._extract_metadata()
        self.multi_artist, self.tracks = self._extract_tracks()
        self.metadata.update(self._extract_musicbrainz())

        # if musicbrainz down
        # result_null = {
        #     "release_date": "",
        #     "musicbrainz_artistid": "",
        #     "musicbrainz_albumid": "",
        #     "musicbrainz_releasegroupid": ""
        # }
        # self.metadata.update(result_null)

        cache_set(self.cache_key, {
            "metadata": self.metadata,
            "tracks": self.tracks,
            "multi_artist": self.multi_artist
        })
        print(f"[DISCOGS] Cached release → {self.release.title}")


    def _get_release_group(self) -> str:
        desc = self.metadata["stats"]["descriptions"]
        if "Compilation" in desc:
            return "Compilation"
        if "Single" in desc:
            return "Single"
        if "LP" in desc:
            return "Album"
        if "EP" in desc:
            return "EP"
        return "Album"

    # extract release info from musicbrainz
    def _extract_musicbrainz(self) -> dict:
        import musicbrainzngs
        musicbrainzngs.set_useragent('musicApp', '0.1', 'localhost')
        musicbrainzngs.set_rate_limit(True)

        # if not contains artist or title, return empty.
        if not hasattr(self, "release_artists") or not hasattr(self, "release"):
            return {}

        # to use in musicbrainz search
        original_artists_list = [ artist.name for artist in self.release.artists ]
        original_artists = ', '.join(original_artists_list)
        mb_artist = original_artists if original_artists else ""
        mb_release = self.release.title if hasattr(self.release, "title") else ""

        if not mb_artist or not mb_release:
            return {}

        # ---------- Cache ----------
        cache_key = f"mb_{mb_artist}_{mb_release}".replace(" ", "_")
        cached = cache_get(cache_key)
        if cached:
            return cached
        # ---------------------------

        # MusicBrainz search
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

        # most detail search to refine results.
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

        # artist id
        mb_artistid = None
        artist_credit = mb_release_full.get('artist-credit', [])
        if artist_credit and 'artist' in artist_credit[0]:
            mb_artistid = artist_credit[0]['artist'].get('id')

        # release group id
        mb_releasegroupid = mb_release_full.get('release-group', {}).get('id', '')

        # release date
        rg = mb_release_full.get('release-group', {})
        release_date = rg.get('first-release-date', None)
        if release_date:
            date_str = release_date.strip()
            # YYYY
            if re.fullmatch(r"\d{4}", date_str):
                release_date = [f"{date_str}-01-01", "year"]
            # YYYY-MM
            if re.fullmatch(r"\d{4}-\d{2}", date_str):
                release_date = [f"{date_str}-01", "month"]
            # YYYY-MM-DD
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
                release_date = [date_str, "day"]

        result = {
            "release_date": release_date[0] or "",
            "release_date_precision": release_date[1] or "",
            "musicbrainz_artistid": mb_artistid or "",
            "musicbrainz_albumid": release_id or "",
            "musicbrainz_releasegroupid": mb_releasegroupid or ""
        }

        # --------- save in cache -----------
        cache_set(cache_key, result)
        # -----------------------------------

        return result


    def _extract_metadata(self) -> dict:
        return {
            "album_title": normalize_title(self.release.title) or normalize_title(self.release.master.title),
            "release_year": safe_get(self.release, ['year'], safe_get(self.release.master, ['year'], 1900)),
            "album_artist": normalize_title(self.album_artist),
            "region": safe_get(self.release, ['country'], 'Unknown'),
            "stats": extract_release_stats(self.release.formats[0]),
            "genres": self.release.genres if self.release.genres else ["Unclassified"],
            "styles": self.release.styles if self.release.styles else ["Unclassified"],
            "publishers": [publisher.name for publisher in self.release.labels] if self.release.labels else [],
        }


    def _extract_tracks(self) -> Tuple[bool, List[Dict[str, Union[int, str]]]]:
        # normalize tracklist (exclude empty spaces and unificate separator)
        default_tracklist = self.release.tracklist or safe_get(self.release, ['master', 'tracklist'], [])
        normalized_tracks = normalize_discogs_tracklist(default_tracklist)

        tracks = []
        has_multiple = False
        tracklist_idx = 0

        # t will be -> {'track': idx, 'position': '1', 'title': 'TrackName'}
        for t in normalized_tracks:
            track_obj = None

            # loop thougth tracklist until find next valid track
            while tracklist_idx < len(self.release.tracklist):
                candidate = self.release.tracklist[tracklist_idx]
                tracklist_idx += 1

                title_candidate = candidate.title.strip() if candidate.title else ""
                position_candidate = candidate.position.strip() if candidate.position else ""

                if title_candidate not in ("", "-") or position_candidate != "":
                    track_obj = candidate
                    break

            # track_obj it is a current valid track. <Track 'Position' 'Title'>
            if track_obj is None:
                # fallback
                track_obj = Track(self.release)
                track_obj.title = t["title"]
                track_obj.position = t["position"]
                track_obj.artists = []

            # extract artists.
            # send current track obj and release artists list as parameters.
            # track artists returned with primary and featured artists.
            track_artists = get_track_artists(track_obj, self.release_artists)

            # set has_multiple flag.
            if len(track_artists["primary"]) > 1:
                has_multiple = True

            # right disc_number.
            disc_number = extract_disc_num(t["position"])
            if disc_number < 1:
                disc_number = 1  # secure fallback

            # return object
            tracks.append({
                "position": t["track"],
                "original_position": normalize_track_position(t["position"]),
                "title": normalize_title(t["title"]),
                "artists": track_artists,
                "disc_number": disc_number
            })

        return has_multiple, tracks

    # write all release info in a toml file using toml class helper.
    def write_info_file(self):
        info_file = self.output_dir / "info_.toml"

        # calcula total_tracks por disco
        from collections import defaultdict
        disc_counts = defaultdict(int)
        for track in self.tracks:
            disc_number = track.get("disc_number", 1)
            disc_counts[disc_number] += 1

        with open(info_file, "w", encoding="utf-8") as f:
            f.write('schema = "music.library.release"\n')
            f.write("schema_version = 1\n")
            f.write("\n")

            writer = TomlWriter(f)

            writer.write_block("release", {
                "title": self.metadata["album_title"],
                "artist": self.metadata["album_artist"],
                "release_type": self._get_release_group(),
                "release_year": self.metadata["release_year"],
                "release_date": self.metadata["release_date"],
                "release_date_precision": self.metadata["release_date_precision"],
                "publishers": list(dict.fromkeys(self.metadata["publishers"])),
            })

            # separate genres for more control
            genres_primary, *genres_secondary = self.metadata["genres"]
            writer.write_block("release.genres", {
                "primary": genres_primary,
                "secondary": genres_secondary,
            })

            # extra release info
            writer.write_block("release.extra", {
                "region": self.metadata["region"],
                "descriptions": self.metadata["stats"]["descriptions"],
                "styles": self.metadata["styles"],
            })

            print(self.metadata["stats"]["total_discs"])

            for d in range(1, self.metadata["stats"]["total_discs"] + 1):
                if self.metadata["stats"]["multi_disc_flag"]:
                    writer.write_array_block("discs", {
                        "index": d,
                        "media_format": self.metadata["stats"]["media_format"],
                        "total_tracks": disc_counts.get(d, 0),
                    })
                else:
                    writer.write_array_block("discs", {
                        "index": d,
                        "media_format": self.metadata["stats"]["media_format"],
                    })

            for track in self.tracks:
                track_block = { "position": track["position"] }
                if self.metadata["stats"]["multi_disc_flag"]:
                    track_block["disc_number"] = track["disc_number"]
                track_block["title"] = track["title"]

                writer.write_array_block("tracks", track_block)

                artists_block = {
                    "primary": track["artists"]["primary"]
                }
                if track["artists"]["featured"]:
                    artists_block.update({
                        "featured": track["artists"]["featured"],
                        "add_featured_in_title": False,
                        "add_featured_in_artists": False
                    })

                writer.write_subblock("tracks", "artists", artists_block)

            writer.write_block("sources", {
                "discogs": True,
                "musicbrainz": True,
            })

            writer.write_block("ids.musicbrainz", {
                "artist": self.metadata["musicbrainz_artistid"],
                "release": self.metadata["musicbrainz_albumid"],
                "master": self.metadata["musicbrainz_releasegroupid"],
            })

            writer.write_block("ids.discogs", {
                "artist": [a.id for a in self.release.artists],
                "release": self.release.id,
                "master": safe_get(self.release.master, ["id"], self.release.id),
            })

            writer.write_block("control", {
                "locker": False,
                "write_tags": True,
                "write_cover": True,
                "add_secondary_genres": True,
                "add_subtitle_in_title": True,
                "add_featured_in_title": True,
                "add_featured_in_artists": False,
                "write_mode": "overwrite",
            })

            f.write("\n")

    # download first image find in release
    def download_cover(self):
        if not self.release.images:
            logging.error(f"No cover for: {self.metadata['album_title']}")
            return
        logging.info(f"Downloading cover for: {self.metadata['album_title']}")
        get_cover(self.release.images[0]["uri"], self.output_dir)

    # save downloaded files in a album folder
    def move_folder(self):
        album_folder_name = f"{self.metadata['release_year']} - {self.metadata['album_title']}"
        album_folder_name = sanitize_path_name(album_folder_name)
        album_folder_path = self.output_dir /album_folder_name
        create_folder(self.output_dir / "info_.toml", self.output_dir / "folder-tmp.jpg", album_folder_path)


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

    # only create album folder when not in batch mode
    if not args.batch:
        processor.move_folder()


# search release from text
def search_id(search_item: str):
    try:
        result = auth_search.search(search_item, type="release", format=args.type)
    except discogs_client.exceptions.HTTPError:
        logging.error("Bad release search")
        return
    except Exception as err:
        logging.error(err)
        return

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

