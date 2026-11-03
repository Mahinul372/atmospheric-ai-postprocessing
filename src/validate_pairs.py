"""Decode downloaded pairs and verify the GRIB metadata and precipitation values."""
from __future__ import annotations

import gzip
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from eccodes import codes_get, codes_get_values, codes_grib_new_from_file, codes_release

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = sorted((ROOT / "data" / "manifests").glob("pair_*z.json"))
INTERIM = ROOT / "data" / "interim" / "events"


def inspect(path: Path) -> tuple[dict, np.ndarray]:
    with path.open("rb") as stream:
        gid = codes_grib_new_from_file(stream)
        if gid is None:
            raise ValueError(f"No GRIB message in {path}")
        keys = ["discipline", "parameterCategory", "parameterNumber", "shortName", "name", "units", "typeOfLevel", "dataDate", "dataTime", "validityDate", "validityTime", "stepType", "stepRange", "startStep", "endStep", "gridType", "Ni", "Nj", "numberOfValues", "DxInMetres", "DyInMetres", "iDirectionIncrementInDegrees", "jDirectionIncrementInDegrees"]
        meta = {}
        for key in keys:
            try:
                meta[key] = codes_get(gid, key)
            except Exception:
                pass
        values = np.asarray(codes_get_values(gid), dtype=np.float32)
        codes_release(gid)
    return meta, values


def dt(date: int, time: int) -> datetime:
    return datetime.strptime(f"{date}{int(time):04d}", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    if not MANIFESTS:
        raise FileNotFoundError("No pair manifests found")
    for manifest_path in MANIFESTS:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        hrrr_path = ROOT / Path(manifest["hrrr_local_file"])
        mrms_gz = ROOT / Path(manifest["mrms_local_file"])
        mrms_path = INTERIM / mrms_gz.name.removesuffix(".gz")
        if not mrms_path.exists() or mrms_path.stat().st_mtime < mrms_gz.stat().st_mtime:
            with gzip.open(mrms_gz, "rb") as source, mrms_path.open("wb") as target:
                target.write(source.read())
        h, hp = inspect(hrrr_path)
        m, mp = inspect(mrms_path)
        init = dt(h["dataDate"], h["dataTime"])
        forecast_start = init + timedelta(hours=int(h["startStep"]))
        forecast_end = init + timedelta(hours=int(h["endStep"]))
        observed_valid = dt(m["validityDate"], m["validityTime"])
        observation_start = observed_valid - timedelta(hours=1)
        expected_valid = datetime.fromisoformat(manifest["valid_time_utc"].replace("Z", "+00:00"))
        checks = {
            "forecast_field_is_surface_total_precip": h.get("parameterCategory") == 1 and h.get("parameterNumber") == 8 and h.get("typeOfLevel") == "surface",
            "forecast_window_is_zero_to_one_hour": h.get("stepType") == "accum" and h.get("startStep") == 0 and h.get("endStep") == 1,
            "observation_product_is_radaronly_qpe_01h": m.get("discipline") == 209 and m.get("parameterCategory") == 6 and m.get("parameterNumber") == 2,
            "valid_time_matches_manifest": forecast_end == expected_valid == observed_valid,
            "accumulation_windows_match": forecast_start == observation_start and forecast_end == observed_valid,
            "decoded_counts_match_grid_metadata": hp.size == h.get("numberOfValues") and mp.size == m.get("numberOfValues"),
        }
        if not all(checks.values()):
            raise AssertionError(f"{manifest_path.name}: {checks}")
        manifest["grib_validation"] = {
            "checks": checks,
            "hrrr_metadata": h,
            "mrms_metadata": m,
            "hrrr_values_min_max": [float(hp.min()), float(hp.max())],
            "mrms_values_min_max_including_sentinels": [float(mp.min()), float(mp.max())],
            "mrms_negative_sentinel_count_full_conus": int(np.count_nonzero(mp < 0)),
            "decoded_mrms_path": str(mrms_path.relative_to(ROOT)),
            "observation_window_derived_from_documented_previous_60_minute_product": [observation_start.isoformat().replace("+00:00", "Z"), observed_valid.isoformat().replace("+00:00", "Z")],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(manifest_path.name, checks, "MRMS sentinels", int(np.count_nonzero(mp < 0)))


if __name__ == "__main__":
    main()
