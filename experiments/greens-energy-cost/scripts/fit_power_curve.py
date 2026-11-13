"""Step 2: fit measured_power_util ~ cpu_util for Google cell a pdu6.
Workload leg: datacentertracesdatasets google2019 real trace, 300 s grouped
cell-wide mean CPU utilisation, 8064 rows (28 days), no timestamps, row order
chronological from trace start. Power leg: PowerData 2019 cella_pdu6.csv,
8928 rows, 5-min grid, time in microseconds since trace start, window 2..8929.
Join: row i of the grouped trace aligns to PDU window i+2 (time = (i+2)*300 s).
Sensitivity: refit with the trace shifted by -1, 0, +1 windows.
No em dashes in this file.
"""
import numpy as np, pandas as pd
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "raw"; OUT = BASE / "outputs"; OUT.mkdir(exist_ok=True)

pdu = pd.read_csv(RAW / "cella_pdu6.csv")
pdu = pdu.sort_values("time").reset_index(drop=True)
pdu["window"] = (pdu["time"] // 300_000_000).astype(int)
assert pdu["window"].is_monotonic_increasing
assert pdu["bad_measurement_data"].sum() == 0
print("PDU rows", len(pdu), "windows", pdu["window"].min(), pdu["window"].max())
print("bad_production_power_data rows:", int(pdu["bad_production_power_data"].sum()),
      "(production_power_util not used)")

g = pd.read_csv("/usr/local/lib/python3.12/dist-packages/datacentertracesdatasets/google2019/machine_usage_grouped_300_seconds.csv")
print("Grouped trace rows", len(g), "cols", list(g.columns))
g = g.rename(columns={"cpu_util": "cpu_util_frac"})
# copy the frozen slice into the experiment directory for reproducibility
g.to_csv(RAW / "google2019_grouped_300s_cellwide_mean.csv", index=False)

def fit(cpu, power, label):
    x = np.asarray(cpu, float); y = np.asarray(power, float)
    A = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    resid = y - pred
    ss_res = float((resid ** 2).sum()); ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot
    n = len(x)
    # standard errors
    s2 = ss_res / (n - 2)
    cov = s2 * np.linalg.inv(A.T @ A)
    se = np.sqrt(np.diag(cov))
    print(f"{label}: n={n} intercept={coef[0]:.4f} (se {se[0]:.4f}) slope={coef[1]:.4f} (se {se[1]:.4f}) R2={r2:.4f} RMSE={np.sqrt(ss_res/n):.4f}")
    return coef, r2, resid, pred

# main join: grouped row i -> PDU window i+2
pdu_indexed = pdu.set_index("window")
rows = []
for shift in (0, 1, 2):
    cpu = g["cpu_util_frac"].values
    win = np.arange(len(cpu)) + 2 + shift
    power = pdu_indexed.loc[win, "measured_power_util"].values
    coef, r2, resid, pred = fit(cpu, power, f"shift {shift:+d}")
    rows.append(dict(shift=shift, intercept=coef[0], slope=coef[1], r2=r2,
                     rmse=float(np.sqrt((resid ** 2).mean()))))
    if shift == 0:
        joined = pd.DataFrame({"window": win, "cpu_util_frac": cpu,
                               "cpu_util_percent": cpu * 100,
                               "measured_power_util": power,
                               "fitted_power_util": pred, "residual": resid})
        joined.to_csv(OUT / "power_curve_join.csv", index=False)

# also fit on daily means (28 days) as a cross check
daily_cpu = g["cpu_util_frac"].values.reshape(28, 288).mean(axis=1)
daily_power = np.array([pdu_indexed.loc[np.arange(d * 288 + 2, (d + 1) * 288 + 2), "measured_power_util"].mean() for d in range(28)])
fit(daily_cpu, daily_power, "daily means (28 days)")

# correlation and ranges
print("CPU frac mean %.4f range %.4f to %.4f" % (g["cpu_util_frac"].mean(), g["cpu_util_frac"].min(), g["cpu_util_frac"].max()))
print("Power util mean %.4f range %.4f to %.4f" % (pdu["measured_power_util"].mean(), pdu["measured_power_util"].min(), pdu["measured_power_util"].max()))
print("Pearson r (main join): %.4f" % np.corrcoef(joined["cpu_util_frac"], joined["measured_power_util"])[0, 1])
pd.DataFrame(rows).to_csv(OUT / "power_curve_fits.csv", index=False)
print("saved power_curve_join.csv and power_curve_fits.csv")
