# Forecast Model Registry

Version: `1.3.0`  
Contract: `pio-backtest-v1`  
As of: `2026-07-29`  
Machine-readable source: `config/forecast_model_registry.json`

## Why this registry exists

This project previously mixed several meanings of “accuracy”:

- the current Forecast Center’s outer holdout score;
- the reference workbook’s expanding H1–H3 WAPE;
- Brand-level versus official-total errors;
- arithmetic reconciliation versus held-out child-allocation accuracy;
- pre-month forecast versus cutoff-specific nowcast.

They are not interchangeable. This registry makes every method state its target, level, implementation status, evidence source, and evaluation contract.

## Status rules

| Status | Meaning |
|---|---|
| `implemented` | Runnable in the application or unified harness |
| `specification_only` | Formula/behavior recovered, but exact source code or source snapshot is unavailable |
| `challenger` | Eligible for common-contract evaluation, not a production champion |
| `diagnostic_only` | Evaluates a reconstruction/allocation component, not an official anchor |
| `blocked` | Exact reproduction needs missing evidence |

“Reference” does not mean “implemented.” The reference workbook gives strong formula and result evidence, but its original 7/15 input snapshot and fitted ETS implementation are not available locally.

## Current and target architecture

| Target | Current application | Reference contract to reproduce |
|---|---|---|
| Revenue | Independent Auto model for HMA/GMA/KUS | HMA ETS + GMA last month + KUS working-day-adjusted seasonal |
| PIO Quantity | Independent Auto Brand anchors | One total ETS anchor, then rolling-six-month Model allocation |
| Wholesale | Statistical Brand forecast, then Model allocation | Sponsor plan first, documented internal fallback |
| Exact part | Governed hierarchical allocation | Previous-month exact-part share with fallback |
| Unit revenue | Quantity × expected unit revenue weights | Latest prior exact-part realized unit revenue, then fallback |
| Current month | July nowcast exists without its own recovered benchmark | Cutoff Day 5/10/15/20/25 blended nowcast |

The update path is:

1. freeze the shared data/backtest contract;
2. run current Auto and reference-contract proxies on identical folds;
3. reproduce cutoff and lower-level tests separately;
4. identify residual differences caused by source snapshot, implementation, or business adjustments;
5. only then test ML challengers.

## Latest available common-contract result (merged 7/28 source)

The current governed runs are stored locally at
`outputs/backtests/unified_backtest_9ff30f6bf08f_pio-backtest-v1.json` and
`outputs/backtests/rebuilt_revenue_portfolio_9ff30f6bf08f_pio-backtest-v1.json`.
They use the merged 7/28 source SHA-256
`9ff30f6bf08f9b631042f74e8a345d36cb7e4b46981f6acbf9169279851b54b9`,
completed months through 2026-06, and the same 51 H1–H3 folds for each result
below. The rebuilt reference portfolio reproduced its historical metrics
exactly, so the source update caused neither improvement nor degradation.

| Official-total run | WAPE | Accuracy proxy | Bias % |
|---|---:|---:|---:|
| Rebuilt reference Revenue: validated HMA HW + GMA last month + KUS working-day seasonal | 6.89% | 93.11% | 1.07% |
| Frozen legacy Revenue: HMA damped trend + GMA log-linear + KUS seasonal mean | 9.35% | 90.65% | -0.65% |
| Repository Additive ETS reference proxy (isolated HMA comparison) | 10.04% | 89.96% | 2.03% |
| Current Auto Revenue | 10.28% | 89.72% | 1.30% |
| Corrected total-Quantity ETS proxy | 9.58% | 90.42% | 1.99% |
| Current Auto Quantity by Brand | 9.91% | 90.09% | 2.68% |
| Current Auto Wholesale | 5.59% | 94.41% | 0.14% |

The rebuilt reference portfolio is now the common-contract Revenue champion.
It is exposed as the explicit `reference_portfolio` Forecast Center strategy,
but `auto` remains the website default pending explicit user approval. The
original reference workbook remains specification evidence rather than exact
source-snapshot reproduction.

The gap is concentrated in HMA. On the reference-style proxy run:

- GMA Last Month reproduces the reference GMA WAPE at about 14.77%.
- KUS Working-Day Seasonal is close to the reference result: about 9.58% versus 9.63%.
- HMA repository ETS is about 13.52% WAPE versus the reference HMA value of about 10.69%.

The HMA experiment compared 1,080 standard ETS/Holt-Winters configurations plus
the repository ETS and legacy damped-trend baselines. All 1,082 candidates had
100% coverage on the same 51 folds. The governed selection is:

- additive trend + additive seasonality, period 12;
- heuristic initialization and optimized smoothing parameters;
- `log1p` transform with correct inverse;
- rolling 24-month training window;
- fold-local robust winsorization;
- `remove_bias=True`;
- HMA combined WAPE `9.8928%` (H1 `8.9033%`, H2 `9.2725%`, H3 `11.6710%`).

The rebuilt Official Total is `6.8939%` WAPE / `93.1061%` accuracy proxy, with
100% coverage and exact repeatability. This exceeds the reference headline but
does not prove exact reproduction because the source snapshot and ETS
implementation differ.

The prior KUS proxy accidentally had an empty Working Days map because numeric
`YYYYMM` values were not parsed as month numbers. After fixing the cache parser,
KUS Working-Day Seasonal reproduces the reference WAPE at `9.6282%`.

## Unified evaluation contract

The canonical implementation is `pio_platform/backtest_harness.py`.

- Expanding rolling-origin folds.
- Minimum 24 completed training months.
- Horizons 1, 2, and 3.
- For 42 completed months, expected fold counts are 18, 17, and 16.
- Primary metric is WAPE.
- Accuracy proxy is `max(0, 1 - WAPE)`.
- Official total is evaluated after HMA/GMA/KUS are summed on the same origin/horizon row.
- Auto selection occurs inside each outer fold using training history only.
- Partial July actual is excluded from pre-month training and evaluated as a separate nowcast problem.

`Selected Model` means the method fitted on all available completed history for production. `Backtest Model` means the method selected using only one outer fold’s training window. The two may differ without being a defect.

Stable scope IDs:

- `application_recent_h1`: legacy recent H1 diagnostic, three to six points per
  Brand. Common origin rows and Brand prediction rows are distinct counts.
- `governed_h123_24m_h1_18_h2_17_h3_16_official_total_51`: 24-month minimum
  training, H1/H2/H3 counts 18/17/16, 51 Official Total common-origin rows.

Registered `rebuilt_reference_portfolio_v1` values are eligible only when the
source hash, PIO Revenue, cutoff `2026-06`, unfiltered complete HMA/GMA/KUS,
Official Total aggregation, and `pio-backtest-v1` all match. Backend
request-scope eligibility is mandatory; hash equality alone is insufficient.
The gate also requires explicit horizons, exact 18/17/16 fold counts and 51
fold keys, full prediction coverage, target, aggregation, contract, and cutoff.
It never supplies permissive defaults for missing evidence.

### Fair Additive ETS comparison

`repository_additive_ets_reference_proxy` versus
`rebuilt_reference_portfolio_v1` is an
`isolated_hma_ets_comparison`, not a forced-ETS comparison across all Brands.
Both use the same source, cutoff, 51 common folds, target, and Official Total
aggregation. Only HMA changes. GMA remains `naive_last`, KUS remains
`working_day_adjusted_seasonal`, and the production default remains unchanged.

### Allocation accuracy and intervals

Model, PLC, and PIS_PNO diagnostics are `allocationOnly`. They report held-out
child-share error after supplying actual parent total solely for isolation;
Brand error would propagate in an end-to-end result. Reconciliation PASS is not
an allocation-accuracy score.

Intervals use horizon-specific held-out rolling-origin residuals, nominal 90%
coverage, and report empirical coverage and calibration counts. Brand and
Official Total can be validated with sufficient residuals. Child allocation
bands remain unvalidated until held-out Model/PLC/PIS_PNO coverage is tested.
Every calibration origin uses the deployed strategy. Auto is selected
fold-locally; the reference portfolio uses governed HMA Holt-Winters, GMA
`naive_last`, and KUS working-day-adjusted seasonal. Nowcast is separately
`unvalidated_nowcast` without cutoff-specific residuals. Deterministic
scope-keyed caches reuse these diagnostics only for identical source, cutoff,
target, strategy, filters, Working Days, and forecast settings.

The previous `referenceQuantityTotalEtsProxy` output is
`invalid_superseded`: the script had not explicitly supplied
`predictor=make_predictor('ets_additive')`. Its stored numbers are audit history,
not corrected Quantity evidence, until a safe corrected run is performed.

## Registered methods

### Current Auto Brand anchors

Implementation:

- `pio_platform.forecasting.select_best_model`
- `pio_platform.forecasting.forecast_history`

The candidate set includes simple baselines, recent means, trend models, seasonal models, deterministic additive ETS, and Croston SBA. This method remains the current implemented path until the common-contract comparison is complete.

Previously reported application evidence:

| Metric | Overall | HMA | GMA | KUS |
|---|---:|---:|---:|---:|
| Revenue accuracy | 83.03% | 79.10% | 87.13% | 89.69% |
| PIO Quantity accuracy | 83.84% | 78.16% | 88.98% | 96.83% |
| Wholesale accuracy | 93.09% | 92.37% | 92.45% | 93.80% |

These values must not be presented as directly disproving the reference results until both are rerun on the same source, folds, horizons, and portfolio aggregation.

### Reference Revenue portfolio

Recovered specification:

- HMA: ETS.
- GMA: last-month revenue.
- KUS: working-day-adjusted seasonal.
- Official total: exact HMA + GMA + KUS.

Reference evidence reports:

- Combined H1–H3 WAPE: `8.2565%`, accuracy proxy `91.7435%`.
- H1 WAPE: `7.7497%`.
- H2 WAPE: `7.7074%`.
- H3 WAPE: `9.4080%`.

The current repository’s fixed-coefficient `ets_additive` is a proxy, not proof that the reference ETS fit has been recovered.

### Reference Quantity portfolio

Recovered specification:

1. forecast one total Quantity anchor with ETS;
2. calculate rolling-six-month Model signals;
3. scale all Models to the total anchor;
4. allocate to exact parts using leakage-safe prior shares;
5. reconcile exactly;
6. add the one explicitly governed KUS fleet adjustment once, if enabled.

Reference total-anchor WAPE is `7.8901%`, or `92.1099%` accuracy proxy. Its Model allocation WAPE is `8.8033%`.

### Lower-level diagnostics

| Component | Reference WAPE | Accuracy proxy | Meaning |
|---|---:|---:|---|
| Exact-part allocation | 34.3949% | 65.6051% | Held-out `PIS_PNO` quantity allocation |
| Expected unit revenue | 37.0648% | 62.9352% | Held-out unit-revenue reconstruction |

These scores expose uncertainty that a zero reconciliation difference cannot reveal. The application still needs equivalent independent Model, PLC, and PIS_PNO tests.

### Cutoff-specific nowcast

Recovered formula:

`Nowcast = (1 - MTD Weight) × Pre-month Forecast + MTD Weight × MTD Completion Projection`

| Cutoff | MTD weight | Reference WAPE |
|---:|---:|---:|
| Day 5 | 0.10 | 8.2155% |
| Day 10 | 0.40 | 7.3920% |
| Day 15 | 0.60 | 5.3961% |
| Day 20 | 0.80 | 5.9013% |
| Day 25 | 1.00 | 2.9188% |

July 22 is not itself a historical Day-20 proof. A proper test must simulate the same cutoff information on prior completed months.

### ML challengers

Two CPU-only challengers are implemented and pretrained on the governed 7/28
source with cutoff `2026-06`:

| Model | H1 WAPE | H2 WAPE | H3 WAPE | Combined WAPE | Coverage | Decision |
|---|---:|---:|---:|---:|---:|---|
| `tree_meta_selector_v1` | 5.9742% | 7.3369% | 8.5593% | 7.2417% | 100% | Not promoted |
| `elastic_net_anchor_residual_v1` | 6.0508% | 6.6949% | 8.5325% | 7.0457% | 100% | Not promoted |
| `rebuilt_reference_portfolio_v1` | 5.8342% | 6.5485% | 8.4476% | 6.8939% | 100% | Remains champion |

Both ML methods use the exact same 18/17/16 Official Total folds. The tree
defaults to the validated anchor and may use only a 0.7-0.9 anchor-weight blend
after a nested 0.005 WAPE-gain gate. Elastic Net uses Revenue weights, six
inner rolling origins, fixed strong-regularization/clip candidates, and an
explicit no-correction competitor. Nested dollar-error improvements, residual
targets, and hyperparameters are restricted to data available before every
outer origin. The final Elastic artifact selected no correction because the
best residual correction made inner Official Total WAPE worse. The browser
loads pretrained JSON artifacts and never trains models on page open. NumPy
CPU is the only runtime dependency, so a GPU is not required.

Same-month realized Wholesale and Fleet remain oracle-only and are not present
in either artifact. A source-hash mismatch requires an explicit offline retrain rather
than silent page-load fitting.

## Promotion decision

A candidate becomes champion only after the unified harness shows:

1. identical source hash, folds, horizon, and aggregation;
2. no leakage;
3. a more complex challenger with worse WAPE cannot be promoted; a small positive
   gain inside the 0.5-point tie band requires documented simplicity,
   bias, and stability review;
4. acceptable coverage and business behavior;
5. reconciliation passes;
6. separate allocation accuracy where relevant;
7. final output definitions and caveats are updated.

Never change production logic only to match the reference percentage. Any remaining gap must be classified as:

- source snapshot/cutoff difference;
- model implementation difference;
- driver availability difference;
- aggregation/fold difference;
- business adjustment difference;
- unresolved evidence gap.
