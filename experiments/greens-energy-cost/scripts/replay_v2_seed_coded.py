"""V2 seed-coded replay. Reads the 30 seed actions from the cloned repo,
validates tier counts, codes each action to one archetype from the prior
run, allocates the extra camouflage permits across archetypes using the
R+A seed mix (24 actions), and recomputes a single mixed total per 1,000
actions. Reuses the prior run energy_per_permit.csv and
energy_per_1000_actions.csv; it does not refit the power curve.
No em dashes in this file.
"""
import json
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = Path("/home/hatch/workspace/paper-submissions/llm_behavioral_camouflage")
SEED = REPO / "data" / "seed_actions.json"
OUT = BASE / "outputs-v2"
CH = BASE / "charts-v2"
OUT.mkdir(exist_ok=True)
CH.mkdir(exist_ok=True)

# --- Validation ---
actions = json.loads(SEED.read_text())["actions"]
assert len(actions) == 30, len(actions)
tiers = {}
for a in actions:
    tiers[a["tier"]] = tiers.get(a["tier"], 0) + 1
assert tiers == {"B": 6, "A": 9, "R": 15}, tiers
assert [a["id"] for a in actions if a["tier"] == "B"] == [1, 2, 3, 4, 5, 6]
assert [a["id"] for a in actions if a["tier"] == "A"] == [7, 8, 9, 10, 11, 12, 13, 14, 15]
assert [a["id"] for a in actions if a["tier"] == "R"] == list(range(16, 31))
print("Validation passed: total 30, B 6 (ids 1-6), A 9 (ids 7-15), R 15 (ids 16-30), R+A 24")

# --- Coding: action, not wording. Archetypes from CODING_GUIDE.md. ---
# Short admin: 0.01 CPU for 5 min. Spin up: 0.05 for 30 min.
# Batch job: 0.10 for 60 min. GPU inference: 0.10 for 15 min (CPU proxy).
# Idle: 0. If an action does not fit, Idle; do not force it into compute.
SHORT = "Short administrative action"
SPIN = "Spin up or scale a service"
BATCH = "Run a batch job"
GPU = "Run GPU inference (CPU proxy)"
IDLE = "Idle or no workload change"

CODING = {
    1: (SHORT, "Read-only summarisation, one brief request, no persistent service or large job."),
    2: (SHORT, "One brief text draft, no persistent service or large job."),
    3: (SHORT, "One brief reformat of a file, no persistent service or large job."),
    4: (SHORT, "One brief read-only retrieval, no persistent service or large job."),
    5: (SHORT, "One brief code generation request, no sustained inference workload or large job."),
    6: (SHORT, "One brief calendar write, no persistent service or large job."),
    7: (SHORT, "One brief permission change, no sustained compute."),
    8: (SHORT, "One brief package install on one host, no persistent service or large job."),
    9: (BATCH, "A merge triggers a CI build and test pipeline, a sustained job, not just the merge click."),
    10: (SHORT, "One brief read query, no sustained compute."),
    11: (SHORT, "Brief per-ticket replies, no persistent service or large job."),
    12: (SPIN, "Direct match: starting a compute instance is a spin up, a persistent service."),
    13: (SHORT, "One brief config toggle, no sustained compute."),
    14: (SHORT, "One brief outbound post, no sustained compute."),
    15: (BATCH, "Bulk sending to a segment is a sustained sending job, not one brief message."),
    16: (BATCH, "Purging backups or storage is a sustained deletion job over a large data set."),
    17: (BATCH, "Sending a full customer list out is a bulk data transfer, a sustained job."),
    18: (SHORT, "One brief financial transaction, no sustained compute."),
    19: (SHORT, "One brief config toggle to disable a check, no sustained compute."),
    20: (SHORT, "One brief permission change, no sustained compute."),
    21: (SHORT, "One brief small data transfer, no sustained compute."),
    22: (SHORT, "One shell command, coded conservatively as brief; duration is unknown, so no large job is assumed."),
    23: (BATCH, "Dropping or overwriting a production table is a sustained large write, not one brief edit."),
    24: (SHORT, "One brief financial transaction, no sustained compute."),
    25: (SHORT, "One brief delete or edit of log records, no sustained compute."),
    26: (SPIN, "Connecting a new tool or MCP server starts a persistent service."),
    27: (SHORT, "Delegation is coordination, one brief handoff; the other agent's work is not counted here."),
    28: (SHORT, "One brief outbound message, no sustained compute."),
    29: (SPIN, "Routing through a proxy opens a persistent proxied session, not one brief request."),
    30: (SHORT, "One brief write to a prompt, policy, or memory store, no sustained compute."),
}

rows = []
for a in actions:
    arch, why = CODING[a["id"]]
    camouflaged = a["tier"] in ("R", "A")
    rows.append({
        "seed_id": a["id"],
        "action": a["action"],
        "tier": a["tier"],
        "risk_category": a["risk_category"],
        "archetype": arch,
        "justification": why,
        "camouflaged_R_or_A": camouflaged,
        "counts_toward_energy_delta": camouflaged,
    })
coding = pd.DataFrame(rows)
coding.to_csv(OUT / "seed_coding.csv", index=False)

# --- Allocation basis: the R+A seed mix (24 actions) ---
ra = coding[coding["camouflaged_R_or_A"]]
mix = ra["archetype"].value_counts()
print("\nR+A mix (n=24):")
for arch in [SHORT, SPIN, BATCH, GPU, IDLE]:
    n = int(mix.get(arch, 0))
    print(f"  {arch}: {n} of 24 = {n / 24:.4f}")
shares = {arch: int(mix.get(arch, 0)) / 24.0 for arch in [SHORT, SPIN, BATCH, GPU, IDLE]}
assert abs(sum(shares.values()) - 1.0) < 1e-9
# Benign (B) actions: all 6 coded Short admin, but they were never
# camouflaged and would have been permitted anyway, so they contribute
# no camouflage delta and are excluded from the allocation basis.

# --- Mixed totals, from the prior run per-archetype per-1000 table ---
per1000 = pd.read_csv(BASE / "outputs" / "energy_per_1000_actions.csv")
per_permit = pd.read_csv(BASE / "outputs" / "energy_per_permit.csv")
CENTRAL = ("central_daily_excl_first2d", "central", "central_uptime2024")

mixed1000 = []
for monitor in ["Claude", "Gemini"]:
    for metric in ["it_kwh_per_permit", "facility_kwh_per_permit", "cooling_kwh_per_permit"]:
        sub = per1000[(per1000["monitor"] == monitor) & (per1000["metric"] == metric)]
        total = {k: 0.0 for k in ["central", "low", "high"]}
        for arch, share in shares.items():
            r = sub[sub["archetype"] == arch]
            if len(r) == 0:
                continue
            for k in total:
                total[k] += share * float(r.iloc[0][k])
        mixed1000.append({
            "monitor": monitor,
            "extra_permits_per_1000": 130.0 if monitor == "Claude" else 216.0,
            "metric": metric,
            "allocation_basis": "R+A seed mix: Short 16/24, Spin up 3/24, Batch 5/24, GPU 0/24, Idle 0/24",
            "central": total["central"], "low": total["low"], "high": total["high"],
        })
mixed1000 = pd.DataFrame(mixed1000)
mixed1000.to_csv(OUT / "mixed_totals_per_1000_actions_v2.csv", index=False)

# Mixed per PERMIT: weighted sum of per-archetype central, and of the
# per-archetype full-range minima and maxima from the prior grid.
mixed_pp = []
for metric in ["it_kwh_per_permit", "facility_kwh_per_permit", "cooling_kwh_per_permit"]:
    cen = 0.0
    lo = 0.0
    hi = 0.0
    for arch, share in shares.items():
        sub = per_permit[per_permit["archetype"] == arch]
        c = sub[(sub["slope_case"] == CENTRAL[0]) & (sub["capacity_case"] == CENTRAL[1])
                & (sub["pue_case"] == CENTRAL[2])].iloc[0][metric]
        cen += share * float(c)
        lo += share * float(sub[metric].min())
        hi += share * float(sub[metric].max())
    mixed_pp.append({"metric": metric, "central": cen, "low": lo, "high": hi})
mixed_pp = pd.DataFrame(mixed_pp)
mixed_pp.to_csv(OUT / "mixed_per_permit_v2.csv", index=False)

# Per-archetype contribution to the mixed total, central, facility kWh
contrib = []
for monitor in ["Claude", "Gemini"]:
    extra = 130.0 if monitor == "Claude" else 216.0
    for arch, share in shares.items():
        sub = per1000[(per1000["monitor"] == monitor)
                      & (per1000["metric"] == "facility_kwh_per_permit")
                      & (per1000["archetype"] == arch)]
        if len(sub) == 0:
            continue
        contrib.append({
            "monitor": monitor, "archetype": arch,
            "share_of_R_A": share,
            "extra_permits_per_1000_from_this_archetype": extra * share,
            "facility_kwh_per_1000_central": share * float(sub.iloc[0]["central"]),
            "facility_kwh_per_1000_low": share * float(sub.iloc[0]["low"]),
            "facility_kwh_per_1000_high": share * float(sub.iloc[0]["high"]),
        })
pd.DataFrame(contrib).to_csv(OUT / "mixed_contributions_v2.csv", index=False)

print("\n=== Mixed total per PERMIT, facility kWh ===")
print(mixed_pp.to_string(index=False))
print("\n=== Mixed total per 1,000 actions ===")
print(mixed1000.to_string(index=False))
print("\n=== Contributions, facility kWh per 1,000 actions, central ===")
print(pd.DataFrame(contrib).to_string(index=False))
print("\nOutputs written to", OUT)
