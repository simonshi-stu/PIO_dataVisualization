# Forecasting Data Contract

Version: `1.4.0`  
As of: `2026-07-29`  
Current operational cutoff: `2026-07-28`

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
| Local path | `E:\Projects\hyundai forecasting\work\canonical_data\CapStone_Sales_Data_0722+PLC_merged_through_0728.xlsx` |
| SHA-256 | `9ff30f6bf08f9b631042f74e8a345d36cb7e4b46981f6acbf9169279851b54b9` |
| PIO rows | 480,984 |
| PIO minimum date | 2023-01-01 |
| PIO maximum date | 2026-07-28 |
| Latest complete month for pre-month training | 2026-06 |
| Current partial month | 2026-07 MTD through day 28 |
| Lineage | 7/28 source including historical Part Description/PLC corrections, July 2026 Wholesale/Fleet updates, and 2,859 PIO rows dated 2026-07-23 through 2026-07-28 |

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
3. application of the reference contract to the current governed 7/28 source.

## Sheet classification

| Sheet | Type | Governed role | Forecast target? | EDA role |
|---|---|---|---|---|
| `PIO_Sales_Data` | Fact | PIO accessory transactions/aggregates | Yes: Revenue and PIO Quantity | Primary PIO EDA |
| `Vehicle_Wholesale_Data` | Driver/fact | Current vehicle Wholesale and Fleet channels plus possible future plan columns | Yes: channel-specific vehicle quantity; driver for cross-checks | Relationship/driver EDA |
| `2023 Vehicle Wholesale` | Driver/fact | Historical 2023 vehicle Wholesale | Yes, through combined Wholesale history | Relationship/driver EDA |
| `2024 Vehicle Wholesale` | Driver/fact | Historical 2024 vehicle Wholesale | Yes, through combined Wholesale history | Relationship/driver EDA |
| `Working_Days` | Reference/driver | Monthly working-day calendar | No | Reference-only message |
| `PLC_Legend` | Reference/dimension | Part-description to PLC lookup | No | Reference-only message |

`PLC_Legend` and `Working_Days` must never be interpreted as ordinary PIO facts for KPI totals, rankings, anomaly detection, or forecast targets.

## Canonical fields

### `PIO_Sales_Data`

Observed shape: 480,984 rows, 12 columns.

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

### Governed source corrections and retained audit items

- `Carpet Floor Mat` is an existing `PLC_Legend` category; no new PLC category
  was created.
- All 714 `HBF14AC000` rows have `Part Description` and `PLC` equal to
  `Carpet Floor Mat`.
- After the HBF correction, PLC=`Cargo Mat` remains on 27,706 rows across 61
  other part numbers. Those rows are retained.
- Of the retained PLC=`Cargo Mat` records, 26,757 have Part Description
  `Cargo Mat`; 949 `K5F33AU000` rows have Part Description `Bed Mat`. The
  `K5F33AU000` mapping is a visible business-validation item and must not be
  changed without explicit approval.

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
| Wholesale PNVW | Wholesale-basket PIO revenue / Wholesale vehicles | USD per Wholesale vehicle | KUS Wholesale basket driver from 2026-06 onward |
| CFM Fleet PNVW | eligible Carpet Floor Mat Fleet revenue / Fleet vehicles | USD per Fleet vehicle | KUS Fleet basket driver from 2026-06 onward |
| Accessory units per vehicle | channel-specific PIO quantity / channel-specific vehicles | accessory units per vehicle | Ratio; do not combine Wholesale and Fleet denominators |

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
6. For KUS before 2026-06, retain the historical Wholesale-basket rule:
   `vehicle wholesale volume x PNVW = KUS MPI revenue`.
7. For KUS from 2026-06 onward, calculate two non-overlapping baskets:
   - `Wholesale MPI revenue = Wholesale vehicle volume x Wholesale PNVW`;
   - `Fleet MPI revenue = Fleet vehicle volume x CFM Fleet PNVW`;
   - `KUS forecast/nowcast = Wholesale MPI revenue + Fleet MPI revenue`.
8. The from-2026-06 Fleet scope is KUS, PLC=`Carpet Floor Mat`, and
   `PIS_MDL_YY=2027`. Treat Fleet penetration as 100%: allocate Fleet vehicle
   volume first, then route the remaining eligible Carpet Floor Mat volume to
   Wholesale. Never double count volume or revenue between baskets.

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
- July 2026 actual is MTD through July 28.
- July output must be labeled `MTD actual + full-month nowcast`.
- August and later are forecast.
- A three-month horizon means the next three forecast months after the current nowcast/last complete month.
- Do not mix July MTD actual into a completed-month training series.

## Backtest and leakage contract

Default contract:

- expanding rolling-origin folds;
- 24 completed training months minimum;
- horizons 1 through 3, with H1 as the primary decision horizon;
- common fold definitions for every compared model;
- same actual target and aggregation;
- no random split;
- no target-month actual PIO inputs;
- no same-month actual Wholesale for deployable models;
- Working Days are allowed because they are calendar-known;
- model selection must occur inside each fold when Auto is evaluated.
- when a complex model improves WAPE by no more than 0.005 absolute
  (0.5 percentage point), prefer the simpler explainable model after the
  governed bias, stability, and coverage checks.

### Validated Revenue reference strategy

`model_strategy=reference_portfolio` is limited to Forecast Center Revenue
Brand anchors:

- HMA: validated optimized additive Holt-Winters candidate;
- GMA: `naive_last`;
- KUS: `working_day_adjusted_seasonal`.

It must not be applied to Quantity or Wholesale, and it does not change
Brand-to-child reconciliation, lifecycle routing, unit-revenue allocation, or
the July nowcast. The fixed specification was retrained and rerun on the
governed 7/28 source. Its 51-fold metrics were unchanged, and they apply only
when the uploaded source SHA-256 matches the registered 7/28 source.

Numeric `Working_Days.Month` values in `YYYYMM` form must be parsed to the
corresponding calendar month. A matching cache with an empty Working Days map
is incomplete for reference-portfolio evaluation and may refresh only that
small reference sheet without reparsing the PIO fact sheet.

Reference expected fold counts on 42 completed months:

- Horizon 1: 18
- Horizon 2: 17
- Horizon 3: 16
- Combined: 51

### Pretrained ML challenger contract

`tree_meta_selector_v1` and `elastic_net_anchor_residual_v1` are optional
Revenue Brand-anchor challengers. They are never trained by the browser or by
a Forecast Center request. The backend loads deterministic JSON artifacts only
when their source hash matches the uploaded workbook; a mismatch fails closed
and requires the offline training script.

- Tree Meta-Selector defaults to the validated anchor and may use only a
  `0.7-0.9` anchor-weight blend when nested dollar-error evidence clears a
  `0.005` WAPE-gain gate.
- Elastic Net: a Revenue-weighted global HMA/GMA/KUS panel model competes
  against leaving the governed anchor uncorrected.
- Outer evaluation uses the governed 24-month H1/H2/H3 folds.
- Tree dollar-error improvements, Elastic Net residual targets, and Elastic Net hyperparameters
  use only target months strictly earlier than each outer origin.
- Elastic Net selection uses the last six synchronized inner origins, fixed
  alpha `0.001/0.01/0.05/0.1/0.2/0.5`, L1 ratio `0.25/0.5/0.75`, and residual
  clips `+/-5%`, `+/-10%`, and `+/-15%`.
- Features are completed target lags and rolling statistics, Brand x month,
  Brand x horizon, KUS x Working-Day ratio, KUS x seasonal ratio, HMA x trend,
  official anchor identity, and the statistical anchor prediction.
- Same-month actual Wholesale/Fleet, target-month PIO, partial-month July values, and
  reference-workbook forecasts are excluded.
- Deployment uses NumPy CPU inference; no GPU or page-load fitting is allowed.
- Full fold predictions remain local audit evidence. Deployable artifacts omit
  Brand-month actual/prediction totals and retain only metrics plus residuals
  needed for interval calibration.

### Evaluation scope identities and registered-evidence gate

- `application_recent_h1` is the legacy application diagnostic. It contains
  three to six H1 prediction rows per eligible Brand. Its metadata reports
  common origin rows separately from Brand prediction rows. It is not ranked
  against the governed contract.
- `governed_h123_24m_h1_18_h2_17_h3_16_official_total_51` is the governed
  comparison scope: 24 minimum training months, H1/H2/H3, 18/17/16 = 51
  Official Total common-origin rows.

Registered Revenue reference metrics may be injected only when the current
source hash, PIO Revenue target, completed cutoff `2026-06`, unfiltered complete
HMA/GMA/KUS coverage, Official Total aggregation, and `pio-backtest-v1` all
match. The backend explicitly marks request-scope eligibility. A filtered
request with the same workbook hash remains unvalidated.
The gate is fail-closed: aggregation, contract version, horizons, exact fold
counts and keys, full prediction coverage, target, and evaluation cutoff are
required metadata. Missing fields are mismatches, not inferred defaults.

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

Allocation-only diagnostics use origin-known quantity shares, or quantity
multiplied by prior realized unit price for Revenue. The held-out target actual
parent total may be supplied only to isolate child-share error. Reports include
WAPE, accuracy proxy, coverage, row count, fold count, scope, and grain, and do
not label these diagnostics as end-to-end forecast accuracy.
Coverage audits include parent-fold coverage, eligible-entity coverage,
missing-signal rows, zero-signal parents, and zero-actual parents. Missing
signals are not rewritten as covered zero predictions. Revenue allocation uses
a recent-six revenue-equivalent signal: same-window quantity multiplied by
same-window realized unit revenue, algebraically equal to recent-six revenue,
with a prior-history fallback when the recent parent signal is zero.

## Forecast Exceptions contract

Forecast Center returns one complete top-level exception list independent of
the displayed hierarchy level. Every item contains `reasonCode`, `severity`,
`scope`, `grain`, `seriesKey`, `entityKey`, `forecastMonth`, structured
`evidence`, and `suggestedAction`. Evidence uses only data known by the request
cutoff.
Series-level findings set `forecastMonth` to null and include
`seriesLevel=true`; forecast-specific findings emit one item for each actually
affected forecast month. Model, PLC, and PIS_PNO profiles are computed from
complete cutoff history before eligibility filtering.

Governed reason codes are `inactive_discontinued`, `low_volume`,
`insufficient_active_months`, `history_gaps`, `recent_zero_streak`,
`new_reintroduced_proxy`, `zero_forecast_historical_unit_price`, and
`planner_review_residual`. Low volume and insufficient active months are
separate evidence conditions, even when both prevent regular allocation.

## Prediction interval contract

Prediction intervals use horizon-specific held-out rolling-origin residuals.
They satisfy `0 <= lower <= point <= upper` and disclose
`nominalCoverage`, `empiricalCoverage`, `coverageSampleCount`,
`calibrationResidualCount`, `calibrationScopeId`, and `validationStatus`.

Brand and Official Total intervals may be validated only with sufficient
held-out residuals at that grain. Model, PLC, and PIS_PNO intervals remain
unvalidated until child-level held-out coverage is tested; they cannot inherit
Brand empirical coverage. Reconciliation remains a separate arithmetic check.
Residuals must be generated by the same deployed strategy at each origin:
reference HMA uses governed Holt-Winters, GMA uses `naive_last`, KUS uses
working-day-adjusted seasonal, and Auto reselects from origin-known history.
Current-month Nowcast intervals are `unvalidated_nowcast` unless
cutoff-specific historical residuals exist. In-process caches are keyed by
source hash and fact signature, cutoff, target, strategy, filter scope,
working-day signature, and forecast settings; mismatched scopes cannot reuse
diagnostics.

## Forecast output run and export contract

Governed major exports use contract `pio-output-run-v1`. A run is an immutable,
process-local snapshot keyed by workbook, governed sheet, source hash, filtered
fact/Wholesale/Working-Days signature, completed cutoff, canonical filters, and
all forecast settings. Preparing a run:

- filters PIO and Wholesale sources once;
- builds Revenue, Quantity, and Wholesale exactly once each;
- builds one exact-part planning bundle;
- records the requested strategy and the effective strategy for every metric;
- applies `reference_portfolio` only to Revenue, with Quantity and Wholesale
  explicitly using `auto`;
- creates one typed canonical Executive Summary used by web preview, PDF, and
  Detailed Excel.

The canonical summary contains run ID, source filename/hash, source signature,
cutoff, filters, horizon, Top N, requested/effective strategies,
Nowcast/Forecast periods and units, monthly Revenue/PIO Quantity/Wholesale
headline totals, Top 10 PLC, and reconciliation controls.

Preview, Executive Summary PDF, Detailed Excel, and current-view CSV read only
the stored run. Downloads never call the forecast engine. A missing or expired
run returns HTTP 404 and is never silently rebuilt. The bounded LRU/TTL cache is
not durable: backend restart invalidates every run and its artifact URLs.

Detailed Excel retains the seven governed SOP sheets and adds hidden
`Run_Metadata`. `Executive_Summary` and `Run_Metadata` carry the identical run
identity and period/strategy contract. Current-view CSV also includes run ID,
source hash, cutoff, requested/effective strategy, unit, period, and period
type.

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
