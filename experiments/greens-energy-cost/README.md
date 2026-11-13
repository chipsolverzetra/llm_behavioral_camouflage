# GREENS energy cost experiment

Energy cost of behavioural camouflage in data center operations, for GREENS'27 (emerging research, deadline 2026-11-20).

## What this is

Study 1 (this repo, main): narration-gated monitors, Claude detection 75.0% to 62.0%, Gemini 99.2% to 77.6%, 1,873 variants of 24 risky and ambiguous seed actions.

Study 2 (this branch): replay the extra permits caused by camouflage (130 per 1,000 actions for Claude, 216 for Gemini) through a power curve fitted to Google ClusterData 2019 and PowerData 2019, with PUE scenarios.

## Headline results (central case: daily slope 0.442, 750 kW PDU, PUE 1.56)

- Per camouflaged PERMIT, mixed facility energy: 12.68 kWh (range 0.79 to 22.25 kWh)
- Per 1,000 actions, mixed facility energy: Claude 1,648.02 kWh (102.56 to 2,892.37), Gemini 2,738.26 kWh (170.41 to 4,805.78)
- Cooling per 1,000 actions: Claude 591.60 kWh, Gemini 982.96 kWh
- Batch actions are 20.8% of the camouflaged mix and 85.0% of the energy

## Files

- `RESULTS.md` - first run, per-archetype ranges
- `RESULTS-v2-seed-coded.md` - seed-coded re-run with the single mixed total
- `scripts/` - power curve fit, replay, chart scripts
- `outputs/` and `outputs-v2/` - fit and energy tables (CSV)
- `charts/` and `charts-v2/` - figures

## Data (not committed)

Raw downloads are not in this repo: Google PowerData 2019 cell a PDU 6, the sampled ClusterData 2019 cell-wide CPU trace, and the Azure LLM Inference Dataset 2024 Conversation trace (1-hour frozen slice, 91,156 requests). See `RESULTS.md` for exact sources, files, and commands.

## Limitations

The energy delta is a modelled counterfactual, not a production measurement. See the limitations paragraph in `RESULTS-v2-seed-coded.md`.
