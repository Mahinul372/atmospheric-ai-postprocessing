# Candidate event sampling plan

**Status: procurement plan, not an experiment split.** No new MRMS observations have been fetched or inspected for the candidate dates below. The previously checked 2024-05-01 and 2024-09-27 pairs remain technical development/QC samples and should not be presented as blind-test results.

## Why use event and background samples

The main experiment needs both ordinary precipitation regimes and challenging heavy-rain events. Training and evaluation on only tropical-cyclone dates would distort precipitation frequency and would not support a statewide operational-skill claim. Conversely, a randomly chosen short period may contain too few heavy-rain cases to evaluate those errors. Keep event-stratified diagnostics separate from any date-weighted overall score, and record the sampling frame.

## Publicly documented candidate event windows

These are candidates for data availability and validation checks, not a final train/validation/test assignment:

- **Tropical Storm Debby, 2024-08-04 to 2024-08-09:** NWS Charleston documents prolonged heavy rain and flooding over southeast Georgia, with multi-day storm-total reports. Candidate windows to inspect include August 5–7, but acquire a buffer around the full event. [NWS Charleston event summary](https://www.weather.gov/chs/debby2024rainfall)
- **Hurricane Helene, 2024-09-24 to 2024-09-27:** NWS Atlanta documents widespread heavy rainfall and flooding across Georgia. The 2024-09-27 hourly pairs in this repository have already been read for technical grid/time/QC checks; retain these as development/QC only, not as a blind final-test event. [NWS Atlanta September 2024 climate summary](https://www.weather.gov/ffc/September2024climatesummary)
- **Hurricane Idalia, 2023-08-30 onward:** NWS Charleston notes heavy rain and flooding over inland southeast Georgia. The exact Georgia event window and hourly HRRR/MRMS archive coverage still require verification. [NWS Charleston tropical-cyclone history](https://www.weather.gov/chs/TChistory)

These examples were selected from NWS event documentation, not from model performance. They cover tropical rainfall cases and do not represent the full precipitation climatology.

## Initial small expansion

1. Keep the existing May 1 sample and September 27 Helene samples tagged as development/technical-QC cases.
2. Verify archive coverage and exact precipitation accumulation metadata for short windows in Debby and Idalia before downloading the full event windows.
3. Add a seeded, season-balanced sample of non-event calendar dates from multiple years. Select calendar dates without examining MRMS values, then fetch matching HRRR f01/MRMS 01H pairs.
4. Include every hourly initialization within each selected date/window only if storage and process time permit. Keep the window/event as the split unit; never randomly split rows or grid cells.
5. Start with modest windows and retain only the Georgia-domain arrays after spatial processing. The source files are small GRIB message ranges for HRRR plus compressed MRMS products, but total volume depends on the number of hours and years.

## Split policy

Do not finalize the held-out test event list from MRMS outcomes or model scores. First freeze a dated case inventory using archive availability and external event calendars. Assign complete event windows or calendar blocks to development, validation, and test before model fitting. Put buffers around partition boundaries so adjacent one-hour windows and a storm crossing midnight cannot straddle partitions.

The 2024-09-27 Helene pairs have already been inspected for technical metadata and precipitation QC, so exclude that event from a strictly untouched test set. For the final test, choose one or more later, separately held-out events/date blocks before reading their MRMS values for analysis; read them only for the final evaluation after all model/mapping choices are frozen. If no enough independent events remain, report a pilot study and do not claim event-generalization.

## Interpretation

Report at least two views: (1) overall metrics on a date/event-representative sample, with the sampling weights stated, and (2) event-stratified metrics for the predeclared tropical/heavy-rain cases. Do not let the event oversample silently change the meaning of the overall score. Keep heavy-precipitation thresholds fixed in advance from a published convention or training data only, never optimized on test observations.
