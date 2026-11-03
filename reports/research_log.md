# Research log

## 2026-11-03 — Milestone 1 started

- **Completed:** Read the project instructions; checked the target location before creation; verified `F:\Atmospheric modeling` exists and contained only `desktop.ini`; confirmed the repository folder was absent; created the repository scaffold and this log.
- **Environment:** Python 3.13.7, Git 2.53.0.windows.3, F: free space 233.9 GB. `gh` and AWS CLI are absent. Global Python has NumPy only among the requested science/ML stack. Git global identity config is absent. WMI inventory was denied; `nvidia-smi` unavailable; CPU/RAM/GPU remain unknown.
- **Data verification:** Official NOAA HRRR and MRMS public archives and product documentation reviewed. Local HTTPS S3 listing failed: Schannel `SEC_E_NO_CREDENTIALS`; no files downloaded. Actual files, grids, and temporal accumulation match remain unverified.
- **Model verification:** Official API supports explicit TabPFN-2.5 regression selection via `ModelVersion.V2_5`. The expected primary checkpoint is `tabpfn-v2.5-regressor-v2.5_default.ckpt`, identified in official source as the default regression checkpoint. The model card labels TabPFN-2.5 synthetic-task-pretrained and distinguishes Real-TabPFN-2.5. Current official PyPI release checked as 9.2.0; Python >=3.10 declared.
- **Scientific design decisions:** Primary task remains HRRR error regression against MRMS hourly QPE. Raw HRRR, linear regression, and TabPFN-2.5 are planned comparisons. Hold out whole dates/events before any model selection; test observations only for final evaluation. Exact lead, accumulation interval, grid mapping, thresholds, and spatial subset await inspection of real files.
- **Files:** `README.md`, `reports/feasibility_report.md`, `reports/research_log.md`, `configs/config.yaml`, `.gitignore`, `pyproject.toml`, `requirements.txt`; data/result directories initialized.
- **Outstanding:** NOAA sample access and GRIB inspection; hardware inventory; isolated dependency/model smoke test; choose GitHub auth/tool path and configure Git identity; decide source-code license.
- **Next action:** Resolve local TLS credentials or establish an approved access route, then fetch only one sample pair and verify time windows, variables, grid metadata, and bytes before expanding.

## Experiment ledger

No model experiments or performance results have been produced.

## 2026-11-03 — Real sample and matching smoke test

- **Completed:** Used Python HTTPS after Windows Schannel could not negotiate the request. Listed and downloaded one HRRR APCP byte range (from `.idx`) and one MRMS `RadarOnly_QPE_01H` object. Decompressed MRMS in the ignored interim area and decoded both with ecCodes 2.50.0.
- **Verified temporal alignment:** HRRR 2024-05-01 12Z f01 APCP is 0–1 hour, valid 13Z. MRMS `RadarOnly_QPE_01H` file at 13Z represents the previous 60 minutes per NOAA WDTD material. Both cover 12–13Z.
- **Verified spatial metadata:** HRRR Lambert 1799x1059 at 3 km; MRMS regular lat/lon 7000x3500 at 0.01 degrees. A 29.5–35.5N, 86–80W rectangular smoke-test mapping produced 42,184 paired cell centers with nearest-MRMS-center matching, mean/max separation 0.393/0.731 km. This is not a GA state polygon or final remapping approach.
- **Observed QC:** Full MRMS sample contains -3 fill values; negative values are excluded. The bounding-box samples were valid in this time. The one sample period is low intensity and cannot support skill claims.
- **Files added:** `src/sample_validation.py`, `src/match_sample.py`, `src/__init__.py`, `tests/test_sample_metadata.py`, `data/manifests/sample_20240501_1300.json`, `data/manifests/sample_spatial_match.json`; intermediate CSV and decompressed GRIB are ignored by Git.
- **Dependencies:** Created project `.venv`; installed NumPy 2.3.3, ecCodes 2.50.0 plus ecCodes Python dependencies. Full `tabpfn`/PyTorch stack not installed; runtime checkpoint not loaded. Python is 3.13.7. Current system probe: 4 logical CPUs, 3.4 GB RAM total, about 0.7 GB available, no `nvidia-smi`; GPU remains unconfirmed.
- **Verification:** Sample validation passed five metadata/content checks. `python -m unittest discover -s tests -v` passed 4 tests. No model was fit and no performance result was generated.
- **GitHub:** `gh` absent; no global Git identity. Connected repository search found no repository with the requested name. Local Git initialized on `main`; no commit/push yet because identity and authenticated repository-creation path are not available in this environment.
- **Next:** Decide exact geographic polygon and final area remapping after inspecting broader samples; verify more dates/events and product availability. Assess model license acceptance and realistic CPU feasibility before installing/loading TabPFN. Establish private GitHub creation/auth path without requesting credentials in chat.

## 2026-11-03 — Second-date/event data checks

- **Completed:** Added `src/download_pair.py` for index-guided HRRR APCP range retrieval and matching MRMS one-hour file retrieval; added `src/validate_pairs.py` for GRIB metadata, time window, product-ID, and decoded-grid-count assertions.
- **Data:** Retrieved real 2024-09-27 HRRR f01/MRMS pairs at 00–01Z and 12–13Z. Both passed all six metadata/content checks. In a Georgia-centered bbox smoke check, all 42,184 selected MRMS locations were valid; MRMS wet fractions and maxima differed substantially between times, showing actual weather variability. These are QC summaries only, not skill results.
- **Manifests:** `data/manifests/pair_20240927_00z.json` and `data/manifests/pair_20240927_12z.json` include source keys, range byte offsets, hashes, decoded metadata, periods, and check results.
- **Next:** Extend validation to a modest multi-event sample, define a Georgia polygon and final spatial aggregation/remapping, and design date/event-level partitions before making an analysis dataset. CPU/RAM and license acceptance remain prerequisites to a TabPFN smoke load.


## 2026-11-03 — Repository publication

- **Repository:** Confirmed `Mahinul372/atmospheric-ai-postprocessing` exists on GitHub and is public, as the user requested.
- **Published:** The remote main branch now contains the project README, `.gitignore`, configuration, requirements, feasibility and research logs, four real-data manifests, validation/download/matching utilities, and existing tests. Remote tree verification found no raw or interim weather files, processed arrays, checkpoints, virtual environment, or result artifacts.
- **Local Git blocker:** The F: checkout has no commit or remote configured. Git read-only inspection works when using a per-command `safe.directory`, but `git add --dry-run` fails to create `.git/index.lock` with `Permission denied` because the checkout is owned by a different Windows sandbox identity. Local Git history synchronization remains pending resolution of that ACL/ownership mismatch.
- **Scientific state:** No model has been fit, no test data has been used for model selection, and no skill score or claimed improvement exists.


## 2026-11-03 — Validation suite and official model-card recheck

- **Tests:** Ran the existing metadata-only unit suite with the local project Python 3.13 environment: all 4 tests passed. These test accumulation-window logic; they do not measure forecast skill.
- **TabPFN documentation:** Rechecked the official Prior Labs API and TabPFN-2.5 model card. The explicit version API remains `TabPFNRegressor.create_default_for_version(ModelVersion.V2_5)`. The model card confirms the default regression checkpoint `tabpfn-v2.5-regressor-v2.5_default.ckpt` is trained on synthetic data only, while separate `real` regression checkpoints use real-data fine-tuning. It describes TabPFN as an in-context-learning tabular transformer with intended support up to 50,000 samples and 2,000 features.
- **License:** The current model card identifies `tabpfn-2.5-license-v1.1`; it allows research/testing and limited internal evaluation but prohibits commercial or production use. No license acceptance or checkpoint download was performed.
- **Next:** Resolve the local F: checkout write ACL; choose and validate the final MRMS-to-HRRR remapping using actual grid coordinates; define whole-event train/validation/test partitions; then expand the real sample across multiple independent precipitation events. Do not begin model fitting before these steps.


## 2026-11-03 — Candidate event sampling plan

- **Completed:** Added `reports/event_sampling_plan.md` with NWS-documented Debby, Helene, and Idalia windows as archive-check candidates plus season-balanced background sampling. This is a procurement plan only; it does not create a final split or use model scores to select cases.
- **Leakage safeguard:** The 2024-09-27 Helene pairs have already been inspected for technical time/grid/QC checks, so the proposed policy excludes that event from a strictly untouched final test. The previous 2024-05-01 sample is also development/QC only. Freeze test dates/events before examining their MRMS values for modeling.
- **Sources:** NOAA NWS Atlanta documented widespread heavy rainfall during Helene (September 24–27, 2024); NWS Charleston documented multi-day Debby rainfall in southeast Georgia (August 4–9, 2024) and Idalia impacts in southeast Georgia (August 2023). These event summaries inform the archive search, not a performance claim.
- **Next:** Confirm HRRR/MRMS archive availability for short Debby and Idalia windows and a seeded background calendar sample; then fetch and validate the pairs before expanding the area or fitting a model.
