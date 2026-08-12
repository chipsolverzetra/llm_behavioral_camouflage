# Running your thesis experiments on Google Cloud — a from-zero runbook

**For:** the *behavioural camouflage* thesis (camouflage → monitor → scoring pipeline)
**Assumes:** no Google Cloud account, no code written yet (both now handled).
**Prepared:** August 2026.

---

## 0. The short version (read this first)

**Recommendation: run API-only on one small CPU virtual machine (VM). Do not rent a GPU yet.**

Your experiment is a *text-only harness*: an agent rewrites a risky action to read as safe, a monitor judges it, you score the gap. That is orchestration of LLM calls, not heavy computation. The frontier models your thesis centres on (GPT, Claude) can *only* be reached by API anyway — you cannot self-host them. And the open-weight models it references (Qwen, Llama) can also be reached by API through a hosted provider, so you still don't need a GPU.

Two facts about the free trial make this decision for you. During the Google Cloud **free trial you cannot attach GPUs, cannot request quota increases, and cannot use third‑party "model‑as‑a‑service" partner models** — those unlock only after you upgrade to a paid billing account ([Google Cloud free program docs](https://docs.cloud.google.com/free/docs/free-cloud-features)). So the only sensible free-trial path is: a cheap CPU VM that runs your Python, which calls the model APIs directly with your own OpenAI/Anthropic keys. Those API calls are billed by OpenAI/Anthropic, *not* by Google Cloud, so the trial restrictions never touch them.

**When you would add a GPU (later, optional):** only if the stretch-goal detector needs token-level perplexity / log-probs from an open model you host yourself. At that point you upgrade to a paid account and rent an L4 — about **$0.70/hr on‑demand, ~$0.07/hr on Spot** ([GCP GPU pricing](https://www.thundercompute.com/blog/google-cloud-gpu-instances)). Even then, a hosted open-model API is usually cheaper and simpler than self-hosting. Treat the GPU as a decision you defer, not one you make now.

**On your professor's "2 VMs — my stuff vs Claude" note:** that is a *reproducibility* check, not a compute requirement. You build one VM, get the pipeline working, then clone it to an identical second VM and run an independent ("mirror") implementation of the same experiment. If both implementations produce the same detection-drop, the effect is real and not an artefact of one code path or of stochastic noise (his "is it my variable change or stochastic?" concern). Section E covers this.

**Rough cost:** the CPU VM is ~$0.07/hr (~$49/mo if left on) and is covered by the $300 free credit; if you **stop it when idle**, a pilot month is a few dollars. Your real spend is model API tokens — a pilot over 24 risky/ambiguous actions is single-digit dollars.

---

## 1. What you are about to build

```
Your laptop ──ssh──▶  GCP CPU VM (e2-standard-2, Debian)
                         │  runs your Python pipeline
                         │
                         ├─▶ Anthropic API  (Claude as camoufleur / monitor)
                         ├─▶ OpenAI API      (GPT as camoufleur / monitor)
                         └─▶ (optional) hosted open-model API (Llama/Qwen)
                         │
                         ▼
                    results/  ──scp──▶  back to your laptop → into the thesis
```

The VM is just a rented Linux computer that stays on and runs your batches while your laptop is closed. Nothing about the science requires the cloud — the cloud gives you a stable, reproducible, always-on box (and satisfies the 2-VM design).

---

## 2. Part A — Create your Google Cloud account (from zero)

1. Go to **https://console.cloud.google.com** and sign in with a Google account. Your NYU Google account (`tra9226@nyu.edu`) works; a personal Gmail works too. *Tip: check whether NYU or your department already has GCP credits or a billing account for students before you burn the personal free trial — ask your advisor or NYU IT. If they do, you can skip the free trial and use that billing account instead.*

2. Click **Start free** / **Activate**. You will:
   - accept the terms,
   - enter a payment method (required for identity; you are **not** charged when the trial ends — it pauses rather than auto-billing),
   - receive **$300 in credit, valid for 90 days**.

3. **Create a project.** Top bar → project dropdown → **New Project**. Name it e.g. `thesis-camouflage`. A project is just a container for your resources and billing. Wait for it to be created, then select it.

4. **Enable the Compute Engine API.** Search bar → "Compute Engine" → **Enable** (takes a minute the first time).

---

## 3. Part B — Create the VM

### Option 1 — Console (click-through, easiest first time)

1. Menu (☰) → **Compute Engine** → **VM instances** → **Create instance**.
2. **Name:** `camo-vm`.
3. **Region / zone:** pick one close to you, e.g. `us-east1` / `us-east1-b`.
4. **Machine configuration:** series **E2**, machine type **e2-standard-2** (2 vCPU, 8 GB). This is plenty for API orchestration. (You can start even smaller with `e2-small` and resize later.)
5. **Boot disk:** click **Change** → **Debian 12** (or Ubuntu 24.04 LTS), size **30 GB**, standard persistent disk.
6. Leave firewall boxes unchecked (you don't need inbound HTTP).
7. **Create.** In ~30 seconds the instance is running.

### Option 2 — One command (gcloud CLI)

If you install the [gcloud CLI](https://cloud.google.com/sdk/docs/install) locally, the same VM is one command:

```bash
gcloud compute instances create camo-vm \
  --project=thesis-camouflage \
  --zone=us-east1-b \
  --machine-type=e2-standard-2 \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-size=30GB
```

> Prefer the console for your first VM so you see the options; use the CLI once you know what you want (it's also how you'll clone for the 2-VM step).

### Connect to it

- **Console:** on the VM row, click **SSH**. A browser terminal opens — no keys to manage. This is the simplest.
- **CLI:** `gcloud compute ssh camo-vm --zone=us-east1-b`

You are now on the VM's command line.

---

## 4. Part C — Set up the pipeline on the VM

Run these **on the VM** (in the SSH window).

```bash
# 1. System packages
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip git tmux unzip

# 2. Get the code onto the VM. Two options:
#    (a) if you push the provided repo to GitHub:
#        git clone https://github.com/<you>/camouflage-experiments.git
#    (b) or upload the zip I gave you via the SSH window's gear menu
#        (⚙ "Upload file"), then:
unzip camouflage-experiments.zip -d ~ && cd ~/camouflage-experiments

# 3. Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Wiring test FIRST — no keys, no cost. Confirms everything connects:
DRY_RUN=1 ./run_all.sh
# You should see a summary table and "DONE. See results/".
```

### Add your API keys (safely)

```bash
cp .env.example .env
nano .env        # paste your real keys, save with Ctrl-O, exit Ctrl-X
```

Your keys live only in this file on the VM. `.env` is already in `.gitignore` so it can never be committed. Get keys from the provider dashboards:
- Anthropic: https://console.anthropic.com → API keys (add a few dollars of credit)
- OpenAI: https://platform.openai.com → API keys

Open `src/config.py` and set the model ids to models you actually have access to, and set **`REPS = 1`** for the first real run (a cheap smoke test).

### Run the real pilot

```bash
source .venv/bin/activate
./run_all.sh
```

For the **full run** (raise `REPS` to 5–10; wider model lists), start it inside `tmux` so it keeps running after you close your laptop:

```bash
tmux new -s run          # start a named session
./run_all.sh             # let it run
# detach: Ctrl-b then d   → you can now close everything
# later: gcloud/console SSH back in, then:  tmux attach -t run
```

---

## 5. Part D — Get results off the VM

Your outputs land in `~/camouflage-experiments/results/` (CSVs + the `detection_drop.png` chart). Pull them to your laptop:

```bash
# from your LAPTOP (needs gcloud CLI):
gcloud compute scp --recurse \
  camo-vm:~/camouflage-experiments/results ./results \
  --zone=us-east1-b
```

Or, in the browser SSH window, use the gear menu ⚙ → **Download file** and give the path `camouflage-experiments/results/summary.csv` (one file at a time).

---

## 6. Part E — The "2 VMs" reproducibility check (your professor's note)

The goal: show the detection-drop is a real effect, not an artefact of one implementation or of model randomness.

1. Get VM #1 fully working and committed (results saved).
2. **Snapshot it into an image**, then create VM #2 from that image so the environment is byte-identical:
   ```bash
   gcloud compute instances stop camo-vm --zone=us-east1-b
   gcloud compute images create camo-image \
     --source-disk=camo-vm --source-disk-zone=us-east1-b
   gcloud compute instances create camo-vm-2 \
     --zone=us-east1-b --machine-type=e2-standard-2 \
     --image=camo-image
   ```
3. On **VM #1** run *your* implementation. On **VM #2** run the **mirror implementation** — the same experiment written independently (e.g. have Claude re-implement the pipeline from the spec without seeing your code). Same seed set, same models, same `REPS`.
4. Compare `results/summary.csv` from both. Matching detection-drops across two independent implementations = the result is real. Divergence tells you exactly where an implementation choice is driving the number.

This directly answers his "999 times / is it stochastic?" point: with `REPS` high on both VMs, you can report the effect size *with* its run-to-run variance, so a reviewer can see the signal sits well outside the noise.

---

## 7. Part F — Don't get surprised by the bill

- **Stop the VM whenever you're not running.** Console: VM row → **Stop**. CLI: `gcloud compute instances stop camo-vm --zone=us-east1-b`. A stopped VM costs **$0 for compute** (you still pay a few cents/day for the 30 GB disk). Start it again when you need it.
- **Set a budget alert:** Billing → **Budgets & alerts** → create a budget (e.g. $50) with email alerts at 50/90/100%. Catches runaway spend early.
- **Delete when the thesis is done:** `gcloud compute instances delete camo-vm camo-vm-2` and delete the `camo-image` and any snapshots so nothing lingers past the trial.
- **Your API spend is separate** and billed by OpenAI/Anthropic. Set a monthly spend limit in each provider's dashboard. Keep `REPS` low until a pilot looks right, then scale.

---

## 8. Security checklist

- Never commit `.env` or paste API keys into code, Overleaf, or the GitHub repo you share with your professor. (`.gitignore` already excludes `.env`.)
- If a key ever lands in a commit, **rotate it** (revoke + reissue) in the provider dashboard — deleting the line later isn't enough.
- Keep the VM's SSH to Google's browser/gcloud method; don't open extra firewall ports.

---

## 9. Suggested order of operations this week

1. Create the account + project + one `e2-standard-2` VM (Sections A–B). ~20 min.
2. Upload the repo, `DRY_RUN=1 ./run_all.sh` to confirm wiring. ~10 min.
3. Add keys, `REPS=1` real smoke test on ~2 models. Eyeball a few camouflaged rewrites and monitor verdicts for sanity. ~15 min + a few cents.
4. Raise `REPS`, widen model lists, run the full pilot in `tmux`. Pull `results/`.
5. Clone to VM #2, run the mirror implementation, compare (Section E).
6. Send your professor the GitHub repo + the `summary.csv` and `detection_drop.png` — that's a concrete pilot result to react to.

---

*Files referenced live in the `camouflage-experiments/` repo delivered alongside this runbook: `data/seed_actions.json` (your 30-action seed set), `src/camouflage.py`, `src/monitor.py`, `src/score.py`, `src/config.py`, `src/llm.py`, plus `README.md`.*
