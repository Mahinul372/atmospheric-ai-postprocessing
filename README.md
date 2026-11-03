# TabPFN-Based Post-Processing of Numerical Weather Predictions

Independent research prototype investigating whether pretrained TabPFN-2.5 regression can correct hourly HRRR precipitation forecasts against NOAA MRMS observations over Georgia, USA.

## Research question

Does a synthetic-only pretrained TabPFN-2.5 regression checkpoint improve HRRR hourly precipitation accuracy through forecast-error correction, compared with raw HRRR and a linear regression correction, when tested on held-out dates or weather events?

This project post-processes an existing operational numerical weather prediction system. It does not generate atmospheric forecasts or claim to model atmospheric dynamics.

## Current status

**Milestone 2 — data validation and matching.** Three real HRRR/MRMS one-hour sample pairs have been downloaded and checked: one 2024-05-01 pair and two 2024-09-27 pairs. The checks confirm HRRR APCP surface accumulation for 0–1 h, matching the MRMS `RadarOnly_QPE_01H` valid-time product for the same preceding hour. A Georgia-centered rectangular area and nearest-center matching have only been used as smoke checks; a state boundary and final remapping method are still pending.

No model has been fit. No forecast skill result or performance improvement has been established. TabPFN has not yet been installed or loaded.

## Data and matching

- **Forecasts:** NOAA HRRR historical GRIB2 files from the [HRRR public archive](https://registry.opendata.aws/noaa-hrrr-pds/). The checked field is surface APCP, extracted using the HRRR index file and byte ranges.
- **Observations:** NOAA MRMS `RadarOnly_QPE_01H` GRIB2 data distributed as gzip-compressed objects in the [MRMS archive](https://www.nssl.noaa.gov/projects/mrms/).
- **Initial pairing:** HRRR forecast initialization time plus one-hour lead is matched to MRMS valid time. The intended hourly interval is the preceding hour. Each pair must pass time-window, product, units/metadata, and grid checks before analysis.
- **Spatial processing:** HRRR is a 3-km Lambert conformal grid (1799 × 1059 in the checked files); MRMS is a 0.01-degree regular latitude/longitude grid (7000 × 3500 in the checked files). The final mapping onto the analysis grid remains to be selected and documented. Nearest-center matching is currently validation-only.
- **Data storage:** Raw and interim weather files, processed datasets, model checkpoints, and result artifacts should remain local and are excluded from Git. Manifests record public source keys, timestamps, byte ranges, hashes, and validation metadata.

The observations are verification targets. No future MRMS information may enter forecast-time predictors.

## Planned experiment

The target is forecast error:

`error = MRMS hourly precipitation - HRRR hourly precipitation`

The corrected estimate is:

`corrected precipitation = HRRR precipitation + predicted error`

Apply a nonnegative constraint if justified and documented. Compare raw HRRR, linear regression correction, and the specified TabPFN-2.5 regression model. Split by whole dates or weather events before fitting or model selection; reserve test observations for final evaluation only. Report performance by lead time, precipitation intensity, event, and spatial area where sample size permits.

## TabPFN configuration requirement

The primary AI model is the pretrained **TabPFN-2.5 regression** model, explicitly selected with `TabPFNRegressor.create_default_for_version(ModelVersion.V2_5)`. The intended checkpoint is the synthetic-only default regression checkpoint `tabpfn-v2.5-regressor-v2.5_default.ckpt`. The model uses training examples as task-specific in-context information at prediction time; this experiment does not fine-tune transformer weights or train the transformer from scratch. No real-data-finetuned checkpoint is allowed in the primary experiment.

Before inference, verify the official API and the exact checkpoint loaded, pin compatible versions, record the runtime configuration, and comply with the model's license. The official model card identifies TabPFN-2.5 weights as licensed under `tabpfn-2.5-license-v1.1`; it permits research/testing and limited internal evaluation but prohibits commercial or production use. The license has not been accepted through the project environment. The project's current machine has 4 logical CPUs and approximately 3.4 GB total RAM; practical inference capacity is not yet established.

## Scientific safeguards and limitations

- Keep all held-out dates/events out of training, feature selection, preprocessing decisions, and model selection.
- Align precipitation accumulation intervals explicitly; a matching valid timestamp alone is insufficient.
- Do not treat reanalysis as an operational forecast.
- Exclude MRMS fill values and document quality-control masks.
- Document any spatial interpolation or remapping; do not interpret smoke-test nearest-neighbor pairs as final scientific data.
- Evaluate precipitation occurrence and amount with suitable metrics, including thresholded categorical scores and continuous error metrics. Heavy-rain conclusions require enough independent events.
- Report inconclusive or negative findings honestly.

## Repository structure

The repository contains the validation/download utilities, configuration, manifests, tests, and feasibility/research notes. The proposed leakage-safe grid/time protocol is in [reports/spatiotemporal_validation_protocol.md](reports/spatiotemporal_validation_protocol.md); its remapping and split choices remain proposals pending validation on actual grids. Weather data and model artifacts must not be committed.

## Official model references

- [Prior Labs TabPFN repository](https://github.com/PriorLabs/TabPFN)
- [TabPFN-2.5 model card](https://huggingface.co/Prior-Labs/tabpfn_2_5)
- [TabPFN-2.5 paper](https://arxiv.org/abs/2511.08667)

## Reproducibility

The local environment and exact commands are being documented alongside the data manifest and validation code. Until the source tree is synchronized to this public repository and the required licensed checkpoint has been verified at runtime, this page describes a preliminary project status, not a completed, reproducible model experiment.
