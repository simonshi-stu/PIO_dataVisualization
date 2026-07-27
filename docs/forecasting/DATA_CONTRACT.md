# Forecasting Data Contract

Version: `1.1.0`  
As of: `2026-07-27`  
Current operational cutoff: `2026-07-22`

## Purpose

This contract defines which workbook sheets and fields may drive Data Workspace, EDA, Forecast Center, AI Analyst, Anomaly Center, backtests, and Executive Summary outputs.

It prevents:

- treating lookup/calendar sheets as sales facts;
- evaluating different models on different sources or folds;
- mixing PIO installation quantity with vehicle Wholesale/Fleet volume;
- using reference forecasts as actual labels;
- leaking future information into historical backtests.

## Source snapshots

### Current governed source

| Item | Value |
|---|---|
| Local path | `C:\Users\Lenovo\Desktop\PIO\CapStone_Sales_Data_0722+PLC.xlsx` |
| SHA-256 | `f44048f30632e6f1d77d5336d2d313b4855e9d1cec95577b4a50f1c8f33c2c47` |
| PIO rows | 478,125 |
| PIO minimum date | 2023-01-01 |
| PIO maximum date | 2026-07-22 |
| Latest complete month for pre-month training | 2026-06 |
| Current partial month | 2026-07 MTD through day 22 |

### Reference forecast source

| Item | Value |
|---|---|
| Reference output | `C:\Users\Lenovo\Desktop\PIO\PIO_Forecast_Output_20260715_v2.xlsx` |
| Declared source | `data/raw/CapStone_Sales_Data_0716.xlsx` |
| Declared source SHA-256 | `cec39f4f681f084b07f0fcc4503bf2293184eb211a58083002a599c9d882f19a` |
| Declared PIO rows | 475,178 |
| Actual data through | 2026-07-15 |
| Completed training through | 2026-06-30 |

The reference output and current source do not share the same source hash or partial-month cutoff. Reproduction results must distinguish:

1. formula/contract reproduction;
2. exact source-snapshot reproduction;
3. application of the reference contract to the current 7/22 source.

## Sheet classification

| Sheet | Type | Governed role | Forecast target? | EDA role |
|---|---|---|---|---|
| `PIO_Sales_Data` | Fact | PIO accessory transactions/aggregates | Yes: Revenue and PIO Quantity | Primary PIO EDA |
| `Vehicle_Wholesale_Data` | Driver/fact | Current vehicle Dealer/non-Fleet Wholesale and possible future plan columns | Yes: Wholesale Quantity; driver for cross-checks | Relationship/driver EDA |
| `2023 Vehicle Wholesale` | Driver/fact | Historical 2023 vehicle Wholesale | Yes, through combined Wholesale history | Relationship/driver EDA |
| `2024 Vehicle Wholesale` | Driver/fact | Historical 2024 vehicle Wholesale | Yes, through combined Wholesale history | Relationship/driver EDA |
| `Working_Days` | Reference/driver | Monthly working-day calendar | No | Reference-only message |
| `PLC_Legend` | Reference/dimension | Part-description to PLC lookup | No | Reference-only message |

`PLC_Legend` and `Working_Days` must never be interpreted as ordinary PIO facts for KPI totals, rankings, anomaly detection, or forecast targets.

## Canonical fields

### `PIO_Sales_Data`

Observed shape: 478,125 rows, 12 columns.

| Business role | Canonical field | Rules |
|---|---|---|
| Invoice/event date | `PIS_MST_IVC_DT` / parsed `Deliminated Date` | Use parsed real date; preserve daily cutoff for MTD |
| Source brand code | `PIS_CMP_KND` | Raw source only; not the final anchor |
| Model code | `PIS_SERI` | Supporting mapping key; not reliable alone |
| Model year | `PIS_MDL_YY` | Treat as category/year, not an event date |
| Model name | `Model` | Normalize for HMA/GMA/KUS and lifecycle mapping |
| Part number | `PIS_PNO` | Exact-part identifier |
| Part description | `Part Description` | Description/dimension, not a stable part key |
| PLC | `PLC` | Governed 21-category level after lookup/cleaning |
| PIO installation quantity | `SumOfPIS_INST_QT` | PIO accessory units; clamp negative values to zero |
| PIO revenue | `SumOfPIS_CRP_CFM_PRI` | Accessory revenue; clamp negative values to zero |
| Source month | `YYYYMM` | Supporting monthly key; event date remains canonical for cutoff |

`Raw Quantity` in Forecast Center means aggregated `SumOfPIS_INST_QT`. It is not vehicle Wholesale, Fleet volume, or unique vehicles.

### `Vehicle_Wholesale_Data`

Observed shape: 115 rows.

Fields include:

- `Brand`
- `Model`
- `Model Code`
- `Jan` through `Dec`
- `Jan (2)` through `Dec (2)`
- corresponding total columns

The duplicated month blocks must be mapped using workbook/year/channel context before aggregation. Do not sum two blocks merely because both are present.

### `2023 Vehicle Wholesale`

Observed shape: 117 rows.

Fields:

- `Brand`
- `Model`
- January through December
- `Total`

### `2024 Vehicle Wholesale`

Observed shape: 60 rows with the same wide-month structure as the 2023 sheet.

### `Working_Days`

Observed shape: 72 rows covering 2021-01 through 2026-12.

Fields:

- `YYYY`
- `Month`
- `# of Working Days`

Working Days represent the business calendar supplied by the workbook, not calendar-day counts. They may reflect weekdays and business closures, which is why a month does not equal 30 or 31 working days.

Allowed uses:

- daily-rate normalization;
- Working-Day-Adjusted Seasonal model;
- MTD completion/nowcast context;
- future-month exogenous calendar feature.

Not allowed:

- treating days as sales quantity;
- using future actual PIO/Wholesale observations;
- forcing a manual multiplier when the selected model already learns a working-day coefficient unless explicitly modeled and backtested.

### `PLC_Legend`

Observed shape: 73 rows.

Fields:

- `Part Description`
- `PLC`

The sheet is a lookup/reference table. The current planning hierarchy expects 21 governed PLC categories, but the lookup sheet may contain repeated descriptions or aliases.

## Governed brand mapping

Final anchors:

- `HMA`
- `GMA`
- `KUS`

Rules:

1. Resolve by normalized model identity and governed mappings before falling back to source brand code.
2. Separate Hyundai and Genesis even when raw source code is `H`.
3. Raw `K` maps to KUS only as a fallback when the model cannot be matched exactly.
4. Keep named IONIQ/EV/HEV/PHEV variants separate unless a reviewed map says otherwise.
5. Record every fallback and expose it as a business-validation warning.

## Metric definitions

| Metric | Actual source | Unit | Official statistical anchor |
|---|---|---|---|
| PIO Revenue | `SumOfPIS_CRP_CFM_PRI` | USD | HMA/GMA/KUS Brand |
| PIO Quantity | `SumOfPIS_INST_QT` | accessory units | Reference method: total anchor; current method: HMA/GMA/KUS |
| Wholesale Quantity | combined Wholesale sheets | vehicles | HMA/GMA/KUS Brand, then Model |
| Expected Unit Revenue | prior realized PIO revenue / PIO quantity at the governed fallback level | USD per accessory unit | Not an independent total anchor |
| PNVW | PIO revenue / non-Fleet Wholesale vehicles | USD per Wholesale vehicle | Cross-check/driver, not automatically the official revenue forecast |
| Accessory units per vehicle | PIO quantity / non-Fleet Wholesale vehicles | accessory units per Wholesale vehicle | Ratio, not an installation percentage |

PIO Revenue represents accessory revenue associated with PIO parts. It is not vehicle sales revenue or vehicle gross profit.

## Hierarchy and reconciliation

### Reference revenue hierarchy

1. Forecast HMA/GMA/KUS Brand revenue.
2. Forecast/reconstruct child quantity.
3. Estimate leakage-safe Expected Unit Revenue.
4. Compute raw child revenue signal:

   `Raw Child Revenue = Child Quantity x Expected Unit Revenue`

5. Allocate within Brand-month:

   `Official Child Revenue = Official Brand Revenue x Raw Child Revenue / Sum(Raw Child Revenue)`

6. Reconcile:

   `PIS_PNO -> PLC/Model -> Brand -> Official Total`

Reconciliation proves arithmetic consistency. It does not prove that the child allocation is accurate.

### Reference quantity hierarchy

1. Forecast aggregate regular total with additive ETS.
2. Calculate raw Model signals using rolling six completed months.
3. Calculate one monthly reconciliation factor.
4. Scale Model signals to the aggregate total.
5. Allocate to exact parts using prior leakage-safe shares and governed fallbacks.
6. Add the separately governed Kia Fleet Carpet Floor Mat adjustment exactly once, if and only if the approved rule is enabled.

### Wholesale hierarchy

Wholesale supports Brand and Model. It has no PLC or PIS_PNO hierarchy.

## Lifecycle and sparse-series policy

- Clamp `-1` and other negative business values to zero before modeling.
- Exclude models with no positive activity in the current forecast year once at least six months of that year are observed.
- Exclude explicitly discontinued series from regular forecasts.
- Route new/reintroduced/limited-history series to a documented proxy or planner-review residual.
- Apply the configured minimum monthly-volume and active-month thresholds.
- Never silently drop excluded series; report counts, volume, and routing reason.

## Surface source contract

| Surface | Required target source | Required supporting source |
|---|---|---|
| Data Table | selected sheet | none |
| Overview for PIO | governed PIO slice | optional reference metadata |
| Governed EDA | `PIO_Sales_Data` | all three Wholesale sheets; PLC lookup as dimension only |
| Forecast Center | governed PIO, regardless of selected sheet | all Wholesale history, Working Days, PLC lookup |
| AI Analyst | governed PIO, regardless of selected sheet | all Wholesale history and governed Forecast Center payload |
| Anomaly Center | governed PIO, regardless of selected sheet | all Wholesale history |

Current known violations:

- Workspace Overview/Data Table/EDA follow the selected sheet.
- AI Analyst follows the selected sheet.
- AI Analyst and Anomaly Center use only the first Wholesale-named sheet.
- AI Analyst calls the legacy single-part forecast instead of the governed HMA/GMA/KUS Forecast Center.

These are tracked P0/P1 product issues, not accepted model behavior.

## Time and cutoff contract

- Pre-month model training uses completed months only.
- July 2026 actual is MTD through July 22.
- July output must be labeled `MTD actual + full-month nowcast`.
- August and later are forecast.
- A three-month horizon means the next three forecast months after the current nowcast/last complete month.
- Do not mix July MTD actual into a completed-month training series.

## Backtest and leakage contract

Default contract:

- expanding rolling-origin folds;
- 24 completed training months minimum;
- horizons 1–3 primary;
- common fold definitions for every compared model;
- same actual target and aggregation;
- no random split;
- no target-month actual PIO inputs;
- no same-month actual Wholesale for deployable models;
- Working Days are allowed because they are calendar-known;
- model selection must occur inside each fold when Auto is evaluated.

### Validated Revenue reference strategy

`model_strategy=reference_portfolio` is limited to Forecast Center Revenue
Brand anchors:

- HMA: validated optimized additive Holt-Winters candidate;
- GMA: `naive_last`;
- KUS: `working_day_adjusted_seasonal`.

It must not be applied to Quantity or Wholesale, and it does not change
Brand-to-child reconciliation, lifecycle routing, unit-revenue allocation, or
the July nowcast. Its registered 51-fold metrics apply only when the uploaded
source SHA-256 matches the governed 7/22 source; other sources must be labeled
as unvalidated for those metrics.

Numeric `Working_Days.Month` values in `YYYYMM` form must be parsed to the
corresponding calendar month. A matching cache with an empty Working Days map
is incomplete for reference-portfolio evaluation and may refresh only that
small reference sheet without reparsing the PIO fact sheet.

Reference expected fold counts on 42 completed months:

- Horizon 1: 18
- Horizon 2: 17
- Horizon 3: 16
- Combined: 51

## Accuracy scopes

Accuracy must name its scope:

- `overall portfolio`;
- `anchor brand`;
- `model`;
- `PLC`;
- `PIS_PNO`;
- `nowcast cutoff day`;
- `unit revenue reconstruction`;
- `allocation only`;
- `wholesale`.

Required metrics:

- WAPE;
- `max(0, 1-WAPE)` proxy;
- MAE;
- signed bias;
- bias percentage;
- fold-WAPE standard deviation;
- fold count;
- prediction coverage.

Model/PLC/PIS_PNO allocation accuracy must be calculated against held-out actual child values. A zero reconciliation delta is not allocation accuracy.

## Reference output evidence map

| Evidence | Location |
|---|---|
| Executive method and headline performance | `Executive_Summary!A27:D48` |
| Candidate formulas and model selection | `Model_Performance!A1:J55` |
| Quantity, part, nowcast and horizon evidence | `Model_Performance!A56:J151` |
| Definitions, limitations and QA | `QA_Assumptions!A1:D108` |
| Official revenue output | `Revenue_Forecast` |
| Total/model quantity method | `Quantity_Forecast` |
| Exact-part quantity/revenue | `Part_Planning` |
| Wholesale/Fleet inputs | `Wholesale_Drivers` |

## Change control

Update this contract when:

- a source sheet or canonical field changes;
- a new target/driver is introduced;
- brand or lifecycle mapping changes;
- a surface changes its governed source;
- backtest folds, horizons, metrics, or aggregation change;
- reference reproduction assumptions are confirmed or rejected.

Changing implementation without updating this contract is incomplete.
