"""Fetch traceable one-hour HRRR/MRMS pairs using the public NOAA S3 archives."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "events"


def fetch(url: str, destination: Path, headers: dict | None = None) -> tuple[int, str | None]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination.stat().st_size, None
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
        if headers and "Range" in headers and response.status != 206:
            raise RuntimeError(f"Expected HTTP 206 for range request, got {response.status}")
        destination.write_bytes(body)
        return len(body), response.headers.get("Content-Range")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_pair(date: str, cycle: str) -> dict:
    if not re.fullmatch(r"20\d{6}", date) or not re.fullmatch(r"\d{2}", cycle):
        raise ValueError("Use YYYYMMDD and a two-digit UTC cycle")
    init = datetime.strptime(date + cycle, "%Y%m%d%H").replace(tzinfo=timezone.utc)
    valid = init + timedelta(hours=1)
    valid_date = valid.strftime("%Y%m%d")
    valid_hh = valid.strftime("%H")
    hrrr_key = f"hrrr.{date}/conus/hrrr.t{cycle}z.wrfsfcf01.grib2"
    hrrr_base = "https://noaa-hrrr-bdp-pds.s3.amazonaws.com/"
    idx_url = hrrr_base + hrrr_key + ".idx"
    index = urllib.request.urlopen(idx_url, timeout=30).read().decode("utf-8")
    lines = index.splitlines()
    target = next((i for i, line in enumerate(lines) if ":APCP:surface:0-1 hour acc fcst:" in line), None)
    if target is None or target + 1 >= len(lines):
        raise RuntimeError(f"Could not locate a bounded APCP 0-1 h message in {idx_url}")
    start = int(lines[target].split(":", 2)[1])
    next_start = int(lines[target + 1].split(":", 2)[1])
    end = next_start - 1
    event_dir = RAW / date
    hrrr_path = event_dir / f"hrrr.t{cycle}z.wrfsfcf01.APCP.grib2"
    index_path = event_dir / f"hrrr.t{cycle}z.wrfsfcf01.grib2.idx"
    range_header = {"Range": f"bytes={start}-{end}"}
    _, content_range = fetch(hrrr_base + hrrr_key, hrrr_path, range_header)
    if content_range != f"bytes {start}-{end}/155228241" and content_range is not None:
        # Total source file size varies by date; validate the returned range prefix only.
        if not content_range.startswith(f"bytes {start}-{end}/"):
            raise RuntimeError(f"Unexpected Content-Range: {content_range}")
    fetch(idx_url, index_path)

    mrms_name = f"MRMS_RadarOnly_QPE_01H_00.00_{valid_date}-{valid_hh}0000.grib2.gz"
    mrms_key = f"CONUS/RadarOnly_QPE_01H_00.00/{valid_date}/{mrms_name}"
    mrms_url = "https://noaa-mrms-pds.s3.amazonaws.com/" + mrms_key
    mrms_path = event_dir / mrms_name
    fetch(mrms_url, mrms_path)
    manifest = {
        "initialization_utc": init.isoformat().replace("+00:00", "Z"),
        "valid_time_utc": valid.isoformat().replace("+00:00", "Z"),
        "forecast_accumulation_utc": [init.isoformat().replace("+00:00", "Z"), valid.isoformat().replace("+00:00", "Z")],
        "observation_accumulation_utc": [init.isoformat().replace("+00:00", "Z"), valid.isoformat().replace("+00:00", "Z")],
        "hrrr_object": hrrr_key,
        "hrrr_index_object": hrrr_key + ".idx",
        "hrrr_index_apcp_line": lines[target],
        "hrrr_byte_range_inclusive": [start, end],
        "hrrr_range_response": content_range,
        "hrrr_local_file": str(hrrr_path.relative_to(ROOT)),
        "hrrr_sha256": sha256(hrrr_path),
        "hrrr_bytes": hrrr_path.stat().st_size,
        "mrms_object": mrms_key,
        "mrms_local_file": str(mrms_path.relative_to(ROOT)),
        "mrms_sha256": sha256(mrms_path),
        "mrms_bytes": mrms_path.stat().st_size,
        "period_alignment_basis": "HRRR APCP message is 0-1 hour accumulation; NOAA WDTD describes RadarOnly_QPE_01H as accumulated over previous 60 minutes, timestamped at valid/end time.",
    }
    manifest_path = ROOT / "data" / "manifests" / f"pair_{date}_{cycle}z.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    pairs = [(sys.argv[1], sys.argv[2])] if len(sys.argv) == 3 else [("20240927", "00"), ("20240927", "12")]
    for pair in pairs:
        print(json.dumps(download_pair(*pair), indent=2))

