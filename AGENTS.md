# PIO Demand Intelligence — Agent Operating Contract

This file is the first-read contract for every Codex session and subagent working in this repository.

## Start here — do not rediscover the project from the raw workbook

Before scanning code or loading the 480,984-row workbook:

1. Read `docs/forecasting/DATA_CONTRACT.md`.
2. Read `docs/forecasting/MODEL_REGISTRY.md`.
3. Read `config/forecast_model_registry.json` when model status or benchmark numbers matter.
4. Read `pio_platform/backtest_harness.py` before changing accuracy calculations.
5. Inspect the raw workbook only when the source hash changed, a field is missing from the contract, or an actual model/backtest run requires the observations.

Do not spend a new session re-inferring sheet roles, the HMA/GMA/KUS hierarchy, or reference-workbook formulas. The documents above are the durable project memory.

## 代码风格与实现原则

1. **最小实现**：只实现需求中明确要求的功能，不做“提前防御”或“万一以后需要”的扩展。
2. **拒绝过度保护**：不添加不必要的空值检查、边界处理、日志记录，除非需求明确要求。
3. **直给优于优雅**：能用 10 行解决的问题，不用 100 行做“架构设计”。
4. **YAGNI（You Aren't Gonna Need It）**：不写当前不需要的代码。
5. **按需注释**：只为本次新增或修改、且用途/返回内容不直观的函数添加简短注释；不进行全仓库注释重写。

## 性能实施指南约定

- 每个性能阶段在 `outputs/performance/` 新建独立中文指南，文件名为 `PHASE_<N>_PERFORMANCE_IMPLEMENTATION_GUIDE_zh-CN.md`。
- 不覆盖或改写已完成阶段的指南；后续 Phase 只创建自己的指南。
- 指南正文使用中文。函数名、API、cache key 等专业术语可保留英文，并紧跟中文说明。

## 性能 Phase 执行约束

以下规则适用于每一个性能 Phase，包括已完成的 Phase 1：

1. **不引入子 agent 或 worker agent**：性能 Phase 由主 agent 直接完成，不为审查、编码或验证额外消耗 agent token；只有用户明确要求时才例外。
2. **不做保护性测试**：只执行 `git diff --check`，并人工核对 scoped diff 是否实现当前 Phase 架构、是否保持在 allowlist 内且不改动全局行为；不默认运行 test、compile、type check、回归或 timing。
3. **简单代码审查**：完成后检查新增/修改代码是否以最少的直接分支、状态和函数满足当前 Phase；删除不必要的抽象、防御性分支和无关注释。
4. **不加载全量数据集验证**：不扫描 raw workbook，也不加载完整 parsed bundle、月度事实或全量数据来跑测试或 timing。已有基线仅作设计依据；只有用户明确要求时才进行这类运行。

这些约束只收紧性能实现的执行与验证，不替代 Forecasting 变更所需的数据治理或业务验证。

## Project objective

The product analyzes Hyundai Mobis PIO accessory demand and produces governed forecasts for:

- accessory revenue;
- PIO installation quantity;
- dealer/non-fleet vehicle wholesale quantity;
- the `Brand -> Model -> PLC -> PIS_PNO` planning hierarchy;
- July/current-month MTD nowcast versus future-month forecasts;
- executive and detailed Excel outputs.

The immediate modeling objective is to replace the current/legacy forecasting contract with a reproducible version of the reference-workbook method, then introduce ML challengers only when they beat the statistical champion on identical leakage-safe folds.

Never promise 90% or 95% accuracy. Report the exact metric, aggregation level, horizons, fold count, source hash, coverage, and cutoff.

## Canonical local evidence

These files are local evidence and must not be committed unless the user explicitly requests it:

- Current source workbook: `E:\Projects\hyundai forecasting\work\canonical_data\CapStone_Sales_Data_0722+PLC_merged_through_0728.xlsx`
- Reference forecast workbook: `C:\Users\Lenovo\Desktop\PIO\PIO_Forecast_Output_20260715_v2.xlsx`
- Business notes: `C:\Users\Lenovo\Desktop\新建 Microsoft Word 文档 (3).docx`
- Local project report: `E:\Projects\hyundai forecasting\docs\PIO_Forecast_Center_设计与算法报告_2026-07-26.docx`

Current source evidence:

- SHA-256: `9ff30f6bf08f9b631042f74e8a345d36cb7e4b46981f6acbf9169279851b54b9`
- PIO rows: `480,984`
- PIO date range: `2023-01-01` through `2026-07-28`
- July 2026 is partial-month actual through July 28.
- The governed source uses the 7/28 workbook's historical Part Description/PLC
  corrections and July 2026 Wholesale/Fleet updates.
- All 714 `HBF14AC000` rows use the existing `Carpet Floor Mat` value for both
  Part Description and PLC. This is a correction, not a new PLC category.
- After that correction, PLC=`Cargo Mat` remains on 27,706 rows across 61
  other part numbers. `K5F33AU000` has 949 `Bed Mat` descriptions mapped to
  PLC=`Cargo Mat`; preserve it pending explicit business validation.

Reference-workbook evidence:

- It was generated from a different source snapshot, `CapStone_Sales_Data_0716.xlsx`.
- Reference source SHA-256: `cec39f4f681f084b07f0fcc4503bf2293184eb211a58083002a599c9d882f19a`
- Reference PIO rows: `475,178`
- Reference actual cutoff: `2026-07-15`
- Reference completed training cutoff: `2026-06-30`

Exact numeric reproduction is not proven until the original reference source snapshot and its fitted-model implementation are available. Treat formulas recovered from the reference workbook as a specification, not as recovered source code.

## Governed dataset roles

- `PIO_Sales_Data`: the only PIO target fact source for installation quantity and accessory revenue.
- `Vehicle_Wholesale_Data`, `2023 Vehicle Wholesale`, `2024 Vehicle Wholesale`: all must be combined for governed wholesale history. Clamp `-1` and other negative business measures to zero.
- `Working_Days`: calendar/driver/reference data. It is not a revenue or quantity fact table.
- `PLC_Legend`: PLC lookup/reference data. It is not a time series or forecast target.
- Reference forecast output: benchmark/specification evidence only. Never use its forecasts as actual training labels.

Read `docs/forecasting/DATA_CONTRACT.md` for field-level rules.

## Brand and hierarchy governance

- Official anchors are `HMA`, `GMA`, and `KUS`.
- Never use raw `H`/`K` as final business anchors.
- Hyundai and Genesis must be separated by normalized model identity. Raw `K` is only a KUS fallback when an exact model mapping is unavailable.
- Keep IONIQ/EV/HEV/PHEV model variants separate unless a governed mapping explicitly combines them.
- Revenue hierarchy: official Brand revenue is the statistical anchor. Model/PLC/PIS_PNO revenue is an allocation that must reconcile to its parent.
- Quantity hierarchy under the reference method: one total ETS anchor -> rolling-six-month model signal -> child allocation -> exact reconciliation.
- Wholesale has Brand/Model hierarchy but no PLC hierarchy.
- Do not exclude KUS Fleet. Before June 2026, KUS used the governed Wholesale
  basket (`vehicle wholesale volume x PNVW`). Starting June 2026, keep
  Wholesale and Fleet as separate baskets: Wholesale volume x Wholesale PNVW
  plus Fleet volume x Carpet Floor Mat PNVW equals the KUS forecast/nowcast.
- For KUS from June 2026 onward, the Fleet allocation scope is
  PLC=`Carpet Floor Mat` and `PIS_MDL_YY=2027`. Fleet penetration is 100%;
  allocate Fleet vehicle volume first, then route the remaining eligible
  Carpet Floor Mat volume to Wholesale. Never double count a vehicle or its
  revenue across both baskets.

## Accuracy and backtest contract

All model comparisons must use `pio_platform/backtest_harness.py`.

Default primary contract:

- expanding/rolling-origin time-series folds; never random split;
- completed months only for pre-month model fitting;
- minimum training history: 24 months;
- horizons: 1, 2, and 3 months;
- H1 is the primary decision horizon; H2 and H3 remain required governed
  diagnostics and must not be hidden.
- expected fold counts on 42 completed months: 18, 17, and 16;
- primary error: WAPE;
- accuracy proxy: `max(0, 1 - WAPE)`;
- also report MAE, signed bias, bias percentage, fold-WAPE standard deviation, prediction coverage, and fold count;
- official portfolio evaluation sums HMA/GMA/KUS predictions at each common fold before calculating total error;
- a model within 0.5 WAPE point of the empirical best is tie-broken by lower
  absolute bias, greater stability, then lower complexity;
- horizon 4–6 outputs are exploratory unless independently validated.
- Prediction intervals must be horizon-specific, nonnegative, and calibrated only
  from held-out rolling-origin residuals. Every interval result must disclose its
  nominal coverage, empirical coverage, sample count, residual count, calibration
  scope ID, and validation status. Brand coverage must never be inherited by
  Model, PLC, or PIS_PNO without independent child-level coverage testing.
  Calibration residuals must use the deployed strategy at every historical
  origin; Auto selection is fold-local. A current-month nowcast remains
  unvalidated unless cutoff-specific historical residuals exist.

`Selected Model` for the final production fit and `Backtest Model` used inside an outer fold are different concepts. Model Performance must state that outer-fold WAPE is produced by leakage-safe selection using only the fold’s training history.

No model may be promoted using in-sample fit, random splits, oracle future Wholesale, skipped bad folds, or different aggregation rules.

## Reference-method specification to reproduce

The reference workbook specifies:

- Revenue: HMA=`ETS`; GMA=`Last-Month Revenue`; KUS=`Working-Day-Adjusted Seasonal`.
- Official total revenue: exact HMA + GMA + KUS.
- Quantity total anchor: aggregate additive ETS.
- Model quantity mix: rolling six-month mean, reconciled to the total ETS anchor.
- Exact-part quantity: previous-month exact-part share with governed fallbacks.
- Expected unit revenue: latest valid prior exact Model + PIS_PNO realized unit revenue, then documented fallbacks.
- Official lower-level revenue: Brand revenue allocated by `quantity x expected unit revenue` weights and reconciled.
- Nowcast: cutoff-specific blend of pre-month forecast and leakage-safe MTD completion projection.

Recovered reference headline metrics are recorded in `config/forecast_model_registry.json`. They are evidence targets, not automatically comparable to the current application’s existing outer-holdout metric.

## ML policy

ML models are challengers, never default champions.

- Start with regularized Ridge/Elastic Net using leakage-safe lag, calendar, working-days, wholesale, lifecycle, and mix features.
- Prefer the simpler, easier-to-explain model whenever a more complex
  challenger improves WAPE by no more than 0.5 percentage point on the same
  governed folds.
- Add tree boosting only after the common backtest harness exists. The reference workbook’s Horizon-1 XGBoost challenger did not beat its comparable ETS result.
- Do not fit a complex model independently to a 42-month Brand series and call it reliable. If using a global/panel model, split by time and preserve entity grouping.
- Every feature must document when it becomes known. Same-month actual Wholesale is oracle-only and cannot be used in deployable evaluation.
- Promotion requires improvement on common folds plus acceptable bias, stability, coverage, reconciliation, and business explainability.

## Product source routing

### Data Workspace and EDA

Data Table may browse the selected sheet. Governed PIO EDA must not reinterpret `PLC_Legend` or `Working_Days` as sales facts.

Required behavior:

- selecting PIO/Wholesale may show relevant governed analytics;
- selecting `PLC_Legend` or `Working_Days` must show a clear `reference sheet — excluded from governed EDA` state;
- PIO relationship analysis must use `PIO_Sales_Data` plus all three Wholesale sheets.

### Forecast Center

Forecast Center must resolve the governed PIO sheet, all Wholesale history, Working Days, and PLC reference roles regardless of the sheet currently browsed in Data Workspace.

### AI Analyst and Anomaly Center

They must not inherit the currently selected reference/Wholesale sheet as their target source.

Required future change:

- force governed PIO targets;
- combine all Wholesale history, not the first sheet whose name contains `Wholesale`;
- consume the HMA/GMA/KUS Forecast Center payload instead of the legacy single-part forecast;
- use the same accuracy, hierarchy, nowcast, and reconciliation contracts as Forecast Center.

## Known P0/P1 work queue

P0:

1. Preserve and independently review the validated Revenue `reference_portfolio`; Auto remains default until explicit approval.
2. Backtest current Auto and legacy/frozen methods on the same folds/horizons.
3. Restore Day 5/10/15/20/25 cutoff-specific nowcast backtests.
4. Add independent Model, PLC, and PIS_PNO allocation accuracy.
5. Separate final selected model from outer-fold selected model in Model Performance.
6. Govern AI Analyst and Anomaly Center to PIO + all Wholesale history.

## Latest Revenue champion

On source SHA-256 `f44048f30632e6f1d77d5336d2d313b4855e9d1cec95577b4a50f1c8f33c2c47`
under `pio-backtest-v1`, the explicit `reference_portfolio` strategy is the
validated Revenue champion:

- HMA: optimized additive Holt-Winters, heuristic initialization, `log1p`,
  rolling 24 months, fold-local robust winsorization, bias removal;
- GMA: `naive_last`;
- KUS: `working_day_adjusted_seasonal`;
- Official Total: `6.8939%` WAPE / `93.1061%` accuracy proxy on 51 common folds.

This strategy is implemented but is not the website default. Do not transfer
its registered metrics to a different source hash.

P1:

1. Mark Legend/Working Days as reference-only in EDA.
2. Add deployable Ridge/Elastic-Net challengers.
3. Add panel/tree boosting only after leakage-safe feature availability is proven.
4. Compare current source results with the reference source/hash and explain residual differences.

## Multi-agent workflow

Use parallel agents for read-heavy independent tasks; avoid parallel writes to the same files.

Performance Phase 例外：遵循“性能 Phase 执行约束”，由主 agent 直接完成；不得默认派发 subagent、worker 或 reviewer。

Recommended roles:

- `project_architect`: map UI -> API -> fact table -> forecast -> export; read-only.
- `data_contract_auditor`: validate source roles, cutoff, hashes, and leakage; read-only.
- `reference_model_forensics`: extract formulas/parameters/evidence from the reference artifacts; read-only.
- `forecast_evaluator`: run the unified harness and compare models; read-only except backtest outputs.
- `integration_worker`: the only agent that edits governed product logic for one approved change.
- `independent_reviewer`: verify diff, tests, business controls, and output labels.

The primary agent owns decisions, consolidates subagent evidence, and performs or approves integration. Subagents must return concise findings with file references rather than raw logs.

## Cache policy

Runtime upload cache lives in `outputs/`:

- `<workbook_id>.xlsx`
- `<workbook_id>_*_bundle.pkl`
- `index.json`

These files are disposable and may be deleted after the backend is stopped. Their deletion clears upload history and causes the next upload to be parsed again.

Do not casually delete:

- `outputs/analyst_memory.sqlite3`;
- `outputs/analyst_memory.json`;
- `outputs/backtest_cache/` when its source hash and contract still match;
- source Excel files, reference files, reports, or Git content.

Backtest cache must be keyed by source SHA-256 and contract version. Never reuse it after either changes.

## Change safety

- Preserve unrelated dirty-worktree changes.
- Do not use `git add .` in a mixed worktree.
- Do not modify Forecast Center logic solely to match a target percentage.
- Do not train on forecast outputs, partial future values, or same-month oracle drivers.
- Do not change source/hierarchy/accuracy definitions without updating Data Contract and Model Registry.
- Do not upload source workbooks, reports, audit outputs, caches, or local reference files unless explicitly requested.

## Definition of done for forecasting changes

A forecasting change is complete only when:

1. source hash, cutoff, metric, level, horizons, folds, and aggregation are recorded;
2. unified backtest results are reproducible;
3. current champion and challenger use identical folds;
4. nowcast is evaluated separately from pre-month forecast;
5. allocation accuracy is distinguished from reconciliation;
6. Brand -> Model -> PLC/PIS_PNO controls pass where applicable;
7. Python compile, relevant tests, frontend type check, and export checks pass;
8. Executive Summary states actual/nowcast/forecast periods and the exact accuracy scope;
9. Model Registry and Data Contract are updated when behavior changes.
