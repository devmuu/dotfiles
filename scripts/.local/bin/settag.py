#!/usr/bin/env python
# ==============================================================================
# Program:       settag
# Description:   Set audio metadata and optionally rename files
# Software/Tool: python3 / eyed3 / toml
# ==============================================================================

import os
import re
import argparse
from pathlib import Path
from functools import lru_cache
from typing import List, Optional, Dict

import toml
import eyed3
from eyed3.id3.frames import ImageFrame

# ---------------------------
# ANSI colors for terminal
# ---------------------------
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

# ---------------------------
# Helpers
# ---------------------------
def normalize_index(filename: str) -> str:
    match = re.match(r"(\d+)", filename)
    if not match:
        raise ValueError("No track number found")
    return match.group(1).zfill(2)

def first_artist(artist_field: str) -> str:
    return artist_field.split(";")[0].strip()

@lru_cache(maxsize=256)
def load_toml(path: Path):
    return toml.load(path)

# ---------------------------
# Core Class
# ---------------------------
class MusicTagProcessor:
    def __init__(
        self,
        *,
        audio_dir: Path,
        metadata_dir: Path,
        work_dir: Path,
        recursive: bool = False,
        toml_name: str = "info.toml",
        audio_format: str = "mp3",
        dry_run: bool = False,
        rename_mode: Optional[str] = None,
        apply_and_rename: bool = False,
        only_tags: bool = False,
        only_cover: bool = False,
        custom_toml: Optional[Path] = None,
        verbose: bool = False
    ):
        self.audio_dir = audio_dir
        self.metadata_dir = metadata_dir
        self.work_dir = work_dir
        self.recursive = recursive
        self.toml_name = toml_name
        self.audio_format = audio_format
        self.dry_run = dry_run
        self.rename_mode = rename_mode
        self.apply_and_rename = apply_and_rename
        self.only_tags = only_tags
        self.only_cover = only_cover
        self.custom_toml = custom_toml
        self.verbose = verbose

        if self.only_tags and self.only_cover:
            raise ValueError("Use only one of --only-tags or --only-cover")
        if self.rename_mode and self.only_cover:
            raise ValueError("--rename cannot be combined with --only-cover")

        self.cover_cache: Dict[Path, Dict[str, Path]] = {}

        # Counters
        self.total_files = 0
        self.tagged_files = 0
        self.cover_files = 0
        self.renamed_files = 0
        self.ignored_no_toml = 0
        self.ignored_errors = 0
        self.toml_usage: Dict[str, int] = {}

        self.directories = self._scan_directories()

    # ---------------------------
    # Scan directories
    # ---------------------------
    def _scan_directories(self) -> List[Path]:
        dirs = set()
        iterator = (
            self.work_dir.rglob(f"*.{self.audio_format}") if self.recursive
            else self.work_dir.glob(f"*.{self.audio_format}")
        )
        for file in iterator:
            dirs.add(file.parent)
        return sorted(dirs)

    # ---------------------------
    # Find TOML
    # ---------------------------
    def _find_toml(self, directory: Path) -> (Optional[Path], Optional[str]):
        if self.custom_toml and self.custom_toml.exists():
            return self.custom_toml, "custom toml"
        local = directory / self.toml_name
        if local.exists():
            return local, "mp3 toml"
        mirror = Path(
            re.sub(
                f"{self.audio_dir}/music/(archived|disposable|main|review)",
                str(self.metadata_dir),
                str(directory),
            )
        ) / self.toml_name
        if mirror.exists():
            return mirror, "mirror toml"
        return None, None

    # ---------------------------
    # Resolve cover with caching
    # ---------------------------
    def _resolve_cover(
            self,
            mp3_dir: Path,
            data_path: Path,
            tracks,
            artist: str,
            idx: str) -> Tuple[Path, str]:

        if mp3_dir in self.cover_cache and idx in self.cover_cache[mp3_dir]:
            cover = self.cover_cache[mp3_dir][idx]
            return cover, "cache"

        candidates = []

        track = None
        if isinstance(tracks, list):
            track = tracks[int(idx) - 1]

            # 1. custom track image
            if "image" in track:
                candidates.append(data_path / track["image"])

            # 2. album cover from album/year keys
            elif "album" in track and "year" in track:
                cover_path = self.metadata_dir / "Artists" / track["artist"] / f'{track["year"]} - {track["album"]}' / "cover.jpg"
                if self.verbose:
                    print(f"[DEBUG] Checking album cover: {cover_path}")
                if cover_path.exists():
                    candidates.append(cover_path)

        # 3. fallback candidates
        candidates.extend([
            mp3_dir / "covers" / f"cover{idx}.jpg",
            mp3_dir / "cover.jpg",
            data_path / "cover.jpg",
            self.metadata_dir / "Artists" / first_artist(artist) / "cover.jpg",
            self.metadata_dir / "cover.jpg",
        ])

        for c in candidates:
            if self.verbose:
                print(f"[DEBUG] Candidate cover: {c}")
            if c.exists():
                if mp3_dir not in self.cover_cache:
                    self.cover_cache[mp3_dir] = {}
                self.cover_cache[mp3_dir][idx] = c

                if track and "image" in track and c == data_path / track["image"]:
                    origin = "track image"
                elif c in [mp3_dir / f"cover{idx}.jpg", mp3_dir / "cover.jpg"]:
                    origin = "mp3 folder"
                elif c == data_path / "cover.jpg":
                    origin = "TOML folder"
                elif c == self.metadata_dir / "Artists" / first_artist(artist) / "cover.jpg":
                    origin = "artist folder"
                else:
                    origin = "metadata folder"

                return c, origin

        raise FileNotFoundError(f"No cover image found for track {idx} in {mp3_dir}")

    # ---------------------------
    # Process directories
    # ---------------------------
    def process(self):
        for directory in self.directories:
            album_total, album_tagged, album_cover, album_errors, album_skip = self._process_directory(directory)
            if album_total == 0:
                continue
            print(f"{Colors.YELLOW}[ALBUM]{Colors.RESET} {directory.name} | "
                  f"Tracks: {album_total}, TAGs: {album_tagged}, COVERs: {album_cover}, "
                  f"Errors: {album_errors}, Skipped: {album_skip}")

        self._print_summary()
        print(f"{Colors.GREEN}[DONE]{Colors.RESET}")

    def _process_directory(self, directory: Path):
        toml_path, toml_origin = self._find_toml(directory)
        album_total = album_tagged = album_cover = album_errors = album_skip = 0

        if not toml_path:
            self.ignored_no_toml += 1
            album_skip = len(list(directory.glob(f"*.{self.audio_format}")))
            return album_total, album_tagged, album_cover, album_errors, album_skip

        self.toml_usage[toml_origin] = self.toml_usage.get(toml_origin, 0) + 1

        files = sorted(f for f in directory.iterdir() if f.is_file() and f.suffix == f".{self.audio_format}")
        album_total = len(files)
        self.total_files += album_total

        for file in files:
            try:
                idx = normalize_index(file.name)
                if self.rename_mode and not self.apply_and_rename:
                    self._rename_file(file)
                    continue
                if self.apply_and_rename:
                    tagged, cover_set = self._write_tags(file, toml_path, toml_origin, idx)
                    album_tagged += tagged
                    album_cover += cover_set
                    if not self.dry_run:
                        self._rename_file(file)
                    continue
                if self.dry_run:
                    continue
                tagged, cover_set = self._write_tags(file, toml_path, toml_origin, idx)
                album_tagged += tagged
                album_cover += cover_set
            except Exception:
                self.ignored_errors += 1
                album_errors += 1

        self.tagged_files += album_tagged
        self.cover_files += album_cover

        return album_total, album_tagged, album_cover, album_errors, album_skip

    # ---------------------------
    # Write tags
    # ---------------------------
    def _write_tags(self, file: Path, toml_path: Path, toml_origin: str, idx: str):
        data = load_toml(toml_path)
        stats = data["stats"]
        tracks = data["tracks"]

        album_artist = stats["artist"]
        album = stats["album"]
        disc = stats["discs"].split(",")
        year = stats["year"]
        genre = stats["genre"]
        total_tracks = len(tracks)

        if isinstance(tracks, list):
            track = tracks[int(idx) - 1]
            title = track["title"]
            artist = track["artist"]
        else:
            title = tracks[f"track{idx}"]
            artist = album_artist

        audio = eyed3.load(file)
        if not audio.tag:
            audio.initTag()
        audio.tag.clear()

        tag_count = cover_count = 0

        if not self.only_cover:
            audio.tag.track_num = (int(idx), total_tracks)
            audio.tag.title = title
            audio.tag.album = album
            audio.tag.recording_date = year
            audio.tag.release_date = year
            audio.tag.artist = artist.replace("; ", "\x00")
            audio.tag.album_artist = album_artist.replace("; ", "\x00")
            audio.tag.genre = genre.replace("; ", "\x00")
            audio.tag.disc_num = (int(disc[0]), int(disc[-1]))
            audio.tag.comments.set("null")
            audio.tag.publisher = "null"
            audio.tag.copyright = "null"
            tag_count = 1

        if not self.only_tags:
            cover, cover_origin = self._resolve_cover(file.parent, toml_path.parent, tracks, artist, idx)
            image_descriptions = [img.description for img in audio.tag.images]
            for desc in image_descriptions:
                audio.tag.images.remove(desc)
            audio.tag.images.set(
                ImageFrame.FRONT_COVER,
                cover.read_bytes(),
                "image/jpeg",
            )
            cover_count = 1

        if not self.dry_run:
            audio.tag.save()

        if self.verbose:
            if not self.only_cover:
                print(f"{Colors.GREEN}[TAGS]{Colors.RESET} {file.name} → {toml_origin}")
            if not self.only_tags:
                print(f"{Colors.BLUE}[COVER]{Colors.RESET} Track {idx} → {cover.name} (from {cover_origin})")

        return tag_count, cover_count

    # ---------------------------
    # Rename
    # ---------------------------
    def _rename_file(self, file: Path):
        sep = " - " if self.rename_mode == "dash" else ". " if self.rename_mode == "dot" else " - "
        audio = eyed3.load(file)
        title = re.sub(r"[/*?!¿]", "_", audio.tag.title)
        new_name = f"{audio.tag.track_num[0]:02}{sep}{title}"
        if self.dry_run:
            return
        try:
            audio.rename(new_name)
            self.renamed_files += 1
        except OSError:
            pass

    # ---------------------------
    # Summary
    # ---------------------------
    def _print_summary(self):
        print("\n[SUMMARY]")
        print(f"Total MP3 files scanned : {self.total_files}")
        print(f"Total TAGs updated      : {self.tagged_files}")
        print(f"Total COVERs updated    : {self.cover_files}")
        print(f"Total files renamed     : {self.renamed_files}")
        print(f"Files skipped (no TOML) : {self.ignored_no_toml}")
        print(f"Files skipped (errors)  : {self.ignored_errors}")
        print("TOML usage count        :")
        for origin, count in self.toml_usage.items():
            print(f"  {origin}: {count}")

# ---------------------------
# CLI
# ---------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Music tag processor")
    parser.add_argument("path", type=Path, help="Root directory")
    parser.add_argument("-i", "--info", type=Path, help="Custom TOML file")
    parser.add_argument("-r", "--rename", choices=["dash", "dot"])
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("-f", "--format", default="mp3")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--only-tags", action="store_true")
    parser.add_argument("--only-cover", action="store_true")
    parser.add_argument("--apply-and-rename", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Show detailed log per file")
    return parser.parse_args()

def main():
    args = parse_args()
    if not args.path.exists():
        print(f"{Colors.RED}[ERROR]{Colors.RESET} Invalid path: {args.path}")
        return

    audio_dir = Path(os.environ.get("AUDIO_DIR", "."))
    metadata_dir = audio_dir / "metadata"

    processor = MusicTagProcessor(
        audio_dir=audio_dir,
        metadata_dir=metadata_dir,
        work_dir=args.path,
        recursive=args.recursive,
        audio_format=args.format,
        dry_run=args.dry_run,
        rename_mode=args.rename,
        apply_and_rename=args.apply_and_rename,
        only_tags=args.only_tags,
        only_cover=args.only_cover,
        custom_toml=args.info,
        verbose=args.verbose
    )

    processor.process()

if __name__ == "__main__":
    main()

