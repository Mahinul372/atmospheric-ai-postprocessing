"""Inspect one real HRRR/MRMS pair and write a traceable metadata manifest."""
from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO

import numpy as np
from eccodes import codes_get, codes_get_values, codes_grib_new_from_file, codes_release

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sample"
INTERIM = ROOT / "data" / "interim" / "sample"
MANIFEST = ROOT / "data" / "manifests" / "sample_20240501_1300.json"
HRRR_NAME = "hrrr.t12z.wrfsfcf01.APCP.grib2"
MRMS_NAME = "MRMS_RadarOnly_QPE_01H_00.00_20240501-130000.grib2.gz"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_grib(stream: BinaryIO) -> tuple[dict, np.ndarray]:
    gid = codes_grib_new_from_file(stream)
    if gid is None:
        raise ValueError("No GRIB message found")
    keys = [
        "discipline", "parameterCategory", "parameterNumber", "shortName", "name", "units",
        "typeOfLevel", "dataDate", "dataTime", "validityDate", "validityTime", "stepType",
        "stepRange", "startStep", "endStep", "gridType", "Ni", "Nj", "numberOfValues",
        "missingValue", "latitudeOfFirstGridPointInDegrees", "longitudeOfFirstGridPointInDegrees",
        "latitudeOfLastGridPointInDegrees", "longitudeOfLastGridPointInDegrees",
        "iDirectionIncrementInDegrees", "jDirectionIncrementInDegrees", "DxInMetres", "DyInMetres",
        "iScansNegatively", "jScansPositively", "jPointsAreConsecutive", "alternativeRowScanning",
        "bitmapPresent", "referenceValue", "bitsPerValue", "productDefinitionTemplateNumber",
    ]
    meta = {}
    for key in keys:
        try:
            meta[key] = codes_get(gid, key)
        except Exception:
            continue
    values = np.asarray(codes_get_values(gid), dtype=np.float32)
    codes_release(gid)
    return meta, values


def valid_datetime(meta: dict, prefix: str = "validity") -> datetime:
    date = str(meta[f"{prefix}Date"])
    time = int(meta[f"{prefix}Time"])
    return datetime.strptime(f"{date}{time:04d}", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)


def hrrr_window(meta: dict) -> tuple[datetime, datetime]:
    init = datetime.strptime(f"{meta['dataDate']}{int(meta['dataTime']):04d}", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    return init + timedelta(hours=int(meta["startStep"])), init + timedelta(hours=int(meta["endStep"]))


def previous_hour_window(valid: datetime) -> tuple[datetime, datetime]:
    return valid - timedelta(hours=1), valid


def periods_match(forecast_start: datetime, forecast_end: datetime, observation_start: datetime, observation_end: datetime) -> bool:
    return forecast_start == observation_start and forecast_end == observation_end


def main() -> None:
    hrrr_path = RAW / HRRR_NAME
    mrms_gz_path = RAW / MRMS_NAME
    if not hrrr_path.is_file() or not mrms_gz_path.is_file():
        raise FileNotFoundError(f"Expected sample files under {RAW}")

    INTERIM.mkdir(parents=True, exist_ok=True)
    mrms_path = INTERIM / MRMS_NAME.removesuffix(".gz")
    if not mrms_path.exists() or mrms_path.stat().st_mtime < mrms_gz_path.stat().st_mtime:
        with gzip.open(mrms_gz_path, "rb") as source, mrms_path.open("wb") as target:
            target.write(source.read())

    with hrrr_path.open("rb") as stream:
        hrrr, hrrr_values = inspect_grib(stream)
    with mrms_path.open("rb") as stream:
        mrms, mrms_values = inspect_grib(stream)

    forecast_start, forecast_end = hrrr_window(hrrr)
    observation_end = valid_datetime(mrms)
    observation_start, observation_end = previous_hour_window(observation_end)

    checks = {
        "HRRR_is_surface_total_precipitation": hrrr.get("parameterCategory") == 1 and hrrr.get("parameterNumber") == 8 and hrrr.get("typeOfLevel") == "surface",
        "HRRR_is_one_hour_accumulation": hrrr.get("stepType") == "accum" and hrrr.get("startStep") == 0 and hrrr.get("endStep") == 1,
        "MRMS_is_RadarOnly_QPE_01H": mrms.get("discipline") == 209 and mrms.get("parameterCategory") == 6 and mrms.get("parameterNumber") == 2,
        "HRRR_and_MRMS_windows_match": periods_match(forecast_start, forecast_end, observation_start, observation_end),
        "grid_value_counts_match_metadata": hrrr_values.size == hrrr.get("numberOfValues") and mrms_values.size == mrms.get("numberOfValues"),
    }
    if not all(checks.values()):
        raise AssertionError(f"Sample validation failed: {checks}")

    mrms_grid = mrms_values.reshape(int(mrms["Nj"]), int(mrms["Ni"]))
    # Approximate Georgia-plus-buffer bounding box; longitudes are represented on 0..360.
    mrms_lat0 = float(mrms["latitudeOfFirstGridPointInDegrees"])
    mrms_lon0 = float(mrms["longitudeOfFirstGridPointInDegrees"])
    dlat = float(mrms["jDirectionIncrementInDegrees"])
    dlon = float(mrms["iDirectionIncrementInDegrees"])
    j0 = max(0, int(np.floor((mrms_lat0 - 35.5) / dlat)))
    j1 = min(int(mrms["Nj"]), int(np.ceil((mrms_lat0 - 29.5) / dlat)))
    i0 = max(0, int(np.floor((274.0 - mrms_lon0) / dlon)))
    i1 = min(int(mrms["Ni"]), int(np.ceil((280.0 - mrms_lon0) / dlon)))
    ga_buffer = mrms_grid[j0:j1, i0:i1]

    def value_summary(values: np.ndarray) -> dict:
        return {
            "count": int(values.size),
            "negative_sentinel_count": int(np.count_nonzero(values < 0)),
            "zero_count": int(np.count_nonzero(values == 0)),
            "positive_count": int(np.count_nonzero(values > 0)),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
        }

    manifest = {
        "sample_id": "2024-05-01T13:00:00Z_HRRR_f01_vs_MRMS_01H",
        "temporal_match": {
            "forecast_initialization_utc": forecast_start.isoformat().replace("+00:00", "Z"),
            "forecast_lead_hours": 1,
            "forecast_valid_time_utc": forecast_end.isoformat().replace("+00:00", "Z"),
            "forecast_accumulation_start_utc": forecast_start.isoformat().replace("+00:00", "Z"),
            "forecast_accumulation_end_utc": forecast_end.isoformat().replace("+00:00", "Z"),
            "observation_accumulation_start_utc": observation_start.isoformat().replace("+00:00", "Z"),
            "observation_accumulation_end_utc": observation_end.isoformat().replace("+00:00", "Z"),
            "mrms_period_basis": "RadarOnly_QPE_01H accumulation is the preceding 60 minutes; timestamp is the valid/end time, per NOAA WDTD MRMS training material.",
            "periods_match": checks["HRRR_and_MRMS_windows_match"],
        },
        "sources": {
            "hrrr": {
                "bucket": "s3://noaa-hrrr-bdp-pds",
                "object": "hrrr.20240501/conus/hrrr.t12z.wrfsfcf01.grib2",
                "index_object": "hrrr.20240501/conus/hrrr.t12z.wrfsfcf01.grib2.idx",
                "byte_range_inclusive": [59755654, 60073889],
                "local_file": f"data/raw/sample/{HRRR_NAME}",
                "sha256": sha256(hrrr_path),
                "bytes": hrrr_path.stat().st_size,
                "metadata": hrrr,
                "values": value_summary(hrrr_values),
                "unit_interpretation": "kg m-2; numerically equivalent to mm liquid-water depth",
            },
            "mrms": {
                "bucket": "s3://noaa-mrms-pds",
                "object": "CONUS/RadarOnly_QPE_01H_00.00/20240501/MRMS_RadarOnly_QPE_01H_00.00_20240501-130000.grib2.gz",
                "local_file": f"data/raw/sample/{MRMS_NAME}",
                "sha256": sha256(mrms_gz_path),
                "bytes": mrms_gz_path.stat().st_size,
                "decompressed_bytes": mrms_path.stat().st_size,
                "metadata": mrms,
                "values": value_summary(mrms_values),
                "documented_unit": "mm",
                "documented_missing_and_fill_values": [-1, -3],
                "approximate_georgia_buffer": {
                    "bbox_degrees": {"south": 29.5, "north": 35.5, "west": -86.0, "east": -80.0},
                    "array_slice_j_i": [[j0, j1], [i0, i1]],
                    "shape": list(ga_buffer.shape),
                    "negative_sentinel_count": int(np.count_nonzero(ga_buffer < 0)),
                    "valid_fraction": float(np.count_nonzero(ga_buffer >= 0) / ga_buffer.size),
                    "maximum_valid_value_mm": float(ga_buffer[ga_buffer >= 0].max()),
                    "note": "Bounding-box diagnostic only; not a state polygon or final remapped dataset.",
                },
            },
        },
        "spatial_alignment": {
            "hrrr_grid": {key: hrrr.get(key) for key in ["gridType", "Ni", "Nj", "DxInMetres", "DyInMetres", "latitudeOfFirstGridPointInDegrees", "longitudeOfFirstGridPointInDegrees"]},
            "mrms_grid": {key: mrms.get(key) for key in ["gridType", "Ni", "Nj", "iDirectionIncrementInDegrees", "jDirectionIncrementInDegrees", "latitudeOfFirstGridPointInDegrees", "longitudeOfFirstGridPointInDegrees", "latitudeOfLastGridPointInDegrees", "longitudeOfLastGridPointInDegrees"]},
            "same_grid": False,
            "remapping_performed": False,
        },
        "validation_checks": checks,
        "software": {"python": "3.13.7", "eccodes": "2.50.0", "numpy": np.__version__},
        "not_model_training_data": True,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST), "checks": checks, "hrrr_values": manifest["sources"]["hrrr"]["values"], "mrms_values": manifest["sources"]["mrms"]["values"], "ga_buffer": manifest["sources"]["mrms"]["approximate_georgia_buffer"]}, indent=2))


if __name__ == "__main__":
    main()
