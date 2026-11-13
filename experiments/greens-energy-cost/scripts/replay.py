"""Steps 3-6: three-condition replay, IT energy, PUE/cooling, LLM side.
All inputs are real downloaded data or values transcribed from the
Luccioni et al. 2024 paper PDF (Table 2, extracted in raw/luccioni2024.txt).
No em dashes in this file.
"""
import numpy as np, pandas as pd, json
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"; OUT.mkdir(exist_ok=True)

# --- Fitted power curve (from scripts/fit_power_curve.py, outputs/power_curve_fits.csv)
# slope_low: 5-min fit, slope 0.0613, R2 0.0090
# slope_central: daily fit excluding days 0-1, slope 0.4420, R2 0.4381
# slope_high: daily fit all 28 days, slope 0.5818, R2 0.4450
SLOPES = {"low_5min": 0.0613, "central_daily_excl_first2d": 0.4420, "high_daily_all28d": 0.5818}
# PDU capacity scenarios (kW). Central 750 kW anchored on the mapping file:
# pdu6 cell a serves 1,738 machines; 1,738 machines at about 310 W mean draw
# is about 539 kW, and mean measured power util is 0.715, so implied capacity
# is about 539 / 0.715 = 754 kW. Low 500 kW and high 1,000 kW bracket it.
CAPACITY_KW = {"low": 500.0, "central": 750.0, "high": 1000.0}
# PUE scenarios: low 1.05 Frontier liquid-cooled HPC average (Sun et al. 2024);
# central 1.56 Uptime Institute 2024 global average (search verified 2026-11-13).
PUE = {"low_frontier": 1.05, "central_uptime2024": 1.56}
# Luccioni et al. 2024 Table 2, Wh per 1,000 queries (mean):
# text classification 0.002, text generation 0.047. Small open models only.
LUCCIONI_WH_PER_1000 = {"text_classification": 0.002, "text_generation": 0.047}
# Source paper detection results (exact, do not alter)
VARIANTS = 1873
EVASION = {"Claude": 0.130, "Gemini": 0.216}
# Deployment LLM calls per action: 1 agent narration + 1 monitor judgement
CALLS_PER_ACTION = 2

ARCHETYPES = pd.DataFrame([
    {"archetype": "Short administrative action", "cpu_frac": 0.01, "duration_min": 5},
    {"archetype": "Spin up or scale a service", "cpu_frac": 0.05, "duration_min": 30},
    {"archetype": "Run a batch job", "cpu_frac": 0.10, "duration_min": 60},
    {"archetype": "Run GPU inference (CPU proxy)", "cpu_frac": 0.10, "duration_min": 15},
    {"archetype": "Idle or no workload change", "cpu_frac": 0.00, "duration_min": 0},
])
ARCHETYPES.to_csv(OUT / "archetypes.csv", index=False)

def energy_it_kwh(slope, cpu_frac, duration_min, capacity_kw):
    return slope * cpu_frac * (duration_min / 60.0) * capacity_kw

rows = []
for _, a in ARCHETYPES.iterrows():
    for sname, slope in SLOPES.items():
        for cname, cap in CAPACITY_KW.items():
            it = energy_it_kwh(slope, a["cpu_frac"], a["duration_min"], cap)
            for pname, pue in PUE.items():
                rows.append({
                    "archetype": a["archetype"], "slope_case": sname, "slope": slope,
                    "capacity_case": cname, "capacity_kw": cap, "pue_case": pname, "pue": pue,
                    "it_kwh_per_permit": it,
                    "facility_kwh_per_permit": it * pue,
                    "cooling_kwh_per_permit": it * (pue - 1.0),
                    "normalised_util_hours_per_permit": slope * a["cpu_frac"] * (a["duration_min"] / 60.0),
                })
per_permit = pd.DataFrame(rows)
per_permit.to_csv(OUT / "energy_per_permit.csv", index=False)

# Per 1,000 actions, per monitor: extra permits = evasion drop * 1000
summary = []
for monitor, ev in EVASION.items():
    extra_per_1000 = ev * 1000
    for arch in ARCHETYPES["archetype"].unique():
        sub = per_permit[per_permit["archetype"] == arch]
        for col in ["it_kwh_per_permit", "facility_kwh_per_permit", "cooling_kwh_per_permit"]:
            v = sub[col] * extra_per_1000
            summary.append({"monitor": monitor, "extra_permits_per_1000": extra_per_1000,
                            "archetype": arch, "metric": col,
                            "central": float(v[(sub["slope_case"] == "central_daily_excl_first2d") &
                                              (sub["capacity_case"] == "central") &
                                              (sub["pue_case"] == "central_uptime2024")].iloc[0]),
                            "low": float(v.min()), "high": float(v.max())})
summary = pd.DataFrame(summary)
summary.to_csv(OUT / "energy_per_1000_actions.csv", index=False)

# Baseline day context for the PDU (measured, not modelled)
pdu = pd.read_csv(BASE / "raw" / "cella_pdu6.csv")
mean_util = float(pdu["measured_power_util"].mean())
baseline = []
for cname, cap in CAPACITY_KW.items():
    it_day = mean_util * cap * 24
    baseline.append({"capacity_case": cname, "capacity_kw": cap,
                     "mean_measured_power_util": mean_util,
                     "baseline_it_kwh_per_day": it_day,
                     "baseline_facility_kwh_per_day_pue1.56": it_day * 1.56,
                     "baseline_facility_kwh_per_day_pue1.05": it_day * 1.05})
pd.DataFrame(baseline).to_csv(OUT / "baseline_pdu_day.csv", index=False)

# LLM side (H3): deployment calls only, Luccioni calibration
llm = []
for task, wh in LUCCIONI_WH_PER_1000.items():
    wh_per_call = wh / 1000.0
    it_wh_per_1000_actions = CALLS_PER_ACTION * 1000 * wh_per_call
    for pname, pue in PUE.items():
        llm.append({"calibration_task": task, "wh_per_1000_queries": wh,
                    "calls_per_action": CALLS_PER_ACTION,
                    "it_wh_per_1000_actions": it_wh_per_1000_actions,
                    "pue_case": pname, "pue": pue,
                    "facility_wh_per_1000_actions": it_wh_per_1000_actions * pue})
llm = pd.DataFrame(llm)
llm.to_csv(OUT / "llm_side_energy.csv", index=False)

# Headline numbers for RESULTS.md
print("=== per PERMIT, facility kWh (central: daily slope 0.442, 750 kW, PUE 1.56) ===")
cen = per_permit[(per_permit["slope_case"] == "central_daily_excl_first2d") &
                 (per_permit["capacity_case"] == "central") &
                 (per_permit["pue_case"] == "central_uptime2024")]
print(cen[["archetype", "it_kwh_per_permit", "facility_kwh_per_permit", "cooling_kwh_per_permit"]].to_string(index=False))
print("\n=== per PERMIT facility kWh, full range (slope 0.061-0.582, capacity 500-1000 kW, PUE 1.05-1.56) ===")
print(per_permit.groupby("archetype")["facility_kwh_per_permit"].agg(["min", "max"]).to_string())
print("\n=== per 1,000 actions, facility kWh ===")
print(summary[summary["metric"] == "facility_kwh_per_permit"].pivot_table(
    index=["monitor", "archetype"], values=["low", "central", "high"]).to_string())
print("\n=== baseline PDU day ===")
print(pd.DataFrame(baseline).to_string(index=False))
print("\n=== LLM side per 1,000 actions ===")
print(llm.to_string(index=False))
print("\nExtra permits in the study: Claude %.1f, Gemini %.1f of %d variants" %
      (EVASION["Claude"] * VARIANTS, EVASION["Gemini"] * VARIANTS, VARIANTS))
