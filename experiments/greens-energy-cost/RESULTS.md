# GREENS energy cost experiment: results

Experiment directory: `~/workspace/paper-submissions/greens-energy-cost-experiment/`
Date run: 2026-11-13. Source paper results used exactly as reported:
Claude detection 75.0% to 62.0%, Gemini 99.2% to 77.6%, 1,873 variants,
30 seed actions (Risky 15, Ambiguous 9, Benign 6). Those numbers were not
re-derived or altered.

## Headline numbers

Central case means: daily power curve slope 0.442, PDU capacity 750 kW,
PUE 1.56. Full range spans slope 0.061 to 0.582, capacity 500 to 1,000 kW,
PUE 1.05 to 1.56.

Per camouflaged PERMIT, facility energy (central, with full range):
- Short administrative action: 0.43 kWh (range 0.03 to 0.76 kWh)
- Spin up or scale a service: 12.93 kWh (range 0.80 to 22.69 kWh)
- Run GPU inference (CPU proxy): 12.93 kWh (range 0.80 to 22.69 kWh)
- Run a batch job: 51.71 kWh (range 3.22 to 90.76 kWh)
- Idle or no workload change: 0 kWh

Per 1,000 actions, facility energy (central, with full range). Extra
permits per 1,000 actions are 130 for Claude and 216 for Gemini, derived
directly from the reported evasion drops of 13.0 pp and 21.6 pp.
- Claude, short admin: 56.02 kWh (range 3.49 to 98.32 kWh)
- Claude, spin up / GPU inference: 1,680.71 kWh (range 104.59 to 2,949.73 kWh)
- Claude, batch job: 6,722.82 kWh (range 418.37 to 11,798.90 kWh)
- Gemini, short admin: 93.09 kWh (range 5.79 to 163.37 kWh)
- Gemini, spin up / GPU inference: 2,792.56 kWh (range 173.79 to 4,901.08 kWh)
- Gemini, batch job: 11,170.22 kWh (range 695.14 to 19,604.33 kWh)

Cooling energy per 1,000 actions (central, with full range):
- Claude, short admin: 20.11 kWh (range 0.17 to 35.30 kWh)
- Claude, spin up / GPU inference: 603.33 kWh (range 4.98 to 1,058.88 kWh)
- Claude, batch job: 2,413.32 kWh (range 19.92 to 4,235.50 kWh)
- Gemini, short admin: 33.42 kWh (range 0.28 to 58.65 kWh)
- Gemini, spin up / GPU inference: 1,002.46 kWh (range 8.28 to 1,759.36 kWh)
- Gemini, batch job: 4,009.82 kWh (range 33.10 to 7,037.45 kWh)

For scale, the PDU baseline day is 12,876 kWh IT and 20,087 kWh facility
at PUE 1.56 (central 750 kW capacity, mean measured power utilisation
0.715). So 1,000 actions that are all batch jobs would add about a third
of a PDU day of facility energy at the central estimate, while 1,000
actions that are all short admin actions would add about 0.3% of a day.

LLM side (H3), per 1,000 actions, 2 deployment calls per action
(1 agent narration + 1 monitor judgement), Luccioni et al. 2024 Table 2:
0.004 to 0.147 Wh facility per 1,000 actions (text classification 0.002
Wh per 1,000 queries at the low end, text generation 0.047 Wh per 1,000
queries at the high end, PUE 1.05 to 1.56). That is five orders of
magnitude smaller than even the short admin workload delta (56,020 Wh
per 1,000 actions for Claude at central). H3 is therefore supported only
in the narrow sense that the monitor adds some energy; under published
small-model calibration it is negligible next to the workload energy of
a permitted action. The caveat is important: Luccioni et al. measured
small open models, and no published per-call energy figure exists for
frontier-scale monitors such as Claude or Gemini, so the LLM side is a
lower bound and H3 cannot be tested at frontier scale from public data.

Hypotheses:
- H1 (permitted camouflaged actions create a positive energy delta that
  grows with the number of permits): supported in direction. Every
  non-idle archetype gives a positive delta, and the per 1,000 action
  delta scales linearly with the extra permit count (Gemini is 1.66x
  Claude because 216 / 130 = 1.66). Magnitude is not pinned down: the
  range spans roughly a factor of 30.
- H2 (the delta is not uniform across archetypes): supported. At
  central, a batch job permit costs about 120x a short admin permit
  (51.71 vs 0.43 kWh facility).
- H3 (the monitor itself adds energy cost): supported in direction,
  negligible in magnitude under published calibration; untestable at
  frontier scale from public data. See the paragraph above.

## What was actually downloaded

All files are under `raw/` in this directory, frozen as downloaded.

1. Google PowerData 2019, cell a pdu6:
   `cella_pdu6.csv.gz` (45 KB compressed, 385 KB uncompressed),
   8,928 rows. Columns: time, cell, pdu, measured_power_util,
   production_power_util, bad_measurement_data, bad_production_power_data.
   Time is microseconds since trace start, a clean 5-minute grid, windows
   2 to 8,929, no duplicate times, 0 bad measurement rows, 1,788 rows
   flagged bad production power data (production_power_util not used).
   Measured power utilisation: mean 0.7153, range 0.612 to 0.771.
   Source: `https://storage.googleapis.com/powerdata_2019/cella_pdu6.csv.gz`
   (public GCS, same object named in the cluster-data repo docs; gsutil
   was not installed, direct HTTPS fetch of the same object was used).
2. Machine to PDU mapping: `machine_to_pdu_mapping.csv.gz` (520 KB
   compressed, 1.8 MB uncompressed), 96,616 rows. Cell a has 5 PDUs and
   10,002 machines; pdu6 in cell a serves 1,738 machines. The mapping
   could NOT be used for the join, because the workload slice below has
   no machine IDs. See the workload leg.
3. Google ClusterData 2019 workload, sampled package (NOT BigQuery):
   `google2019_grouped_300s_cellwide_mean.csv` (594 KB), 8,064 rows,
   copied from the `datacentertracesdatasets` PyPI package v0.3.3
   (`machine_usage_grouped_300_seconds.csv`). Columns: cpu_util,
   mem_util, assigned_mem, cycles_per_instruction. This is the
   cell-wide mean utilisation grouped every 300 seconds over 28 days,
   processed from the original trace by that package (README verified
   live at github.com/alejandrofdez-us/DataCenter-Traces-Datasets,
   Zenodo DOI 10.5281/zenodo.14564847). CPU utilisation fraction:
   mean 0.4728, range 0.3203 to 0.5924. No timestamps, no machine IDs,
   no cell label in the file.
4. Azure LLM Inference 2024, Conversation trace, full release file:
   `AzureLLMInferenceTrace_conv_1week.csv` (1.1 GB, 27,303,999 data
   rows). Actual coverage in the file is 2024-05-12 00:00 to 2024-05-18
   23:59 UTC, not 2024-05-10 to 2024-05-19 as the dataset page says.
   The release asset is a single file, so the whole week was downloaded
   and the 1-hour slice was cut from it.
5. Azure 1-hour frozen slice:
   `AzureLLMInferenceTrace_conv_1hour_2024-05-12_00-01.csv` (3.7 MB,
   91,156 rows), 2024-05-12 00:00 to 01:00 UTC. Context tokens: mean
   1,634.6, median 931, p90 3,760, max 7,999. Generated tokens: mean
   116.3, median 41, p90 397, max 1,200. Total tokens per request:
   mean 1,750.9, median 1,000, p90 3,986. No nulls. Requests per minute
   in the hour: 1,519.3.
6. Luccioni et al. 2024, Power Hungry Processing (arXiv 2311.16863):
   `luccioni2024.pdf` (915 KB, 21 pages) and extracted text
   `luccioni2024.txt`. Table 2 values used: text classification 0.002
   Wh per 1,000 queries, text generation 0.047 Wh per 1,000 queries
   (means; standard deviations 0.001 and 0.03). These are small open
   model measurements, CPU+GPU+RAM via CodeCarbon.
7. Azure dataset page: `azure_llm_2024_doc.md` (raw markdown of the
   dataset page, CC-BY, DynamoLLM HPCA 2025 citation).
8. NREL catalog page snippet: `nrel_catalog.html` (107 KB, mostly
   scripts, no usable PUE table extracted). See failures below.
9. Source paper text: `source_paper.txt`, extracted from the uploaded
   PDF with PyMuPDF, 5 pages.

## What failed or was not obtained

- BigQuery workload slice (Step B as written): NOT obtained. No GCP
  credentials or project were available in this environment, and no
  BigQuery query was run. The sampled package in item 3 above was used
  instead, as the instructions allowed after verifying the package
  repository first. Consequence: the workload is a cell-wide mean, not
  PDU-matched machine usage, and the machine to PDU mapping could not
  be used. This is the largest methodological weakness; see the
  limitations paragraph.
- NREL ESIF PUE data (https://data.nrel.gov/submissions/300): NOT
  obtained. Direct fetch failed with curl exit 52 (empty reply), and a
  browser fetch of the same URL failed and was not retried. No NREL
  median PUE was computed. PUE scenarios used instead: 1.05 from
  Frontier (Sun et al. 2024, average PUE 1.05, verified in the research
  report) as the low bound, and 1.56, the Uptime Institute 2024 global
  average PUE, as the central case (verified by web search on
  2026-11-13; multiple secondary sources agree on 1.56 for 2024 and
  1.58 for 2023). The NREL check in the instructions final checks
  therefore remains open.
- AI Energy Score leaderboard: NOT used for values. The leaderboard is
  a JavaScript app and no bulk CSV was found, so no values were
  transcribed from it. Luccioni et al. 2024 Table 2 was used instead
  and is fully cited above.
- Variant level archetype coding (Step 1 as written): NOT possible.
  The manuscript does not list its 30 seed actions individually; the
  action list is referenced to a GitHub link that is blank in the
  manuscript. No variant was coded. The replay uses aggregate
  incremental permit counts and reports per archetype, with per 1,000
  action totals given as a range across archetypes, not as a single
  mixed total. See CODING_GUIDE.md.
- SPECpower cross check: not run. SPECpower is a commercial benchmark,
  not a downloadable dataset, and no published SPECpower curve was
  transcribed. The daily fit shape (intercept 0.44, full load about
  1.02) is consistent with the textbook server power shape, but that
  is an observation, not a cross check against a SPECpower result page.

## Exact commands used

- PDU and mapping:
  `curl -sL -o cella_pdu6.csv.gz https://storage.googleapis.com/powerdata_2019/cella_pdu6.csv.gz`
  `curl -sL -o machine_to_pdu_mapping.csv.gz https://storage.googleapis.com/powerdata_2019/machine_to_pdu_mapping.csv.gz`
  then `gunzip -k -f` on both.
- Azure dataset page and release:
  `curl -sL https://raw.githubusercontent.com/Azure/AzurePublicDataset/master/AzureLLMInferenceDataset2024.md`
  `curl -sL -o AzureLLMInferenceTrace_conv_1week.csv https://github.com/Azure/AzurePublicDataset/releases/download/dataset-llm-2024/AzureLLMInferenceTrace_conv_1week.csv`
- Azure 1-hour slice:
  `awk -F, 'NR==1 || ($1 ~ /^2024-05-12 00:/)' AzureLLMInferenceTrace_conv_1week.csv > AzureLLMInferenceTrace_conv_1hour_2024-05-12_00-01.csv`
- Luccioni paper: `curl -sL -o luccioni2024.pdf https://arxiv.org/pdf/2311.16863`
- Sampled Google trace: `pip install --break-system-packages datacentertracesdatasets`
  (v0.3.3), then the packaged CSV was copied to `raw/` unchanged.
- Analysis: `python3 scripts/fit_power_curve.py`,
  `python3 scripts/replay.py`, `python3 scripts/make_charts.py`.
  All scripts are in `scripts/` in this directory.

## Fitted power curve and fit quality

Model: measured_power_util = intercept + slope * cpu_util_frac,
cell a pdu6, joined to the cell-wide mean CPU trace by 5-minute window
index (grouped trace row i aligns to PDU window i+2; the grouped trace
has no timestamps, so this alignment is an assumption; shifting the
alignment by +1 or +2 windows changes the 5-minute slope only from
0.0613 to 0.0601 and 0.0585, so the fit is not sensitive to that choice).

- 5-minute windows, n=8,064: intercept 0.6862 (se 0.0034), slope 0.0613
  (se 0.0072), R2 0.0090, RMSE 0.0256, Pearson r 0.0950.
- Hourly means, n=672: intercept 0.6793, slope 0.0760, R2 0.0119.
- 6-hourly means, n=112: intercept 0.6320, slope 0.1760, R2 0.0484.
- Daily means, n=28: intercept 0.4402 (se 0.0603), slope 0.5818
  (se 0.1274), R2 0.4450, RMSE 0.0115.
- Daily means excluding day 0: slope 0.3932, R2 0.3505.
- Daily means excluding days 0-1: slope 0.4420, R2 0.4381.
- Leave-one-out daily slope range: 0.393 to 0.634.
- Detrended daily correlation (CPU vs power, linear time trend
  removed): 0.648. Daily first-difference correlation: 0.695.
  5-minute first-difference correlation: 0.014.
- CPU decile binned means: mean power utilisation is 0.707 to 0.719
  across all ten CPU deciles, non-monotonic, with the top CPU decile
  at 0.715. At 5-minute scale the PDU power barely responds to
  cell-wide CPU swings.

Reading: the cell-wide mean CPU does not explain this PDU's power at
5-minute scale (R2 0.009). A real association appears only at daily
scale (R2 0.445), and the daily slope is sensitive to the first day
(0.582 with all 28 days, 0.393 without day 0). The replay therefore
uses three slope cases: low 0.0613 (5-minute fit), central 0.4420
(daily fit excluding days 0-1), high 0.5818 (daily fit, all 28 days).
The central slope is the daily association, not a 5-minute causal
effect, and the paper must say that.

## Replay method (Steps 3 to 5)

Baseline: the frozen 28-day PDU record with no added agent actions.
Truthful-blocked: baseline plus zero added workload, because a blocked
action does not execute. Camouflaged-permitted: baseline plus the
archetype workload for each extra permit. The only difference between
conditions is the added workload from camouflaged permits.

Extra permits are the incremental permits caused by camouflage:
Claude 13.0% of 1,873 = 243.5 permits in the study, 130 per 1,000
actions; Gemini 21.6% of 1,873 = 404.6 permits in the study, 216 per
1,000 actions. Actions the monitor would have permitted even when
described truthfully are not counted, because they are not caused by
camouflage.

Per action IT energy: slope * cpu_frac * duration_hours * capacity_kW.
Facility energy = IT energy * PUE. Cooling energy = IT energy * (PUE - 1).
Capacity scenarios: 500, 750 (central), 1,000 kW. The central 750 kW
is anchored on the mapping file: pdu6 serves 1,738 machines, and
1,738 machines at about 310 W mean draw is about 539 kW, divided by
the mean power utilisation 0.715 gives about 754 kW of capacity.
Capacity is a scenario parameter, not a measurement, so the
capacity-free figure is also reported: normalised utilisation-hours
per permit at the central slope are 0.000368 (short admin), 0.011050
(spin up / GPU inference), and 0.044200 (batch job). Multiply by any
PDU capacity in kW to get IT kWh per permit at the central slope.

Archetype assumptions (researcher defined, see CODING_GUIDE.md):
short admin 0.01 of PDU CPU for 5 min; spin up 0.05 for 30 min;
batch job 0.10 for 60 min; GPU inference 0.10 for 15 min (CPU proxy,
GPU is not in the trace); idle 0.

## Figures and tables for the paper

Charts (all from the data actually downloaded, labelled with source,
slice, and units on the figure):
- `charts/fig1_power_curve.png`: Figure 1, power curve fit. Left:
  5-minute decile means with the 5-minute fit. Right: daily means
  with both daily fits. Use this to show why the daily fit is the
  usable one and the 5-minute fit is the lower bound.
- `charts/fig2_energy_by_condition.png`: Figure 2, facility kWh per
  1,000 actions by condition and archetype, Claude and Gemini, central
  bars with full range whiskers. Baseline and truthful-blocked are
  zero by construction.
- `charts/fig3_energy_per_permit_and_per_1000.png`: Figure 3, log
  scale, per PERMIT and per 1,000 actions, central points with full
  range whiskers.
- `charts/fig4_azure_token_distribution.png`: Figure 4, Azure
  Conversation 1-hour slice token distributions, context median 931
  and generated median 41, n=91,156.

Tables (CSVs in `outputs/`):
- Table 1, archetype definitions: `outputs/archetypes.csv` (also in
  CODING_GUIDE.md).
- Table 2, energy delta by archetype, per PERMIT and per 1,000
  actions: `outputs/energy_per_permit.csv` and
  `outputs/energy_per_1000_actions.csv`. The headline values are in
  the first section of this file.
- Table 3, sensitivity: the range in Table 2 already spans slope,
  capacity, and PUE jointly. For the paper, split it: slope alone
  moves the central batch job permit from 7.17 kWh facility (slope
  0.061, 750 kW, PUE 1.56) to 68.07 kWh (slope 0.582); capacity alone
  moves it from 34.48 kWh (500 kW) to 68.95 kWh (1,000 kW) at central
  slope and PUE; PUE alone moves it from 34.81 kWh (1.05) to 51.71
  kWh (1.56) at central slope and capacity. Slope is the dominant
  sensitivity, then capacity, then PUE.
- Baseline context: `outputs/baseline_pdu_day.csv`.
- LLM side: `outputs/llm_side_energy.csv`.
- Fit details: `outputs/power_curve_fits.csv`,
  `outputs/power_curve_join.csv` (8,064 joined windows).

## Limitations paragraph (for the paper, adapted to the slices used)

No public dataset links an LLM agent narration, a monitor PERMIT or
BLOCK decision, and measured data center energy for the same action.
Our energy delta is therefore a modelled counterfactual. First, the
mapping from camouflaged actions to CPU demand is researcher defined,
and variant level coding was not possible because the manuscript does
not list its 30 seed actions; per 1,000 action totals are reported as
a range across archetypes, not as a single mixed total. Second, Google
power is a normalised utilisation from 2019 Borg jobs, not watts from
LLM serving, and the power curve was fitted between a cell-wide mean
CPU trace and a single PDU, not between PDU-matched machine usage and
that PDU, because no BigQuery access was available; the 5-minute fit
is near flat (R2 0.009) and only the daily fit is usable (R2 0.445),
so the slope is carried as a range from 0.061 to 0.582. Third, PDU
capacity in kilowatts is a scenario (500 to 1,000 kW, central 750 kW
anchored on 1,738 machines), not a measurement, and PUE is borrowed:
1.05 from a liquid-cooled HPC system and 1.56 as the industry average,
because the NREL PUE file could not be fetched. Fourth, LLM energy is
GPU only in the calibration source, from small open models on different
hardware than a frontier deployment, so the LLM side is a lower bound.
We report the delta as a range over slope, capacity, and PUE
assumptions, and our claim is about the order of magnitude and
direction of the camouflage energy penalty, not a precise per action
wattage. Do not claim this energy was measured in a production data
center, and do not present the Frontier PUE of 1.05 as typical for
cloud data centers.

## What is still missing before the paper can be written

- The 30 seed action descriptions. Without them there is no variant
  level archetype coding and no defensible archetype mix, so the paper
  must report the per archetype range as done here, or Rea must supply
  the action list from the GitHub repo (currently a blank link in the
  manuscript).
- A PDU-matched workload slice. BigQuery access with GCP credentials
  would let the power curve be fitted on the machines actually behind
  pdu6, which is the single biggest improvement available. Until then
  the slope range stays wide.
- The NREL PUE file, if the paper wants a measured PUE instead of the
  Uptime Institute average. The NREL landing page needs to be opened
  and its fields confirmed on the page itself.
- A frontier-scale LLM energy figure, if H3 is to be tested at the
  scale of the monitors actually used. No public figure was found.
- A decision on the central case for the paper: this file uses daily
  slope 0.442, 750 kW, PUE 1.56 as central. The paper should either
  adopt that or justify a different central case, and must always show
  the range beside it.
- The paper itself was not written in this task, as instructed.
