# Spatiotemporal validation protocol (proposed)

**Status: design proposal only.** The validated nearest-center code is a smoke test. This protocol does not declare the final production remapping, define final precipitation thresholds, or create train/validation/test partitions.

## Case definition and hourly time matching

Treat each forecast case as the tuple (initialization_UTC, forecast_lead, accumulation_start_UTC, accumulation_end_UTC). For this first experiment, restrict to HRRR surface APCP for f01 and MRMS RadarOnly_QPE_01H with the same one-hour window. Decode and record each GRIB message's reference time, valid time, step range, units, product identifier, and missing-value convention. Require exact agreement of the accumulation start/end, not just equal valid timestamps. Preserve all timestamps in UTC.

The checked 2024-05-01 case is HRRR initialized 12Z, f01 ending 13Z, paired with the MRMS one-hour product at 13Z. The two 2024-09-27 cases are likewise f01 one-hour windows. These are metadata validation cases, not an evaluation sample.

## Spatial alignment options

The checked grids are not coincident: HRRR uses a regular 3-km Lambert conformal grid and MRMS uses a 0.01-degree regular latitude/longitude grid. The current nearest-MRMS-center mapping is acceptable only as a low-cost smoke check.

Evaluate these choices on the same real cases:

1. **Nearest MRMS center:** simple reference mapping; preserves individual MRMS values but may misrepresent a 3-km HRRR footprint and can be sensitive to storm displacement.
2. **Bilinear interpolation to HRRR centers:** smooths fine-scale QPE and is not conservative.
3. **Area-weighted aggregation over HRRR cell footprints:** preferred candidate for the main grid-to-grid verification because the observation's finer cells are aggregated to the forecast support. Build target cell footprints from the decoded HRRR projection/spacing; transform MRMS pixel footprints to that projection; omit invalid MRMS values and track the valid-area fraction. Select a minimum-coverage rule before model evaluation and report sensitivity to that rule.

Before adopting option 3, verify the grid origin, cell-center convention, earth shape, projection parameters, and cell edges from the actual GRIB metadata. Compare the three mappings around intense and displaced precipitation structures. Record mapping differences and edge effects. Do not tune the mapping to maximize TabPFN performance.

Keep Georgia state-mask selection separate from grid remapping. Use an authoritative state boundary (for example, a Census TIGER/Line Georgia boundary), intersect it with HRRR cells, and document whether boundary cells are center-in-state or fractionally included. Retain the existing rectangular bbox only for inexpensive smoke checks.

## Quality control and target interpretation

- Convert HRRR APCP and MRMS QPE to millimeters of liquid-water-equivalent depth only after verifying the decoded units and accumulation periods.
- Treat MRMS as an observational reference estimate, not error-free ground truth. RadarOnly_QPE_01H is radar-only; its error characteristics differ from multi-sensor/gauge-adjusted QPE.
- Mask the product's documented invalid/fill codes before interpolation. Track the valid MRMS area fraction per target cell; never convert sentinel values into precipitation.
- Preserve the raw HRRR and raw MRMS values and quality masks alongside the remapped fields.
- The correction target remains MRMS - HRRR; corrected amount is HRRR + predicted_error, optionally clipped at zero under a predeclared rule.

## Leakage-resistant split

Create the split table before generating model rows. Keep complete UTC dates, forecast initializations, and weather-event windows in exactly one partition. For event holdouts, keep a multi-hour storm sequence together across UTC midnight and apply a time buffer so adjacent forecast/observation windows cannot straddle partitions. Freeze the test event/date list before feature selection or hyperparameter/model selection.

Fit any missing-value handling, standardization, filtering thresholds, sample selection, and feature decisions on training data only. Use validation events for choices. Do not expose test observations to TabPFN's fit context, linear-regression fitting, threshold selection, or method choice. TabPFN's pretrained weights remain frozen: its fit(X_train, y_train) supplies task examples as in-context information; it is not transformer fine-tuning.

Randomly assigning grid cells or times to train and test is prohibited because neighboring pixels and adjacent periods are strongly dependent. Report how many distinct events, dates, initializations, and wet/heavy-rain cases occur in each partition. If the available sample cannot fill each partition with independent events, call the result a pilot rather than a generalization study.

## Feature and resource scope

For a controlled first study, begin with only forecast-time features: HRRR APCP, lead time (if more than f01 is added), initialization-cycle/time encodings, and optional HRRR forecast fields available at the same valid time. Use the same features for linear regression and TabPFN. Do not use MRMS-derived predictors or future observations. Add location/climatological predictors only as a documented secondary experiment.

TabPFN-2.5 documents intended use up to 50,000 rows and 2,000 features, but these are model limits, not a promise that a 3.4-GB-RAM CPU can process that size. Keep each fit context substantially below the ceiling; measure peak RAM/time on a small real training partition before scaling. Any event/block subsampling rule must be fixed from training data and recorded.

## References

- [NOAA HRRR open-data record](https://registry.opendata.aws/noaa-hrrr-pds/)
- [NCEP HRRR 3-km Lambert grid specification](https://www.emc.ncep.noaa.gov/mmb/namgrids/hrrrspecs.html)
- [NOAA MRMS operational product table](https://www.nssl.noaa.gov/projects/mrms/operational/tables.php)
- [NOAA MRMS data access](https://www.nssl.noaa.gov/projects/mrms/MRMS_data.php)
- [TabPFN-2.5 official model card](https://huggingface.co/Prior-Labs/tabpfn_2_5)
- [Prior Labs TabPFN implementation](https://github.com/PriorLabs/TabPFN)
