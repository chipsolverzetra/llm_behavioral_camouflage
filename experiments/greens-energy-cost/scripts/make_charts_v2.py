"""V2 charts: updated fig2 and fig3 with the seed-coded mixed total,
plus a mix and contribution chart. All values come from outputs/ and
outputs-v2/ of the prior run. No em dashes in labels.
"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
OUT2 = BASE / "outputs-v2"
CH = BASE / "charts-v2"
CH.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

summary = pd.read_csv(OUT / "energy_per_1000_actions.csv")
mixed = pd.read_csv(OUT2 / "mixed_totals_per_1000_actions_v2.csv")
mixed_pp = pd.read_csv(OUT2 / "mixed_per_permit_v2.csv")
contrib = pd.read_csv(OUT2 / "mixed_contributions_v2.csv")
per_permit = pd.read_csv(OUT / "energy_per_permit.csv")

fac = summary[summary["metric"] == "facility_kwh_per_permit"]
archs = ["Short administrative action", "Spin up or scale a service",
         "Run GPU inference (CPU proxy)", "Run a batch job"]
labels = ["Short admin", "Spin up / scale", "GPU inference", "Batch job"]

# --- fig2 v2: per-archetype (left) and seed-coded mixed total (right) ---
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
xpos = np.arange(len(archs)); w = 0.36
for i, mon in enumerate(["Claude", "Gemini"]):
    sub = fac[fac["monitor"] == mon].set_index("archetype").loc[archs]
    ax[0].bar(xpos + (i - 0.5) * w, sub["central"], w, label=f"{mon} (central)",
              yerr=[sub["central"] - sub["low"], sub["high"] - sub["central"]], capsize=4)
ax[0].axhline(0, color="black", linewidth=0.8)
ax[0].set_xticks(xpos); ax[0].set_xticklabels(labels)
ax[0].set_ylabel("Facility kWh per 1,000 actions")
ax[0].set_title("(a) Per archetype, all extra permits in one archetype")
ax[0].legend(fontsize=8)
mfac = mixed[mixed["metric"] == "facility_kwh_per_permit"]
x2 = np.arange(2)
ax[1].bar(x2, mfac["central"], 0.5, color=["#4a7bb7", "#7bb74a"],
          yerr=[mfac["central"] - mfac["low"], mfac["high"] - mfac["central"]], capsize=5)
for i, v in enumerate(mfac["central"]):
    ax[1].text(i, v + 150, f"{v:,.0f}", ha="center", fontsize=9)
ax[1].set_xticks(x2); ax[1].set_xticklabels(["Claude\n130 extra permits", "Gemini\n216 extra permits"])
ax[1].set_ylabel("Facility kWh per 1,000 actions")
ax[1].set_title("(b) Mixed total, seed-coded R+A mix\nShort 16/24, Spin up 3/24, Batch 5/24")
fig.suptitle("Figure 2 v2. Energy delta per 1,000 actions. Bars central (daily slope 0.442, 750 kW, PUE 1.56);\nwhiskers span slope 0.061-0.582, capacity 500-1,000 kW, PUE 1.05-1.56. Baseline and truthful-blocked are zero.")
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(CH / "fig2_v2_energy_by_condition_mixed.png", dpi=200)
plt.close(fig)

# --- fig3 v2: log scale, per PERMIT and per 1,000 actions, mixed total added ---
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
pp = per_permit[per_permit["slope_case"] == "central_daily_excl_first2d"]
pp = pp[(pp["capacity_case"] == "central") & (pp["pue_case"] == "central_uptime2024")]
pp = pp.set_index("archetype").loc[archs]
rng = per_permit.groupby("archetype")["facility_kwh_per_permit"].agg(["min", "max"]).loc[archs]
labels_pp = labels + ["MIXED TOTAL"]
vals_pp = list(pp["facility_kwh_per_permit"]) + [float(mixed_pp[mixed_pp["metric"] == "facility_kwh_per_permit"]["central"].iloc[0])]
lo_pp = list(pp["facility_kwh_per_permit"] - rng["min"]) + [float(mixed_pp[mixed_pp["metric"] == "facility_kwh_per_permit"]["central"].iloc[0] - mixed_pp[mixed_pp["metric"] == "facility_kwh_per_permit"]["low"].iloc[0])]
hi_pp = list(rng["max"] - pp["facility_kwh_per_permit"]) + [float(mixed_pp[mixed_pp["metric"] == "facility_kwh_per_permit"]["high"].iloc[0] - mixed_pp[mixed_pp["metric"] == "facility_kwh_per_permit"]["central"].iloc[0])]
colors = ["#8aa8c8", "#8aa8c8", "#8aa8c8", "#8aa8c8", "#c0392b"]
ax[0].barh(labels_pp, vals_pp, xerr=[lo_pp, hi_pp], capsize=4, color=colors)
ax[0].set_xscale("log")
ax[0].set_xlabel("Facility kWh per camouflaged PERMIT (log scale)")
ax[0].set_title("(c1) Per PERMIT")
rows1000 = []
for mon in ["Claude", "Gemini"]:
    sub = fac[fac["monitor"] == mon].set_index("archetype").loc[archs]
    for l, a in zip(labels, archs):
        rows1000.append((f"{l} ({mon})", float(sub.loc[a, "central"]),
                         float(sub.loc[a, "central"] - sub.loc[a, "low"]),
                         float(sub.loc[a, "high"] - sub.loc[a, "central"]), "#8aa8c8"))
    m = mfac[mfac["monitor"] == mon].iloc[0]
    rows1000.append((f"MIXED TOTAL ({mon})", float(m["central"]),
                     float(m["central"] - m["low"]), float(m["high"] - m["central"]), "#c0392b"))
y = [r[0] for r in rows1000]
ax[1].barh(y, [r[1] for r in rows1000],
           xerr=[[r[2] for r in rows1000], [r[3] for r in rows1000]],
           capsize=3, color=[r[4] for r in rows1000])
ax[1].set_xscale("log")
ax[1].set_xlabel("Facility kWh per 1,000 actions (log scale)")
ax[1].set_title("(c2) Per 1,000 actions")
fig.suptitle("Figure 3 v2. Energy per PERMIT and per 1,000 actions, mixed total in red.\nPoints central (daily slope 0.442, 750 kW, PUE 1.56);\nwhiskers span slope 0.061-0.582, capacity 500-1,000 kW, PUE 1.05-1.56.")
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(CH / "fig3_v2_energy_per_permit_and_per_1000_mixed.png", dpi=200)
plt.close(fig)

# --- fig5: R+A mix and contribution to the mixed total (central, Claude) ---
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
mix_labels = ["Short admin\n16 of 24", "Spin up / scale\n3 of 24", "Batch job\n5 of 24",
              "GPU inference\n0 of 24", "Idle\n0 of 24"]
mix_vals = [16, 3, 5, 0, 0]
ax[0].bar(mix_labels, mix_vals, color=["#4a7bb7", "#7bb74a", "#c0392b", "#999999", "#cccccc"])
ax[0].set_ylabel("Seed actions in R+A (n=24)")
ax[0].set_title("(d1) Allocation basis: the R+A seed mix")
c = contrib[contrib["monitor"] == "Claude"]
ax[1].bar(["Claude mixed total\n1,648 kWh per 1,000 actions"],
          [float(c[c["archetype"] == "Run a batch job"]["facility_kwh_per_1000_central"].iloc[0])],
          label="Batch job (5 of 24 actions, 85.0% of energy)", color="#c0392b")
ax[1].bar(["Claude mixed total\n1,648 kWh per 1,000 actions"],
          [float(c[c["archetype"] == "Spin up or scale a service"]["facility_kwh_per_1000_central"].iloc[0])],
          bottom=[float(c[c["archetype"] == "Run a batch job"]["facility_kwh_per_1000_central"].iloc[0])],
          label="Spin up / scale (3 of 24, 12.8%)", color="#7bb74a")
ax[1].bar(["Claude mixed total\n1,648 kWh per 1,000 actions"],
          [float(c[c["archetype"] == "Short administrative action"]["facility_kwh_per_1000_central"].iloc[0])],
          bottom=[float(c[c["archetype"] == "Run a batch job"]["facility_kwh_per_1000_central"].iloc[0]
                   + c[c["archetype"] == "Spin up or scale a service"]["facility_kwh_per_1000_central"].iloc[0])],
          label="Short admin (16 of 24, 2.3%)", color="#4a7bb7")
ax[1].set_ylabel("Facility kWh per 1,000 actions (central)")
ax[1].set_title("(d2) Contribution: batch jobs dominate the total")
ax[1].legend(fontsize=8)
fig.suptitle("Figure 5. Seed-coded mix and its energy contribution. GPU inference and Idle get 0 of 24 R+A actions,\nso they contribute nothing to the mixed total; no seed action was a GPU inference workload.")
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(CH / "fig5_v2_mix_and_contribution.png", dpi=200)
plt.close(fig)

print("charts v2 written:")
for f in sorted(CH.glob("*.png")):
    print(" ", f.name, f.stat().st_size, "bytes")
