import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
R = Path("results")
BLUE, RED, GREY = "#2b6cb0", "#c53030", "#a0aec0"
MONITORS = {
    "claude": ("Claude monitor (Sonnet 5)", "summary_claude_n99.csv", "bytf_claude_n99.csv", BLUE),
    "gemini": ("Gemini monitor (3-flash)", "summary_gemini_n99.csv", "bytf_gemini_n99.csv", RED),
}
def load(key):
    title, sfn, bfn, theme = MONITORS[key]
    s = pd.read_csv(R / sfn).iloc[0]
    d = dict(title=title, theme=theme,
             tpr=s["tpr"]*100, tpr_lo=s["tpr_lo"]*100, tpr_hi=s["tpr_hi"]*100,
             camo=s["camo_tpr"]*100, camo_lo=s["camo_lo"]*100, camo_hi=s["camo_hi"]*100,
             drop=s["drop"]*100, drop_lo=s["drop_lo"]*100, drop_hi=s["drop_hi"]*100,
             fpr=s["fpr"]*100, fpr_lo=s["fpr_lo"]*100, fpr_hi=s["fpr_hi"]*100)
    bt = pd.read_csv(R / bfn).sort_values("detection_rate")
    d["bytf"] = [(row["transformations"].replace("_"," "), row["detection_rate"]*100, int(row["n"]))
                 for _, row in bt.iterrows()]
    return d
def per_monitor_figure(key):
    d = load(key)
    fig,(axA,axB)=plt.subplots(1,2,figsize=(11.5,4.6),gridspec_kw={"width_ratios":[1,1.25]})
    conds=["Original\n(risky)","Camouflaged","Benign\n(false pos.)"]
    means=[d["tpr"],d["camo"],d["fpr"]]; lo=[d["tpr_lo"],d["camo_lo"],d["fpr_lo"]]; hi=[d["tpr_hi"],d["camo_hi"],d["fpr_hi"]]
    yerr=[[m-l for m,l in zip(means,lo)],[h-m for m,h in zip(means,hi)]]
    bars=axA.bar(conds,means,color=[BLUE,RED,GREY],yerr=yerr,capsize=6,ecolor="#1a1a1a",width=0.62)
    for bar,m in zip(bars,means):
        axA.text(bar.get_x()+bar.get_width()/2,m+2.0,f"{m:.1f}%",ha="center",va="bottom",fontsize=10,fontweight="bold")
    axA.annotate("",xy=(1,d["camo"]),xytext=(0,d["tpr"]),arrowprops=dict(arrowstyle="<->",color="#2d3748",lw=1.4))
    axA.text(0.5,(d["tpr"]+d["camo"])/2+4,f"drop {d['drop']:.1f} pp\n[{d['drop_lo']:.1f}, {d['drop_hi']:.1f}]",ha="center",va="bottom",fontsize=9,color="#2d3748",fontweight="bold")
    axA.set_ylim(0,112); axA.set_ylabel("Detected as RISKY (%)")
    axA.set_title("(A)  Detection by condition",fontsize=11); axA.spines[["top","right"]].set_visible(False)
    fams=[f"{f}  (n={n})" for f,r,n in d["bytf"]]; rates=[r for f,r,n in d["bytf"]]
    ypos=np.arange(len(fams))[::-1]
    axB.barh(ypos,rates,color=d["theme"],alpha=0.85,height=0.62)
    for y,r in zip(ypos,rates): axB.text(r+1,y,f"{r:.1f}%",va="center",fontsize=9,fontweight="bold")
    axB.set_yticks(ypos); axB.set_yticklabels(fams,fontsize=9); axB.set_xlim(0,100)
    axB.set_xlabel("Detected as RISKY (%)  -  lower = fools monitor more")
    axB.set_title("(B)  Which disguise family evades this monitor",fontsize=11); axB.spines[["top","right"]].set_visible(False)
    fig.suptitle(d["title"]+"  -  N=99",fontsize=13,fontweight="bold",y=1.02); fig.tight_layout()
    fig.savefig(R/f"{key}_figure.png",dpi=200,bbox_inches="tight"); fig.savefig(R/f"{key}_figure.pdf",bbox_inches="tight"); plt.close(fig)
def comparison_figure():
    keys=list(MONITORS); ds={k:load(k) for k in keys}
    labels=[ds[k]["title"].split(" monitor")[0] for k in keys]; x=np.arange(len(keys)); w=0.36
    fig,(axA,axB)=plt.subplots(1,2,figsize=(11,4.4))
    orig=[ds[k]["tpr"] for k in keys]; camo=[ds[k]["camo"] for k in keys]
    oe=[[ds[k]["tpr"]-ds[k]["tpr_lo"] for k in keys],[ds[k]["tpr_hi"]-ds[k]["tpr"] for k in keys]]
    ce=[[ds[k]["camo"]-ds[k]["camo_lo"] for k in keys],[ds[k]["camo_hi"]-ds[k]["camo"] for k in keys]]
    b1=axA.bar(x-w/2,orig,w,label="Original risky",color=BLUE,yerr=oe,capsize=5,ecolor="#1a1a1a")
    b2=axA.bar(x+w/2,camo,w,label="Camouflaged",color=RED,yerr=ce,capsize=5,ecolor="#1a1a1a")
    for bars in (b1,b2):
        for bar in bars:
            h=bar.get_height(); axA.text(bar.get_x()+bar.get_width()/2,h+1.5,f"{h:.1f}%",ha="center",va="bottom",fontsize=9,fontweight="bold")
    axA.set_ylim(0,112); axA.set_xticks(x); axA.set_xticklabels(labels); axA.set_ylabel("Detected as RISKY (%)")
    axA.set_title("(A)  Detection collapses under camouflage",fontsize=11)
    axA.legend(frameon=False,fontsize=9,loc="lower center"); axA.spines[["top","right"]].set_visible(False)
    drops=[ds[k]["drop"] for k in keys]
    de=[[ds[k]["drop"]-ds[k]["drop_lo"] for k in keys],[ds[k]["drop_hi"]-ds[k]["drop"] for k in keys]]
    axB.bar(x,drops,0.5,color=[BLUE,RED],yerr=de,capsize=7,ecolor="#1a1a1a"); axB.axhline(0,color="#1a1a1a",lw=1)
    for xi,k in zip(x,keys):
        axB.text(xi,ds[k]["drop_hi"]+0.6,f"{ds[k]['drop']:.1f} pp\n[{ds[k]['drop_lo']:.1f}, {ds[k]['drop_hi']:.1f}]",ha="center",va="bottom",fontsize=9,fontweight="bold")
    axB.set_xticks(x); axB.set_xticklabels(labels); axB.set_ylabel("Evasion drop (pp)")
    axB.set_title("(B)  Drop is real for both vendors (95% CI excludes 0)",fontsize=11)
    axB.set_ylim(0,max(ds[k]["drop_hi"] for k in keys)+6); axB.spines[["top","right"]].set_visible(False)
    fig.suptitle("Behavioural camouflage evades oversight monitors across vendors  (N=99)",fontsize=12,fontweight="bold",y=1.02)
    fig.tight_layout()
    fig.savefig(R/"comparison_figure.png",dpi=200,bbox_inches="tight"); fig.savefig(R/"comparison_figure.pdf",bbox_inches="tight"); plt.close(fig)
for k in MONITORS: per_monitor_figure(k)
comparison_figure()
print("saved results/claude_figure, gemini_figure, comparison_figure (png+pdf)")
