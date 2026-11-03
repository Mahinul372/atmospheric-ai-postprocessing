# Feasibility report (initial)

**Date:** 2026-11-03 (Asia/Dhaka)  
**Status:** Preliminary; local sample verification remains pending.

## Current environment evidence

- Target parent `F:\Atmospheric modeling` exists and contained only `desktop.ini` at inspection. The requested repository directory was absent, so this setup creates it without overwriting an existing project.
- Free space on F: was reported as 233.9 GB.
- Python 3.13.7 and Git 2.53.0.windows.3 are available.
- GitHub CLI (`gh`) and AWS CLI (`aws`) are not available on PATH.
- The global Python environment has NumPy, but not PyTorch, TabPFN, xarray, cfgrib/eccodes, pygrib, pandas, scipy, pyproj, boto3, or pytest.
- WMI system inventory access was denied and `nvidia-smi` is unavailable. CPU model, installed RAM, and GPU details remain unknown; do not infer their values from this failed probe.
- Git global configuration is absent (`C:/Users/Mahi/.gitconfig` not found).

## Data feasibility

Official NOAA registries describe public HRRR and MRMS S3 archives. HRRR is distributed as GRIB2 (and an additional Zarr archive is listed); MRMS includes gridded GRIB2 precipitation products. Primary candidate fields are HRRR surface APCP and MRMS `RadarOnly_QPE_01H`, but their actual accumulation windows and timestamps must be verified from sample GRIB metadata before constructing matches.

A local HTTPS listing attempt against each public S3 endpoint failed in Windows Schannel with `SEC_E_NO_CREDENTIALS` (curl) and a .NET authentication failure (PowerShell). Thus archive access is not yet confirmed from this computer, and no files were downloaded. This appears to be a local TLS/network credential issue; it must be resolved or tested through an approved transfer path before a data pipeline can be validated. No observations have been fabricated or substituted.

## TabPFN verification

Official Prior Labs sources verify that the regression API can explicitly choose `ModelVersion.V2_5`; the default TabPFN-2.5 regression checkpoint is `tabpfn-v2.5-regressor-v2.5_default.ckpt`. The model card says TabPFN-2.5 is trained purely on synthetic tabular tasks and distinguishes it from Real-TabPFN-2.5, which has continued real-data pretraining. The current official package on PyPI is 9.2.0 and declares Python >=3.10, so Python 3.13 is within its declared interpreter range. This does not yet establish that a complete Windows GRIB/geospatial stack or GPU backend installs and runs on this machine.

Primary configuration will be pinned to the exact version/checkpoint after smoke-loading succeeds. Runtime logs must record package version and resolved checkpoint identity. Do not use `pretrain=False`, fine-tune weights, or silently substitute model versions/checkpoints.

## Scientific feasibility and constraints

The project is scientifically feasible as a bounded prototype if it uses a single, verified lead/accumulation pairing and a modest Georgia subset. HRRR and MRMS use distinct grids; MRMS-to-HRRR remapping and missing-data handling must be stated. Precipitation is zero-inflated and skewed, and neighboring pixels/hours/events are dependent. Partition by whole dates/events, with test observations held out from all model and threshold decisions. TabPFN-2.5 is limited to about 50,000 rows and 2,000 features; this is not a full-state, full-resolution, multi-year gridded training design.

The initial experiment should compare raw HRRR, linear error regression, and synthetic-only default TabPFN-2.5 on identical samples. Report MAE, RMSE, bias, correlation, and event/threshold verification for heavy precipitation with thresholds chosen without test data.

## Blockers and next actions

1. Resolve local HTTPS/TLS access to anonymous NOAA S3 or establish a user-approved transfer route; then retrieve one representative HRRR and MRMS pair, not a broad archive.
2. Obtain CPU/RAM/GPU inventory through an allowed system path; current WMI inventory was denied.
3. Check TabPFN-2.5 model access/license acceptance and smoke-load the exact default regression checkpoint in an isolated environment.
4. Inspect actual GRIB metadata, coordinates, units, missing values, timestamp conventions, and accumulation periods; only then approve a matching rule and expand sample acquisition.
5. Configure Git author identity and a GitHub CLI/authenticated path. `gh` is absent; the connected GitHub repository search found no matching repository, and the connector available in this session does not expose repository creation.
6. Select a source-code license only after deciding the intended reuse terms; model weights remain under their separate license.

## Sources checked

- [NOAA HRRR Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/)
- [NOAA MRMS Open Data Registry](https://registry.opendata.aws/noaa-mrms-pds/)
- [MRMS operational product table](https://www.nssl.noaa.gov/projects/mrms/operational/tables.php)
- [Official TabPFN regressor API](https://github.com/PriorLabs/TabPFN/blob/main/src/tabpfn/regressor.py)
- [Official TabPFN checkpoint loader](https://github.com/PriorLabs/TabPFN/blob/main/src/tabpfn/model_loading.py)
- [Official TabPFN-2.5 model card](https://huggingface.co/Prior-Labs/tabpfn_2_5)
- [Official TabPFN package on PyPI](https://pypi.org/project/tabpfn/)
- [TabPFN-2.5 license](https://huggingface.co/Prior-Labs/tabpfn_2_5/blob/main/LICENSE)

## 2026-11-03 actual sample verification addendum

The initial shell request used Windows Schannel and failed, but Python's standard HTTPS client successfully accessed the anonymous NOAA S3 endpoints. A single real pair was downloaded and inspected; no synthetic or substituted data were used.

### Files and exact matching

- HRRR object: `hrrr.20240501/conus/hrrr.t12z.wrfsfcf01.grib2`; its `.idx` identifies APCP surface accumulation at bytes 59,755,654–60,073,889 inclusive. The extracted message is 318,236 bytes. GRIB metadata reports initialization 2024-05-01 12:00 UTC, valid time 13:00 UTC, `stepType=accum`, `stepRange=0-1`, `Total Precipitation`, and units kg m-2.
- MRMS object: `CONUS/RadarOnly_QPE_01H_00.00/20240501/MRMS_RadarOnly_QPE_01H_00.00_20240501-130000.grib2.gz`; compressed size 555,574 bytes. The GRIB parameter identifiers are discipline/category/number 209/6/2, with timestamp 13:00 UTC. NOAA identifies this as one-hour radar precipitation accumulation; WDTD training describes the one-hour value as the sum over the previous 60 minutes. Therefore the sample’s observation window is 12:00–13:00 UTC, exactly matching HRRR f01’s 0–1-hour window. This period interpretation is supported by NOAA product documentation, not just filename coincidence. See the [official MRMS product table](https://www.nssl.noaa.gov/projects/mrms/operational/tables.php) and [NOAA WDTD explanation of the previous-60-minute accumulation](https://training.weather.gov/wdtd/courses/rac/documentation/rac24-mrms.pdf).
- A reproducible manifest with source paths, index byte range, hashes, metadata, and checks is at `data/manifests/sample_20240501_1300.json`.

### Actual grids and data quality

- HRRR message grid: Lambert conformal, 1799 x 1059 points, 3,000 m spacing. Its whole-CONUS sample APCP values range from 0 to about 32.899 kg m-2 (mm equivalent).
- MRMS grid: regular latitude/longitude, 7000 x 3500 points, 0.01-degree spacing (about 1 km). The official product units are mm. Its full CONUS decoded sample includes the -3 fill value in 8,261,972 of 24,500,000 cells; negative product sentinels were excluded in the Georgia-centered subset. In the approximate 29.5–35.5N, 86–80W bounding box, the selected MRMS sample points were valid for all 42,184 HRRR centers checked.
- The initial mapping script writes `data/interim/sample/ga_bbox_nearest_neighbor_20240501_1300.csv` and `data/manifests/sample_spatial_match.json`. It uses the nearest MRMS cell center for each HRRR center, with mean/max center separation about 0.393/0.731 km. The rectangle includes adjacent states and is not a Georgia polygon. Nearest-neighbor is only a data-alignment smoke test; choose and validate the final remapping method before scientific evaluation. No full spatial interpolation has been claimed.

### Environment implications

- Python reports 4 logical CPUs and Windows `GlobalMemoryStatusEx` reports 3.4 GB total RAM / about 0.7 GB available at inspection. F: has 233.9 GB free. `nvidia-smi` is not installed and no display adapter was returned by the available probe; GPU availability is unconfirmed, so do not assume acceleration.
- An isolated `.venv` now contains NumPy 2.3.3 and ecCodes 2.50.0 on Python 3.13.7. The actual GRIBs decoded and validation ran successfully. This avoids loading the full national fields through xarray for the sample inspection.
- TabPFN 9.2.0 declares Python >=3.10 and therefore permits this Python version. Its API can explicitly choose V2_5, whose default regression filename is the synthetic-only checkpoint. However, the TabPFN/PyTorch stack and weights have not been installed or loaded. Given 3.4 GB total RAM and no confirmed GPU, a full 42,184-row training fit is not a viable assumption; official guidance limits older TabPFN versions to modest CPU datasets (around 1,000 samples) and warns CPU is slow. The primary model remains TabPFN-2.5; do not switch models silently. A small CPU smoke test will be considered only after verifying available memory and accepting the model license.

### Validation run

`src/sample_validation.py` passed all five sample assertions: HRRR surface total precipitation, one-hour forecast accumulation, MRMS product identifier, equal 12–13 UTC periods, and metadata/value-count consistency. `src/match_sample.py` generated the nearest-neighbor smoke-test table and manifest. `python -m unittest discover -s tests -v` passed four period-alignment tests.

This one date/time demonstrates archive access, data decoding, exact temporal matching, and bounded spatial sampling. It does not establish model skill or provide enough independent events for research conclusions.

### Multi-time storm-event availability check

The acquisition and validation scripts were also run for two additional HRRR/MRMS pairs during the 2024-09-27 Helene event. Both independently decoded and matched: HRRR 00Z f01 to MRMS 01Z (00–01Z window), and HRRR 12Z f01 to MRMS 13Z (12–13Z window). The full-CONUS MRMS grids decode with about 8.26 million negative fill/missing cells; the approximate Georgia-centered rectangle had all 42,184 nearest-mapped locations valid at both times. QC-only precipitation diagnostics in that rectangle showed MRMS wet fractions of about 93% and 29% and maxima of 46.4 mm and 127.3 mm for the two selected hours. These are sample-content checks only, not verification scores or model results.

Reusable acquisition and GRIB validation code is in `src/download_pair.py` and `src/validate_pairs.py`; each event pair has an independent manifest in `data/manifests/pair_*.json`. The two additional raw forecast message extracts total less than 1 MB; the compressed MRMS files total about 2.1 MB. All raw and interim data remain excluded from Git.
