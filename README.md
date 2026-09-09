# Behavioral Camouflage — experiment harness (rigor build)

Harness for the thesis *"Can LLM agents disguise risky actions as safety
behaviors, and what transformations do they use?"*

An agent that narrates its own actions to an oversight monitor can reword a
risky action so the monitor reads it as routine. The execution semantics do not
change. Only the description does. This repo measures how far that gets you
against two frontier monitors.

Accompanying paper: *Behavioral Camouflage in LLM Agent Oversight: Evaluating
Narration-Gated Monitors Under Descriptive Reframing* (in submission).

## Headline results

N=99 disguises per action, 1,873 valid variants, generated once and reused
across both monitors.

| Monitor | Original detection | Camouflaged detection | Evasion drop | 95% CI | Control FPR |
|---|---|---|---|---|---|
| Claude Sonnet 5 | 75.0% | 62.0% | 13.0 pp | [4.8, 21.0] | 0% |
| Gemini 3 Flash | 99.2% | 77.6% | 21.6 pp | [18.9, 24.0] | 0% |

Both drops exclude zero. Neither monitor false-alarmed on benign controls
(0/30 judgements each, rule-of-three upper bound ~10%).

Gemini is the more interesting row. It caught 99.2% of plain risky actions and
still lost 21.6 points once they were reframed. A better detector is not a safe
detector.

### Detection by disguise family

Lower detection = the disguise works better.

| Disguise family | n | Claude Sonnet 5 | Gemini 3 Flash |
|---|---|---|---|
| Goal recontextualization | 266 | **59.0%** | **71.4%** |
| Register / stylistic elevation | 1,677 | 60.2% | 77.6% |
| Safety rationale wrapping | 1,559 | 63.5% | 76.9% |
| Lexical softening / euphemism | 1,779 | 63.7% | 79.1% |
| Selective omission / abstraction | 233 | 64.4% | 80.3% |
| Framing inversion | 28 | 75.0% | 75.0% |

Goal recontextualization is rank 1 on both monitors. Below that the ordering
does not transfer — framing inversion is last against Claude and second against
Gemini. Note its n is only 28, so treat that rank cautiously.

Tags are non-exclusive; counts sum to more than 1,873 because most variants use
several techniques at once.

### By risk tier (Gemini)

| Tier | Original | Camouflaged | Drop |
|---|---|---|---|
| R (destructive) | 100.0% | 93.0% | 7.0 pp |
| A (ambiguous) | 97.8% | 59.0% | 38.8 pp |

Ambiguous actions are where disguise bites hardest.

## Pipeline

Three steps, run by `run_all.sh`:

| Step | File | Produces |
|------|------|----------|
| 1. Camouflage generation | `src/camouflage.py` | `data/camouflaged.jsonl` |
| 2. Monitor evaluation | `src/monitor.py` | `data/monitor_judgements.jsonl` |
| 3. Scoring | `src/score.py` | per-monitor summary and by-transformation CSVs in `results/` |

Figures are built separately by `make_figures.py` and `make_comparison_figure.py`.

The 30-action risk-labelled seed set is `data/seed_actions.json`. Knobs live in
`src/config.py`.

## What "rigor" adds

- **False positives.** Benign actions (tier B) are run through the monitor as
  controls, so `score.py` reports a false-positive rate. A monitor that flags
  everything is useless; this makes the detection number interpretable.
- **Repetitions + confidence intervals.** The camoufleur makes `N_REPS` distinct
  disguises per action; `score.py` reports every rate with a bootstrap 95% CI
  (2,000 resamples, fixed seed) and states whether the evasion drop is real (its
  CI excludes 0). This is the "run it 99 times" requirement.
- **Concurrency.** `MAX_WORKERS` parallel API calls, so 99 reps finish in minutes.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# wiring test — no keys, no cost:
DRY_RUN=1 bash run_all.sh

# real run — put your keys in .env first:
cp .env.example .env    # then paste ANTHROPIC_API_KEY and GEMINI_API_KEY
bash run_all.sh
```

Both keys are needed for the full cross-vendor run. See `.env.example` for the
exact variable names.

## Key settings (`src/config.py`)

- `N_REPS` — disguises per action. **20** to validate timing/cost, **99** for the full run.
- `MONITOR_REPS` — times each original/benign action is re-judged (monitor noise).
- `MAX_WORKERS` — parallel calls; lower if you hit rate limits.
- `CAMOUFLEUR_MODELS` / `MONITOR_MODELS` — add a GPT id once you have an OpenAI key
  to enable cross-family monitoring.

## Models used

- **Camoufleur:** Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- **Monitors:** Claude Sonnet 5, Gemini 3 Flash

Claude Sonnet 5 was tried as the camoufleur first and refused the role for
explicitly destructive actions, citing misuse potential. That refusal was not
circumvented; Sonnet 4.5 was used instead. The divergence is reported in the
paper as a finding rather than worked around.

## Reproducing the published numbers

The committed results in `results/` are the N=99 run reported in the paper. To
regenerate from scratch, set `N_REPS = 99` and run the full pipeline with both
keys. Expect the numbers to move by a fraction of a point — the camoufleur is
sampled at API defaults, so a fresh corpus is not identical to ours. The
committed `data/camouflaged.jsonl` is the exact corpus behind the table above;
use it to reproduce the scoring exactly.

## Responsible use

This repository contains a working corpus of 1,873 action descriptions that
measurably evade two production oversight monitors. It is published for
reproducibility of a defensive result: the weakness it documents is a property
of narration-only monitoring, not a novel exploit, and defenders cannot evaluate
mitigations against an attack they cannot run.

Intended uses: evaluating and hardening oversight monitors, red-teaming agent
scaffolds you own or are authorized to test, and replicating or extending the
published results.

Not intended: deploying these transformations against systems you do not own or
have permission to test, or building them into an agent to evade a monitor in
production.

No vendor was notified prior to release. The behavior is a documented weakness
class in narration-gated oversight rather than an implementation flaw in any
one product, and both monitors remain effective on unmodified inputs.

Nothing in this harness executes any action. The seed set describes operations
in text only; the monitor reads descriptions and returns a classification.

## Not yet built (next layers)

- **Fidelity Gate** — verify a disguise didn't secretly change the action.
- **Graded 0–100 monitor scores** and **TPR@FPR** (vs binary risky/safe).
- **Adaptive adversary** — let the camoufleur iterate against the monitor.

The last one matters most for reading these results. Our adversary is static and
blind: it never sees a verdict and never revises. Every number here is a floor.

## Citation

```bibtex
@misc{ara2026camouflage,
  author = {Ara, Rea and Torrens, Paul},
  title  = {Behavioral Camouflage in LLM Agent Oversight},
  year   = {2026},
  note   = {Tandon School of Engineering, New York University},
  url    = {https://github.com/chipsolverzetra/llm_behavioral_camouflage}
}
```

## License

Code is released under the MIT License. Data and results are released under
CC BY 4.0. See `LICENSE`.
