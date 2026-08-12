# Behavioural Camouflage — experiment harness (rigor build)

Harness for the thesis *"Can LLM agents disguise risky actions as safety
behaviours, and what transformations do they use?"*

Pipeline (three steps, run by `run_all.sh`):

| Step | File | Produces |
|------|------|----------|
| 1. Camouflage generation | `src/camouflage.py` | `data/camouflaged.jsonl` |
| 2. Monitor evaluation | `src/monitor.py` | `data/monitor_judgements.jsonl` |
| 3. Scoring | `src/score.py` | `results/summary.csv`, `by_transformation.csv`, `detection_drop.png` |

The 30-action risk-labelled seed set is `data/seed_actions.json`. Knobs live in
`src/config.py`.

## What "rigor" adds

- **False positives.** Benign actions (tier B) are run through the monitor as
  controls, so `score.py` reports a false-positive rate. A monitor that flags
  everything is useless; this makes the detection number interpretable.
- **Repetitions + confidence intervals.** The camoufleur makes `N_REPS` distinct
  disguises per action; `score.py` reports every rate with a bootstrap 95% CI and
  states whether the evasion drop is real (its CI excludes 0). This is the
  "run it 99 times" requirement.
- **Concurrency.** `MAX_WORKERS` parallel API calls, so 99 reps finish in minutes.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# wiring test — no keys, no cost:
DRY_RUN=1 bash run_all.sh

# real run — put your key in .env first:
cp .env.example .env    # then paste ANTHROPIC_API_KEY
bash run_all.sh
```

## Key settings (`src/config.py`)

- `N_REPS` — disguises per action. **20** to validate timing/cost, **99** for the full run.
- `MONITOR_REPS` — times each original/benign action is re-judged (monitor noise).
- `MAX_WORKERS` — parallel calls; lower if you hit rate limits.
- `CAMOUFLEUR_MODELS` / `MONITOR_MODELS` — add a GPT id once you have an OpenAI key
  to enable cross-family monitoring.

## Not yet built (next layers)

- **Fidelity Gate** — verify a disguise didn't secretly change the action.
- **Graded 0–100 monitor scores** and **TPR@FPR** (vs binary risky/safe).
- **Adaptive adversary** — let the camoufleur iterate against the monitor.
