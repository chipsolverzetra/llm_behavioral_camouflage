import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

R = Path("results")
RUNS = [
    ("Claude\n(Sonnet 5)", "summary_claude_n99.csv", "#2b6cb0"),
    ("Gemini\n(3-flash)",  "summary_gemini_n99.csv", "#c53030"),
]
rows = []
for label, fn, color in RUNS:
    p = R / fn
    if not p.exists():
        print(f"  skip: {p} not found"); continue
    s = pd.read_csv(p).iloc[0]
    rows.append(dict(label=label, color=color,
        tpr=s["tpr"]*100, tpr_lo=s["tpr_lo"]*100, tpr_hi=s["tpr_hi"]*100,
        camo=s["camo_tpr"]*100, camo_lo=s["camo_lo"]*100, camo_hi=s["camo_hi"]*100,
        drop=s["drop"]*100, drop_lo=s["drop_lo"]*100, drop_hi=s["drop_hi"]*100,
        fpr=s["fpr"]*100))
if not rows:
    raise SystemExit("No summary CSVs found in results/")
labels=[r["label"] for r in rows]; x=np.arange(len(rows)); w=0.36; BLUE="#2b6cb0"
fig,(axA,axB)=plt.subplots(1,2,figsize=(11,4.4))
orig=[r["tpr"] for r in rows]; camo=[r["camo"] for r in rows]
oe=[[r["tpr"]-r["tpr_lo"] for r in rows],[r["tpr_hi"]-r["tpr"] for r in rows]]
ce=[[r["camo"]-r["camo_lo"] for r in rows],[r["camo_hi"]-r["camo"] for r in rows]]
b1=axA.bar(x-w/2,orig,w,label="Original risky action",color=BLUE,yerr=oe,capsize=5,ecolor="#1a1a1a")
b2=axA.bar(x+w/2,camo,w,label="Camouflaged action",color="#c53030",yerr=ce,capsize=5,ecolor="#1a1a1a")
for bars in (b1,b2):
    for bar in bars:
        h=bar.get_height()
        axA.text(bar.get_x()+bar.get_width()/2,h+1.5,f"{h:.1f}%",ha="center",va="bottom",fontsize=9,fontweight="bold")
axA.set_ylim(0,112); axA.set_xticks(x); axA.set_xticklabels(labels)
axA.set_ylabel("Detected as RISKY (%)")
axA.set_title("(A)  Detection collapses under camouflage",fontsize=11)
axA.legend(frameon=False,fontsize=9,loc="lower center")
axA.spines[["top","right"]].set_visible(False)
drops=[r["drop"] for r in rows]
de=[[r["drop"]-r["drop_lo"] for r in rows],[r["drop_hi"]-r["drop"] for r in rows]]
axB.bar(x,drops,0.5,color=[r["color"] for r in rows],yerr=de,capsize=7,ecolor="#1a1a1a")
axB.axhline(0,color="#1a1a1a",lw=1)
for xi,r in zip(x,rows):
    axB.text(xi,r["drop_hi"]+0.6,f"{r['drop']:.1f} pp\n[{r['drop_lo']:.1f}, {r['drop_hi']:.1f}]",ha="center",va="bottom",fontsize=9,fontweight="bold")
axB.set_xticks(x); axB.set_xticklabels(labels)
axB.set_ylabel("Evasion drop (TPR - camouflaged, pp)")
axB.set_title("(B)  Drop is real for both vendors (95% CI excludes 0)",fontsize=11)
axB.set_ylim(0,max(r["drop_hi"] for r in rows)+6)
axB.spines[["top","right"]].set_visible(False)
fig.suptitle("Behavioural camouflage evades oversight monitors across vendors",fontsize=12,fontweight="bold",y=1.02)
fig.tight_layout()
fig.savefig(R/"comparison_figure.png",dpi=200,bbox_inches="tight")
fig.savefig(R/"comparison_figure.pdf",bbox_inches="tight")
print(f"saved comparison_figure.png/.pdf ({len(rows)} monitors)")
