"""Create a one-hour, Georgia-centered bbox sample using nearest MRMS grid points.

This is a spatial alignment smoke test only. It is not the final regridding method
or a state-polygon mask; it should not be used to claim model skill.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from eccodes import codes_get, codes_get_array, codes_get_values, codes_grib_new_from_file, codes_release

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sample"
INTERIM = ROOT / "data" / "interim" / "sample"
OUT = INTERIM / "ga_bbox_nearest_neighbor_20240501_1300.csv"
MANIFEST = ROOT / "data" / "manifests" / "sample_spatial_match.json"
HRRR_NAME = "hrrr.t12z.wrfsfcf01.APCP.grib2"
MRMS_NAME = "MRMS_RadarOnly_QPE_01H_00.00_20240501-130000.grib2.gz"


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    with (RAW / HRRR_NAME).open("rb") as stream:
        h = codes_grib_new_from_file(stream)
        hmeta = {key: codes_get(h, key) for key in ["Ni", "Nj", "DxInMetres", "DyInMetres", "dataDate", "dataTime", "validityDate", "validityTime", "stepRange"]}
        hrrr_values = np.asarray(codes_get_values(h), dtype=np.float32).reshape(int(hmeta["Nj"]), int(hmeta["Ni"]))
        hrrr_lat = np.asarray(codes_get_array(h, "latitudes"), dtype=np.float32).reshape(hrrr_values.shape)
        hrrr_lon360 = np.asarray(codes_get_array(h, "longitudes"), dtype=np.float32).reshape(hrrr_values.shape)
        codes_release(h)

    with (INTERIM / MRMS_NAME.removesuffix(".gz")).open("rb") as stream:
        m = codes_grib_new_from_file(stream)
        mmeta = {key: codes_get(m, key) for key in ["Ni", "Nj", "gridType", "dataDate", "dataTime", "iDirectionIncrementInDegrees", "jDirectionIncrementInDegrees", "latitudeOfFirstGridPointInDegrees", "longitudeOfFirstGridPointInDegrees", "iScansNegatively", "jScansPositively", "jPointsAreConsecutive", "alternativeRowScanning"]}
        mrms_values = np.asarray(codes_get_values(m), dtype=np.float32).reshape(int(mmeta["Nj"]), int(mmeta["Ni"]))
        codes_release(m)

    hrrr_lon = ((hrrr_lon360 + 180.0) % 360.0) - 180.0
    # A Georgia-centered rectangle with buffer; it includes neighboring states and is not a state mask.
    spatial = (hrrr_lat >= 29.5) & (hrrr_lat <= 35.5) & (hrrr_lon >= -86.0) & (hrrr_lon <= -80.0)
    rows, cols = np.where(spatial)
    lat = hrrr_lat[rows, cols]
    lon = hrrr_lon360[rows, cols]
    precip_fcst = hrrr_values[rows, cols]

    mrms_lat0 = float(mmeta["latitudeOfFirstGridPointInDegrees"])
    mrms_lon0 = float(mmeta["longitudeOfFirstGridPointInDegrees"])
    dlat = float(mmeta["jDirectionIncrementInDegrees"])
    dlon = float(mmeta["iDirectionIncrementInDegrees"])
    mrms_j = np.rint((mrms_lat0 - lat) / dlat).astype(np.int64)
    mrms_i = np.rint((lon - mrms_lon0) / dlon).astype(np.int64)
    inside = (mrms_j >= 0) & (mrms_j < mrms_values.shape[0]) & (mrms_i >= 0) & (mrms_i < mrms_values.shape[1])
    rows, cols, lat, lon, precip_fcst, mrms_j, mrms_i = [x[inside] for x in [rows, cols, lat, lon, precip_fcst, mrms_j, mrms_i]]
    precip_obs = mrms_values[mrms_j, mrms_i]
    valid = np.isfinite(precip_obs) & (precip_obs >= 0) & np.isfinite(precip_fcst)
    rows, cols, lat, lon, precip_fcst, mrms_j, mrms_i, precip_obs = [x[valid] for x in [rows, cols, lat, lon, precip_fcst, mrms_j, mrms_i, precip_obs]]

    # Great-circle distance from each HRRR point to the selected MRMS grid center.
    lat_m = mrms_lat0 - mrms_j * dlat
    lon_m = mrms_lon0 + mrms_i * dlon
    dlat_rad = np.deg2rad(lat - lat_m)
    dlon_rad = np.deg2rad((lon - lon_m + 180.0) % 360.0 - 180.0)
    a = np.sin(dlat_rad / 2) ** 2 + np.cos(np.deg2rad(lat)) * np.cos(np.deg2rad(lat_m)) * np.sin(dlon_rad / 2) ** 2
    distance_km = 6371.0 * 2 * np.arcsin(np.sqrt(a))

    with OUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["hrrr_i", "hrrr_j", "latitude", "longitude", "hrrr_apcp_mm_equiv", "mrms_qpe_mm", "error_obs_minus_fcst_mm", "mrms_i", "mrms_j", "nearest_center_distance_km"])
        for values in zip(cols, rows, lat, ((lon + 180) % 360) - 180, precip_fcst, precip_obs, precip_obs - precip_fcst, mrms_i, mrms_j, distance_km):
            writer.writerow([int(values[0]), int(values[1]), *(round(float(x), 5) for x in values[2:])])

    def digest(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()

    result = {
        "sample_id": "2024-05-01T13:00:00Z_HRRR_f01_vs_MRMS_01H",
        "scope": "Georgia-centered bounding box, not a state polygon",
        "bbox_degrees": {"south": 29.5, "north": 35.5, "west": -86.0, "east": -80.0},
        "forecast_grid": hmeta,
        "observation_grid": mmeta,
        "method": "nearest MRMS regular-latitude/longitude grid point for each HRRR cell center; no areal averaging or interpolation",
        "row_count": int(len(precip_obs)),
        "invalid_observation_points_dropped": int(np.count_nonzero(~valid)) if len(valid) else 0,
        "missing_sentinels_removed": "All negative MRMS values, including product missing/fill sentinels (-1/-3), were excluded.",
        "hrrr_forecast_mm_equivalent_range": [float(precip_fcst.min()), float(precip_fcst.max())],
        "mrms_mm_range": [float(precip_obs.min()), float(precip_obs.max())],
        "nearest_grid_center_distance_km": {"mean": float(distance_km.mean()), "max": float(distance_km.max())},
        "derived_file": str(OUT.relative_to(ROOT)),
        "derived_file_sha256": digest(OUT),
        "source_manifest": "data/manifests/sample_20240501_1300.json",
        "use_limit": "Alignment smoke test only; one valid time cannot support training, and nearest-neighbor values are not the final remapping choice.",
    }
    MANIFEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

