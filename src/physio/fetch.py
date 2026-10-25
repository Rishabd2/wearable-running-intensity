"""Download the open physiology datasets and verify every file against a checksum.

Files land in ``data/raw/<dataset>/`` (gitignored). Checksums come from
``data/manifest.json``. That manifest is built from each repository's own
API (Harvard Dataverse MD5, figshare MD5, PhysioNet SHA256SUMS.txt) with
``python -m src.physio.fetch --build-manifest``; the committed copy is what
``fetch`` verifies against.

Usage::

    python -m src.physio.fetch            # download and verify
    python -m src.physio.fetch --verify   # verify files already on disk
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.json"

DATAVERSE_DOI = "doi:10.7910/DVN/ZS2Z2J"
DATAVERSE_FILES = {"aw_fb_data.csv"}
FIGSHARE_ARTICLE = 4543435
FIGSHARE_INFO_ID = 39452932  # RBDSinfo.txt, current revision
PHYSIONET_BASE = "https://physionet.org/files/treadmill-exercise-cardioresp/1.0.1/"
PHYSIONET_FILES = ["subject-info.csv", "test_measure.csv"]
USER_AGENT = "spotify-running-physiology/1.0 (research fetch script)"


def _get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def build_manifest() -> dict:
    """Query each repository API and record URL plus published checksum per file."""
    entries = []

    meta = json.loads(_get(
        "https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=" + DATAVERSE_DOI
    ))["data"]["latestVersion"]
    for f in meta["files"]:
        df = f["dataFile"]
        if df["filename"] in DATAVERSE_FILES:
            entries.append({
                "dataset": "fuller_apple_watch",
                "name": df["filename"],
                "url": f"https://dataverse.harvard.edu/api/access/datafile/{df['id']}",
                "algo": "md5",
                "checksum": df["md5"],
                "size": df["filesize"],
            })

    art = json.loads(_get(f"https://api.figshare.com/v2/articles/{FIGSHARE_ARTICLE}"))
    for f in art["files"]:
        keep = re.fullmatch(r"RBDS\d{3}runT(25|35|45)forces\.txt", f["name"]) or f["id"] == FIGSHARE_INFO_ID
        if keep:
            entries.append({
                "dataset": "fukuchi_running",
                "name": f["name"],
                "url": f["download_url"],
                "algo": "md5",
                "checksum": f["computed_md5"],
                "size": f["size"],
            })

    sums = _get(PHYSIONET_BASE + "SHA256SUMS.txt").decode()
    published = {line.split()[1]: line.split()[0] for line in sums.splitlines() if line.strip()}
    for name in PHYSIONET_FILES:
        entries.append({
            "dataset": "malaga_treadmill",
            "name": name,
            "url": PHYSIONET_BASE + name,
            "algo": "sha256",
            "checksum": published[name],
            "size": None,
        })

    entries.sort(key=lambda e: (e["dataset"], e["name"]))
    return {"built": time.strftime("%Y-%m-%d"), "files": entries}


def _digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def target(entry: dict, raw: Path = RAW) -> Path:
    return raw / entry["dataset"] / entry["name"]


def verify(raw: Path = RAW) -> list[str]:
    """Return the names of files that are missing or fail their checksum."""
    bad = []
    for entry in load_manifest()["files"]:
        path = target(entry, raw)
        if not path.exists() or _digest(path, entry["algo"]) != entry["checksum"]:
            bad.append(f"{entry['dataset']}/{entry['name']}")
    return bad


def fetch(raw: Path = RAW, retries: int = 4) -> None:
    files = load_manifest()["files"]
    for i, entry in enumerate(files, 1):
        path = target(entry, raw)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and _digest(path, entry["algo"]) == entry["checksum"]:
            continue
        for attempt in range(1, retries + 1):
            try:
                data = _get(entry["url"], timeout=600)
            except OSError as exc:  # network hiccup: retry
                print(f"  retry {attempt} {entry['name']}: {exc}", file=sys.stderr)
                time.sleep(2 * attempt)
                continue
            if hashlib.new(entry["algo"], data).hexdigest() == entry["checksum"]:
                path.write_bytes(data)
                break
            print(f"  checksum mismatch {entry['name']} (attempt {attempt})", file=sys.stderr)
        else:
            raise SystemExit(f"could not fetch a verified copy of {entry['name']}")
        print(f"[{i}/{len(files)}] {entry['dataset']}/{entry['name']}")
    print(f"all {len(files)} files verified under {raw}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", action="store_true", help="only verify files on disk")
    parser.add_argument("--build-manifest", action="store_true", help="rebuild data/manifest.json from the APIs")
    args = parser.parse_args()
    if args.build_manifest:
        MANIFEST.write_text(json.dumps(build_manifest(), indent=1) + "\n", encoding="utf-8")
        print(f"wrote {MANIFEST}")
        return
    if args.verify:
        bad = verify()
        if bad:
            raise SystemExit("missing or bad: " + ", ".join(bad))
        print("all files verified")
        return
    fetch()


if __name__ == "__main__":
    main()
