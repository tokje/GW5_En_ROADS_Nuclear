"""
make_figures.py
===============

Reproduces Figures 2-6 and Table 3 of

    "What If the World Put Nuclear Power First?
     A Counterfactual Analysis with the En-ROADS Climate Simulator"

from the En-ROADS data exported with extract_enroads.js (one CSV per
simulation, stored in data/). It also prints every number quoted in the
Results section, so each statement in the report can be traced to the data.

Usage
-----
    python make_figures.py

Output
------
    figures/fig2_nuclear.pdf          Nuclear primary energy and capacity
    figures/fig3_energy_mix.pdf       Energy mix and crowding out
    figures/fig4_ghg_temperature.pdf  Emissions and temperature
    figures/fig5_economy.pdf          Prices, revenue and GDP growth
    figures/fig6_pm25.pdf             PM2.5 emissions
    results/table3.csv                Key results of all simulations (Table 3)
    results/key_numbers.txt           All numbers quoted in Section 4

Requirements: Python 3.9+, numpy, pandas, matplotlib.

Data format (data/enroads_<run>.csv)
------------------------------------
    first line : "# url=<En-ROADS link used for the export>"
    columns    : graph, series, year, value
    series     : "baseline" or "scenario" for single-variable graphs, or the
                 energy source for "Global Sources of Primary Energy".
En-ROADS version 26.11, annual values 2000-2100.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIGS = HERE / "figures"
RES = HERE / "results"
FIGS.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# Simulations (see Section 3.3 and Appendix A of the report)
# --------------------------------------------------------------------------
RUNS = {  # file suffix -> label in Table 3 (data/enroads_baseline.csv is also read)
    "main": "Main scenario",
    "counterfactual": "Counterfactual (nuclear at status quo)",
    "no_breakthrough": "Nuclear subsidy without R&D breakthrough",
    "nuclear_only": "Nuclear policy only, applied to baseline",
    "ecs_2.5": "Main scenario, ECS = 2.5 °C",
    "ecs_4.0": "Main scenario, ECS = 4.0 °C",
    "counterfactual_ecs_2.5": "Counterfactual, ECS = 2.5 °C",
    "counterfactual_ecs_4.0": "Counterfactual, ECS = 4.0 °C",
    "pr_0.90": "Main scenario, nuclear PR = 0.90",
    "pr_1.00": "Main scenario, nuclear PR = 1.00",
}

# Graph names in En-ROADS
TEMP = "Temperature Change"
GHG = "Greenhouse Gas Net Emissions"
NUC = "Nuclear Primary Energy Demand"
CAP = "Nuclear Capacity"
MIX = "Global Sources of Primary Energy"
PELEC = "Price of Electricity"
PENERGY = "Average Price of Energy to Consumers"
REV = "Net Revenue from Energy Taxes & Subsidies"
GDPPC = "GDP per Capita"
GROWTH = "GDP per Capita Growth Rate"
DAMAGE = "Reduction in GDP from Climate Impacts"
PM = "Air Pollution from Energy"

# IPCC AR6 best-estimate warming for 2081-2100 (IPCC, 2021, Table SPM.1)
SSP = {"SSP1-2.6": 1.8, "SSP2-4.5": 2.7, "SSP3-7.0": 3.6}

# --------------------------------------------------------------------------
# Plot style: serif font matching the report, light vector output
# --------------------------------------------------------------------------
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "0.9",
    "grid.linewidth": 0.6,
    "lines.linewidth": 1.6,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
})

STYLE = {  # run -> (label, colour, line style)
    "main": ("Main scenario", "#1f6fd1", "-"),
    "counterfactual": ("Counterfactual (nuclear at status quo)", "#e8743b", "--"),
    "no_breakthrough": ("Nuclear subsidy without R&D breakthrough", "#19a979", "-."),
    "baseline": ("Baseline", "#404040", "-"),
}
SOURCE_COLOURS = {
    "Coal": "#6a4cd6", "Oil": "#ef6c3a", "Natural gas": "#2d7fd9",
    "Nuclear": "#22b28c", "New zero-carbon": "#f2a516", "Bioenergy": "#ef7fa8",
    "Renewables": "#118a2b",
}
STACK_ORDER = ["Coal", "Oil", "Natural gas", "Nuclear", "New zero-carbon",
               "Bioenergy", "Renewables"]
SOURCE = "Data: En-ROADS version 26.11."


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_run(run: str) -> pd.DataFrame:
    """Read one exported simulation into a long table."""
    df = pd.read_csv(DATA / f"enroads_{run}.csv", comment="#")
    df["year"] = df["year"].astype(int)
    return df


DFS = {run: load_run(run) for run in RUNS}
# The baseline export (En-ROADS with default settings) is needed only for the
# baseline energy mix; all other baseline series are also in every export.
DFS["baseline"] = load_run("baseline")


def series(run: str, graph: str, which: str = "scenario") -> pd.Series:
    """Annual values (index = year) of one series of one graph in one run.
    which = "scenario", "baseline" or an energy source name."""
    df = DFS[run]
    s = df[(df.graph == graph) & (df.series == which)].set_index("year")["value"]
    if s.empty:
        raise KeyError(f"No data for {graph!r} / {which!r} in run {run!r}")
    return s.sort_index()


def base(graph: str) -> pd.Series:
    """Baseline series (identical in every export; taken from the main run)."""
    return series("main", graph, "baseline")


def run_or_base(run: str, graph: str) -> pd.Series:
    return base(graph) if run == "baseline" else series(run, graph)


def plot_runs(ax, graph, runs, start=2000):
    for run in runs:
        label, colour, ls = STYLE[run]
        s = run_or_base(run, graph).loc[start:]
        ax.plot(s.index, s.values, ls, color=colour, label=label,
                lw=1.2 if run == "baseline" else 1.8)


def panel_label(ax, text):
    ax.text(-0.02, 1.04, text, transform=ax.transAxes, fontweight="bold",
            ha="right", va="bottom")


# --------------------------------------------------------------------------
# Figure 2: nuclear expansion
# --------------------------------------------------------------------------
def figure2():
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 2.7))
    plot_runs(a, NUC, ["main", "no_breakthrough", "counterfactual", "baseline"])
    for x, txt in [(2038, "R&D\nbreakthrough"), (2080, "subsidy\nends")]:
        a.axvline(x, color="0.55", lw=0.8)
        a.text(x - 1.5, 0.97, txt, transform=a.get_xaxis_transform(),
               ha="right", va="top", fontsize=7, color="0.35")
    a.set_ylabel(r"Nuclear primary energy (EJ yr$^{-1}$)")
    a.set_xlim(2000, 2100)
    a.set_ylim(0, 100)          # head-room for the labels of the vertical lines
    panel_label(a, "(a)")

    for run in ["main", "counterfactual", "baseline"]:
        cap = run_or_base(run, CAP)
        rel = (cap / cap.loc[2020]).loc[2020:]
        label, colour, ls = STYLE[run]
        b.plot(rel.index, rel.values, ls, color=colour,
               lw=1.2 if run == "baseline" else 1.8)
    b.plot([2050], [3.0], "o", mfc="white", mec="black", ms=6, zorder=5)
    b.annotate("COP28 target:\n3× by 2050", xy=(2050, 3.0), xytext=(2026, 5.2),
               fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.6))
    b.set_ylabel("Nuclear capacity relative to 2020 (–)")
    b.set_xlim(2020, 2100)
    b.set_ylim(bottom=0)
    panel_label(b, "(b)")

    handles, labels = a.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.12))
    fig.tight_layout()
    fig.savefig(FIGS / "fig2_nuclear.pdf")
    fig.savefig(FIGS / "fig2_nuclear.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 3: energy mix and crowding out
# --------------------------------------------------------------------------
def mix_table(run: str) -> pd.DataFrame:
    df = DFS[run]
    t = df[df.graph == MIX].pivot(index="year", columns="series", values="value")
    return t[STACK_ORDER]


def figure3(year=2080):
    main, cf = mix_table("main"), mix_table("counterfactual")
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.3, 4.3),
                               gridspec_kw={"height_ratios": [1.6, 1]})
    a.stackplot(main.index, *[main[c] for c in STACK_ORDER],
                colors=[SOURCE_COLOURS[c] for c in STACK_ORDER],
                labels=STACK_ORDER, edgecolor="white", linewidth=0.3)
    a.set_xlim(2000, 2100)
    a.set_ylabel(r"Primary energy (EJ yr$^{-1}$)")
    h, l = a.get_legend_handles_labels()
    a.legend(h[::-1], l[::-1], loc="center left", bbox_to_anchor=(1.01, 0.6),
             frameon=False)
    a.grid(False)
    panel_label(a, "(a)")

    diff = (main.loc[year] - cf.loc[year])
    diff = diff[diff.abs() > 0.05].sort_values(key=np.abs)
    colours = [SOURCE_COLOURS[c] for c in diff.index]
    b.barh(diff.index, diff.values, color=colours, height=0.6)
    for y, v in enumerate(diff.values):
        b.text(v + (1 if v > 0 else -1), y, f"{v:+.1f}".replace("-", "\u2212"), va="center",
               ha="left" if v > 0 else "right", fontsize=7)
    b.axvline(0, color="0.3", lw=0.8)
    b.set_xlabel(f"Change in primary energy in {year}, main scenario minus "
                 r"counterfactual (EJ yr$^{-1}$)")
    lim = np.ceil(diff.abs().max() / 10) * 10 + 10
    b.set_xlim(-lim, lim)
    b.grid(axis="y", visible=False)
    panel_label(b, "(b)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig3_energy_mix.pdf")
    fig.savefig(FIGS / "fig3_energy_mix.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 4: emissions and temperature
# --------------------------------------------------------------------------
def figure4():
    runs = ["main", "counterfactual", "baseline"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 2.7))
    plot_runs(a, GHG, runs)
    a.set_ylabel(r"Net GHG emissions (Gt CO$_2$-eq yr$^{-1}$)")
    a.set_xlim(2000, 2100)
    a.set_ylim(bottom=0)
    panel_label(a, "(a)")

    plot_runs(b, TEMP, runs)
    for name, value in SSP.items():
        b.plot([2081, 2100], [value, value], color="0.6", lw=3,
               solid_capstyle="butt")
        b.text(2102, value, name, va="center", fontsize=7)
    b.set_ylabel("Temperature change (°C)")
    b.set_xlim(2000, 2100)
    panel_label(b, "(b)")

    handles, labels = a.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.07))
    fig.tight_layout()
    fig.savefig(FIGS / "fig4_ghg_temperature.pdf")
    fig.savefig(FIGS / "fig4_ghg_temperature.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 5: economic indicators
# --------------------------------------------------------------------------
def figure5():
    runs = ["main", "counterfactual", "baseline"]
    fig, axes = plt.subplots(2, 2, figsize=(6.3, 4.4))
    (a, b), (c, d) = axes

    plot_runs(a, PELEC, runs)
    p2020 = base(PELEC).loc[2020]
    a.axhline(p2020, color="0.55", lw=0.8)
    a.text(2098, p2020 + 0.002, "2020 level", ha="right", fontsize=7, color="0.35")
    a.set_ylabel(r"Electricity price (US\$ kWh$^{-1}$)")
    panel_label(a, "(a)")

    plot_runs(b, PENERGY, runs)
    b.set_ylabel(r"Average energy price (US\$ GJ$^{-1}$)")
    panel_label(b, "(b)")

    plot_runs(c, REV, runs)
    c.axhline(0, color="0.3", lw=0.8)
    for x, txt, side in [(2065, "renewables\nsubsidy ends", "right"),
                         (2080, "nuclear\nsubsidy ends", "left")]:
        c.axvline(x, color="0.55", lw=0.8)
        c.text(x + (-1 if side == "right" else 1), 0.98, txt,
               transform=c.get_xaxis_transform(), ha=side, va="top",
               fontsize=7, color="0.35")
    c.set_ylim(top=3.0)         # head-room for the labels
    c.set_ylabel(r"Net revenue (10$^{12}$ US\$ yr$^{-1}$)")
    panel_label(c, "(c)")

    plot_runs(d, GROWTH, runs, start=2025)
    d.set_ylabel(r"GDP per capita growth (% yr$^{-1}$)")
    d.set_xlim(2025, 2100)
    panel_label(d, "(d)")

    for ax in (a, b, c):
        ax.set_xlim(2000, 2100)
    handles, labels = a.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.03))
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_economy.pdf")
    fig.savefig(FIGS / "fig5_economy.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 6: PM2.5
# --------------------------------------------------------------------------
def figure6():
    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    plot_runs(ax, PM, ["main", "counterfactual", "baseline"])
    ax.set_ylabel(r"PM$_{2.5}$ emissions (Mt yr$^{-1}$)")
    ax.set_xlim(2000, 2100)
    ax.set_ylim(bottom=0)
    ax.legend(loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig(FIGS / "fig6_pm25.pdf")
    fig.savefig(FIGS / "fig6_pm25.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Table 3 and the numbers quoted in Section 4
# --------------------------------------------------------------------------
def table3() -> pd.DataFrame:
    rows = [("Baseline", base(TEMP).loc[2100], base(TEMP).loc[2081:2100].mean(),
             base(NUC).loc[2080], base(GHG).loc[2100])]
    for run, label in RUNS.items():
        rows.append((label, series(run, TEMP).loc[2100],
                     series(run, TEMP).loc[2081:2100].mean(),
                     series(run, NUC).loc[2080], series(run, GHG).loc[2100]))
    t = pd.DataFrame(rows, columns=["Simulation", "T2100 (degC)",
                                    "T mean 2081-2100 (degC)",
                                    "Nuclear 2080 (EJ/yr)", "Net GHG 2100 (Gt CO2-eq/yr)"])
    t.to_csv(RES / "table3.csv", index=False, float_format="%.3f")
    return t


def key_numbers() -> str:
    m, cf, nb, no = "main", "counterfactual", "no_breakthrough", "nuclear_only"
    L = []
    add = L.append
    pct = lambda x, r: 100 * (x - r) / r

    add("4.1 Nuclear expansion")
    nuc = series(m, NUC)
    add(f"  Nuclear primary energy, main: 2030 {nuc[2030]:.1f}, 2050 {nuc[2050]:.1f}, "
        f"peak {nuc.max():.1f} EJ/yr in {nuc.idxmax()}, 2100 {nuc[2100]:.1f}")
    for run, lab in [(m, "main"), (cf, "counterfactual"), ("baseline", "baseline")]:
        cap = run_or_base(run, CAP)
        rel = cap / cap[2020]
        add(f"  Capacity relative to 2020, {lab}: 2050 {rel[2050]:.2f}"
            + (f", peak {rel.max():.2f} in {rel.idxmax()}" if run == m else ""))
    add(f"  Nuclear 2080: counterfactual {series(cf, NUC)[2080]:.1f}, "
        f"subsidy adds {series(nb, NUC)[2080] - series(cf, NUC)[2080]:.1f}, "
        f"breakthrough adds {nuc[2080] - series(nb, NUC)[2080]:.1f} EJ/yr")
    rel = series(m, CAP) / series(m, CAP)[2020]
    add(f"  Capacity first reaches 3 times its 2020 value in {rel[rel >= 3].index.min()}")
    for pr in ["pr_0.90", "pr_1.00"]:
        add(f"  {pr}: nuclear 2080 changes by {pct(series(pr, NUC)[2080], nuc[2080]):+.0f} %")

    add("4.2 Energy mix")
    mm, mc = mix_table(m), mix_table(cf)
    tot = mm.sum(axis=1)
    for y in (2050, 2080):
        add(f"  Share of primary energy {y}: nuclear {100*mm.Nuclear[y]/tot[y]:.1f} %, "
            f"renewables {100*mm.Renewables[y]/tot[y]:.1f} %")
    add(f"  Coal: 2020 {mm.Coal[2020]:.1f} -> 2080 {mm.Coal[2080]:.1f} EJ/yr; "
        f"oil 2080 {mm.Oil[2080]:.1f}; gas 2080 {mm['Natural gas'][2080]:.1f}")
    nz = mm["New zero-carbon"]
    add(f"  New zero-carbon: first year above 1 EJ/yr {nz[nz > 1].index.min()}; "
        f"2100 {nz[2100]:.1f} EJ/yr ({100*nz[2100]/tot[2100]:.1f} % of primary energy)")
    d = mm.loc[2080] - mc.loc[2080]
    add("  Main minus counterfactual, 2080 (EJ/yr): "
        + ", ".join(f"{k} {v:+.1f}" for k, v in d.items()))
    add(f"  Share of added nuclear that replaced renewables: "
        f"{-d.Renewables / d.Nuclear:.2f}")
    dn = mix_table(no).loc[2080] - mix_table("baseline").loc[2080]
    add(f"  Nuclear policy on baseline, 2080: nuclear {dn.Nuclear:+.1f}, renewables "
        f"{dn.Renewables:+.1f} EJ/yr; share replacing renewables "
        f"{-dn.Renewables / dn.Nuclear:.2f}")

    add("4.3 Emissions and temperature")
    g = series(m, GHG)
    add(f"  Net GHG, main: peak {g.loc[2020:].max():.1f} in {g.loc[2020:].idxmax()}, "
        f"2100 {g[2100]:.1f} ({pct(g[2100], base(GHG)[2100]):.0f} % vs baseline)")
    cum = lambda s: s.loc[2020:2100].sum()
    add(f"  Cumulative GHG 2020-2100 vs baseline: {pct(cum(g), cum(base(GHG))):.0f} %")
    t, tb = series(m, TEMP), base(TEMP)
    add(f"  Temperature 2100: main {t[2100]:.3f}, baseline {tb[2100]:.3f} degC; "
        f"mean 2081-2100: main {t.loc[2081:2100].mean():.3f}, "
        f"baseline {tb.loc[2081:2100].mean():.3f}")
    add(f"  Warming rate 2090-2100: main {(t[2100]-t[2090]):.3f}, "
        f"baseline {(tb[2100]-tb[2090]):.3f} degC per decade")

    add("4.4 Economy")
    pe, peb, pecf = series(m, PELEC), base(PELEC), series(cf, PELEC)
    f = pe.loc[2027:]
    add(f"  Electricity price 2020 {peb[2020]:.4f}; main max after 2027 {f.max():.4f} "
        f"in {f.idxmax()}; 2080 {pe[2080]:.4f} US$/kWh")
    add(f"  Largest year-to-year change after 2027: "
        f"{100*f.pct_change().abs().max():.1f} %")
    rel = 100 * (pe - peb) / peb
    add(f"  Main vs baseline 2040-2100: {rel.loc[2040:].min():.1f} to {rel.loc[2040:].max():.1f} %;"
        f" main vs counterfactual 2080: {pct(pe[2080], pecf[2080]):.0f} %")
    en, enb, encf = series(m, PENERGY), base(PENERGY), series(cf, PENERGY)
    add(f"  Average energy price: 2020 {en[2020]:.1f} -> 2100 {en[2100]:.1f} US$/GJ, "
        f"{pct(en[2100], enb[2100]):.0f} % vs baseline, "
        f"{pct(en[2100], encf[2100]):.0f} % vs counterfactual")
    rele = 100 * (en - enb) / enb
    add(f"  Average energy price vs baseline: max {rele.max():.1f} % in {rele.idxmax()}")
    r, rcf = series(m, REV), series(cf, REV)
    pos = r.loc[2025:][r.loc[2025:] > 0]
    add(f"  Net revenue positive from {pos.index.min()}; peak {r.max():.2f} "
        f"x10^12 US$/yr in {r.idxmax()}")
    add(f"  Cost of nuclear policy (counterfactual minus main revenue), 2028-2100: "
        f"{(rcf - r).loc[2028:2100].sum():.1f} x10^12 US$ "
        f"(mean {(rcf - r).loc[2028:2100].mean():.2f} per year)")
    gp, gpb, gpcf = series(m, GDPPC), base(GDPPC), series(cf, GDPPC)
    cagr = lambda s: 100 * ((s[2100] / s[2020]) ** (1 / 80) - 1)
    gr, grb = series(m, GROWTH), base(GROWTH)
    add(f"  GDP per capita growth 2020-2100: compound {cagr(gp):.2f} vs {cagr(gpb):.2f} % per year;"
        f" mean of annual rates {gr.loc[2020:2100].mean():.2f} vs {grb.loc[2020:2100].mean():.2f};"
        f" minimum after 2025 {gr.loc[2025:].min():.2f}")
    add(f"  GDP per capita 2100: {pct(gp[2100], gpb[2100]):.1f} % vs baseline; "
        f"nuclear policy adds {pct(gp[2100], gpcf[2100]):.1f} %")
    add(f"  Reduction in GDP from climate impacts, 2100: main {series(m, DAMAGE)[2100]:.1f} %, "
        f"baseline {base(DAMAGE)[2100]:.1f} %, counterfactual {series(cf, DAMAGE)[2100]:.1f} %")

    add("4.5 Air pollution")
    p, pb, pcf = series(m, PM), base(PM), series(cf, PM)
    add(f"  PM2.5 main: peak {p.max():.1f} Mt/yr in {p.idxmax()}, 2100 {p[2100]:.1f} "
        f"({pct(p[2100], pb[2100]):.0f} % vs baseline, "
        f"{pct(p[2100], pcf[2100]):.0f} % vs counterfactual)")
    add(f"  Baseline minimum in {pb.loc[2025:].idxmin()}")

    add("4.6 Contribution of nuclear power")
    T = {k: series(k, TEMP)[2100] for k in RUNS}
    Tb = tb[2100]
    add(f"  Avoided warming main vs baseline: {Tb - T[m]:.3f} degC")
    add(f"  Nuclear contribution T_cf - T_main: {T[cf] - T[m]:.3f} degC; "
        f"f_nuc = {100*(T[cf]-T[m])/(Tb-T[m]):.1f} %")
    add(f"  Subsidy: {T[cf] - T[nb]:.3f} degC; breakthrough: {T[nb] - T[m]:.3f} degC")
    add(f"  Cumulative GHG main vs counterfactual: "
        f"{pct(cum(g), cum(series(cf, GHG))):.1f} %")
    add(f"  Nuclear policy on baseline: lowers 2100 warming by {Tb - T[no]:.3f} degC")
    add(f"  ECS 2.5 / 4.0: {T['ecs_2.5']:.2f} / {T['ecs_4.0']:.2f} degC; "
        f"2020 warming {series('ecs_2.5', TEMP)[2020]:.2f} / {series('ecs_4.0', TEMP)[2020]:.2f}")
    for e in ["2.5", "4.0"]:
        dT = T[f"counterfactual_ecs_{e}"] - T[f"ecs_{e}"]
        add(f"  ECS {e}: nuclear contribution T_cf - T_main {dT:.3f} degC")
    add(f"  PR 0.90 / 1.00 change 2100 warming by "
        f"{T['pr_0.90'] - T[m]:+.3f} / {T['pr_1.00'] - T[m]:+.3f} degC")
    text = "\n".join(L)
    (RES / "key_numbers.txt").write_text(text + "\n", encoding="utf-8")
    return text


if __name__ == "__main__":
    figure2()
    figure3()
    figure4()
    figure5()
    figure6()
    print(table3().round(3).to_string(index=False))
    print()
    print(key_numbers())
    print(f"\nFigures written to {FIGS}")
