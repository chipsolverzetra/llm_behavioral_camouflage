"""Charts from the data actually downloaded. No em dashes in labels."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"; CH = BASE / "charts"; CH.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

joined = pd.read_csv(OUT / "power_curve_join.csv")
per_permit = pd.read_csv(OUT / "energy_per_permit.csv")
summary = pd.read_csv(OUT / "energy_per_1000_actions.csv")
azure = pd.read_csv(BASE / "raw" / "AzureLLMInferenceTrace_conv_1hour_2024-05-12_00-01.csv")

# (a) power curve: 5-min binned means + daily means
fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
jb = joined.copy()
jb["cpu_bin"] = pd.qcut(jb["cpu_util_frac"], 10)
b = jb.groupby("cpu_bin", observed=True).agg(cpu=("cpu_util_frac", "mean"),
    power=("measured_power_util", "mean"), sd=("measured_power_util", "std"))
ax[0].errorbar(b["cpu"], b["power"], yerr=b["sd"], fmt="o", capsize=3,
               label="5-min decile means (n=8,064 windows)")
x = np.linspace(0.30, 0.60, 50)
ax[0].plot(x, 0.6862 + 0.0613 * x, label="5-min fit: slope 0.061, R2 0.009")
ax[0].set_xlabel("Cell-wide mean CPU utilisation (fraction)")
ax[0].set_ylabel("PDU measured power utilisation (fraction)")
ax[0].set_title("(a1) 5-minute windows: almost flat")
ax[0].legend(fontsize=8)
joined["day"] = np.arange(len(joined)) // 288
d = joined.groupby("day").agg(cpu=("cpu_util_frac", "mean"), power=("measured_power_util", "mean"))
ax[1].scatter(d["cpu"], d["power"], label="Daily means (n=28 days)")
ax[1].plot(x, 0.4402 + 0.5818 * x, label="Daily fit all 28 d: slope 0.582, R2 0.445")
ax[1].plot(x, 0.5085 + 0.4420 * x, "--", label="Daily fit excl. days 0-1: slope 0.442, R2 0.438")
ax[1].set_xlabel("Cell-wide mean CPU utilisation (fraction)")
ax[1].set_ylabel("PDU measured power utilisation (fraction)")
ax[1].set_title("(a2) Daily means: the usable fit")
ax[1].legend(fontsize=8)
fig.suptitle("Figure 1. Power curve fit, Google cell a pdu6, May 2019 (8,064 five-minute windows)")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(CH / "fig1_power_curve.png", dpi=200)
plt.close(fig)

# (b) energy per condition, per 1,000 actions, facility kWh, central + range
fac = summary[summary["metric"] == "facility_kwh_per_permit"]
archs = ["Short administrative action", "Spin up or scale a service",
         "Run GPU inference (CPU proxy)", "Run a batch job"]
labels = ["Short admin", "Spin up / scale", "GPU inference", "Batch job"]
fig, ax = plt.subplots(figsize=(9, 4.6))
xpos = np.arange(len(archs)); w = 0.36
for i, mon in enumerate(["Claude", "Gemini"]):
    sub = fac[fac["monitor"] == mon].set_index("archetype").loc[archs]
    ax.bar(xpos + (i - 0.5) * w, sub["central"], w, label=f"{mon} camouflaged-permitted (central)",
           yerr=[sub["central"] - sub["low"], sub["high"] - sub["central"]], capsize=4)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(xpos); ax.set_xticklabels(labels)
ax.set_ylabel("Facility kWh per 1,000 actions")
ax.set_title("Figure 2. Energy delta by condition: baseline and truthful-blocked are zero by construction;\n"
             "camouflaged-permitted adds the archetype workload. Bars central, whiskers full range.")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(CH / "fig2_energy_by_condition.png", dpi=200)
plt.close(fig)

# (c) per PERMIT and per 1,000 actions, log scale
fig, ax = plt.subplots(1, 2, figsize=(10, 4.4))
pp = per_permit[per_permit["slope_case"] == "central_daily_excl_first2d"]
pp = pp[(pp["capacity_case"] == "central") & (pp["pue_case"] == "central_uptime2024")]
pp = pp.set_index("archetype").loc[archs]
rng = per_permit.groupby("archetype")["facility_kwh_per_permit"].agg(["min", "max"]).loc[archs]
ax[0].barh(labels, pp["facility_kwh_per_permit"],
           xerr=[pp["facility_kwh_per_permit"] - rng["min"], rng["max"] - pp["facility_kwh_per_permit"]],
           capsize=4)
ax[0].set_xscale("log")
ax[0].set_xlabel("Facility kWh per camouflaged PERMIT (log scale)")
ax[0].set_title("(c1) Per PERMIT")
for i, mon in enumerate(["Claude", "Gemini"]):
    sub = fac[fac["monitor"] == mon].set_index("archetype").loc[archs]
    ax[1].barh([f"{l} ({mon})" for l in labels], sub["central"],
               xerr=[sub["central"] - sub["low"], sub["high"] - sub["central"]], capsize=3)
ax[1].set_xscale("log")
ax[1].set_xlabel("Facility kWh per 1,000 actions (log scale)")
ax[1].set_title("(c2) Per 1,000 actions")
fig.suptitle("Figure 3. Energy per PERMIT and per 1,000 actions. Points central (daily slope 0.442,\n750 kW PDU, PUE 1.56); whiskers span slope 0.061-0.582, capacity 500-1,000 kW, PUE 1.05-1.56.")
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig(CH / "fig3_energy_per_permit_and_per_1000.png", dpi=200)
plt.close(fig)

# (d) Azure LLM trace, 1-hour slice
fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
ax[0].hist(azure["ContextTokens"], bins=60, color="#4a7bb7")
ax[0].axvline(azure["ContextTokens"].median(), color="red", linestyle="--",
              label=f"Median {azure['ContextTokens'].median():.0f}")
ax[0].axvline(azure["ContextTokens"].mean(), color="black", linestyle=":",
              label=f"Mean {azure['ContextTokens'].mean():.0f}")
ax[0].set_xlabel("Context tokens per request"); ax[0].set_ylabel("Requests")
ax[0].set_title("Context tokens (n=91,156)")
ax[0].legend(fontsize=8)
ax[1].hist(azure["GeneratedTokens"], bins=60, color="#7bb74a")
ax[1].axvline(azure["GeneratedTokens"].median(), color="red", linestyle="--",
              label=f"Median {azure['GeneratedTokens'].median():.0f}")
ax[1].axvline(azure["GeneratedTokens"].mean(), color="black", linestyle=":",
              label=f"Mean {azure['GeneratedTokens'].mean():.0f}")
ax[1].set_xlabel("Generated tokens per request"); ax[1].set_ylabel("Requests")
ax[1].set_title("Generated tokens (n=91,156)")
ax[1].legend(fontsize=8)
fig.suptitle("Figure 4. Azure LLM Inference 2024, Conversation trace, 1-hour slice 2024-05-12 00:00-01:00 UTC")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(CH / "fig4_azure_token_distribution.png", dpi=200)
plt.close(fig)
print("charts written:")
for f in sorted(CH.glob("*.png")):
    print(" ", f.name, f.stat().st_size, "bytes")
