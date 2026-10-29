"""Build the tables, numbers and charts for the Project 1 slide deck.

Runs the professor's 20 regressions once (ADH_Assignment1_python.py, unchanged)
and writes everything to output/main (slide-ready) and output/backup (technical).

Run: python make_tables.py
"""

import sys

sys.dont_write_bytecode = True  # keep the project folder free of __pycache__

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
# The professor's script sits next to this file locally, or in provided_code/ in the group repo.
PROVIDED = HERE / "provided_code" if (HERE / "provided_code").is_dir() else HERE
sys.path.insert(0, str(PROVIDED))

from ADH_Assignment1_python import run

DATA = HERE / "workfile_china.dta"
MAIN = HERE / "output" / "main"
BACKUP = HERE / "output" / "backup"

# Labels used by run() -> short keys and plain-language names for the slides.
VERSIONS = {
    "Stacked baseline": ("original", "Original study"),
    "1990–2000": ("1990s", "1990s only"),
    "2000–2007": ("2000s", "2000s only"),
    "Stacked with year-specific 1990 manufacturing-share slopes":
        ("better_control", "With better control"),
}
VERSION_ORDER = ["original", "1990s", "2000s", "better_control"]
OUTCOMES = {
    "d_sh_empl_mfg": "Factory jobs",
    "d_sh_empl_nmfg": "Jobs in other sectors",
    "d_sh_unempl": "Unemployment",
    "d_sh_nilf": "Leaving the workforce",
    "d_avg_lnwkwage": "Pay",
}
UNITS = {
    "d_sh_empl_mfg": "pp of working-age adults",
    "d_sh_empl_nmfg": "pp of working-age adults",
    "d_sh_unempl": "pp of working-age adults",
    "d_sh_nilf": "pp of working-age adults",
    "d_avg_lnwkwage": "% of average weekly pay",
}
# Published ADH (2013) estimates: Table 5 Panel B (all education levels) and Table 6 Panel A col. 1.
ADH_PUBLISHED = {
    "d_sh_empl_mfg": (-0.596, 0.099),
    "d_sh_empl_nmfg": (-0.178, 0.137),
    "d_sh_unempl": (0.221, 0.058),
    "d_sh_nilf": (0.553, 0.150),
    "d_avg_lnwkwage": (-0.759, 0.253),
}
EXPOSURE = "d_tradeusch_pw"
INSTRUMENT = "d_tradeotch_pw_lag"


def weighted_quantile(values, weights, q):
    order = np.argsort(values)
    values, weights = np.asarray(values)[order], np.asarray(weights)[order]
    return np.interp(q, np.cumsum(weights) / weights.sum(), values)


def weighted_corr(x, y, w):
    cov = np.cov(x, y, aweights=w)
    return cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])


def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


# ---------------------------------------------------------------- Step 1
def collect_results():
    """Run the 20 regressions once and keep everything the tables need."""
    rows, interactions, raw = [], [], {}
    for label, outcome, res in run(DATA, display=False):
        version, version_label = VERSIONS[label]
        raw[(version, outcome)] = res
        fs = res.first_stage
        fs_ols = fs.individual[EXPOSURE]
        ci = res.conf_int().loc[EXPOSURE]
        rows.append({
            "version": version,
            "version_label": version_label,
            "outcome": outcome,
            "outcome_label": OUTCOMES[outcome],
            "coef": res.params[EXPOSURE],
            "se": res.std_errors[EXPOSURE],
            "pvalue": res.pvalues[EXPOSURE],
            "ci_low": ci["lower"],
            "ci_high": ci["upper"],
            "nobs": int(res.nobs),
            "r2": res.rsquared,
            "fs_coef": fs_ols.params[INSTRUMENT],
            "fs_se": fs_ols.std_errors[INSTRUMENT],
            "fs_F": fs.diagnostics.loc[EXPOSURE, "f.stat"],
        })
        if version == "better_control":
            for name in res.params.index:
                if name.endswith(".yr#c.mshare90"):
                    interactions.append({
                        "outcome": outcome,
                        "outcome_label": OUTCOMES[outcome],
                        "term": name,
                        "period": "1990s" if name.startswith("1990") else "2000s",
                        "coef": res.params[name],
                        "se": res.std_errors[name],
                        "pvalue": res.pvalues[name],
                    })
    results = pd.DataFrame(rows)
    results["stars"] = results["pvalue"].map(stars)
    results["version"] = pd.Categorical(results["version"], VERSION_ORDER, ordered=True)
    results["outcome"] = pd.Categorical(results["outcome"], list(OUTCOMES), ordered=True)
    results = results.sort_values(["outcome", "version"]).reset_index(drop=True)
    return results, pd.DataFrame(interactions), raw


# ---------------------------------------------------------------- Step 2
def slide_numbers(results):
    """Translate coefficients into plain terms and gather the 'why' facts."""
    df = pd.read_stata(DATA, convert_categoricals=False)
    df["mshare90"] = (df["l_shind_manuf_cbp"] * (df["yr"] == 1990)).groupby(df["czone"]).transform("max")
    w = "timepwt48"
    numbers = []

    def add(name, value, description):
        numbers.append({"name": name, "value": value, "description": description})

    # Exposure gap, as in Lecture 5: population-weighted 75th vs 25th percentile
    # of 2000-2007 exposure growth, converted from per-decade to the actual 7 years.
    gaps = {}
    for year, period in [(1990, "1990s"), (2000, "2000s")]:
        d = df[df["yr"] == year]
        gaps[period] = (weighted_quantile(d[EXPOSURE], d[w], 0.75)
                        - weighted_quantile(d[EXPOSURE], d[w], 0.25))
        add(f"gap_per_decade_{period}", gaps[period],
            f"75th minus 25th percentile of exposure growth, {period} ($1,000 per worker per decade, weighted)")
    gap = gaps["2000s"] * 0.7
    add("gap_2000_2007", gap,
        "Heavily vs. lightly exposed region (75th vs. 25th pct.), actual 2000-2007 exposure growth "
        "($1,000 per worker); Lecture 5 uses 1.06")

    # Shock size: average exposure growth per decade, by period.
    means = {}
    for year, period in [(1990, "1990s"), (2000, "2000s")]:
        d = df[df["yr"] == year]
        means[period] = np.average(d[EXPOSURE], weights=d[w])
        add(f"mean_exposure_{period}", means[period],
            f"Average growth in Chinese import exposure, {period} ($1,000 per worker per decade, weighted)")
    add("shock_ratio_2000s_vs_1990s", means["2000s"] / means["1990s"],
        "How many times faster exposure grew in the 2000s than the 1990s")

    # Why results change: factory-heavy regions and exposure move together,
    # and factory-heavy regions lost factory jobs faster in the 2000s anyway.
    for year, period in [(1990, "1990s"), (2000, "2000s")]:
        d = df[df["yr"] == year]
        add(f"corr_exposure_mshare90_{period}", weighted_corr(d[EXPOSURE], d["mshare90"], d[w]),
            f"Correlation between exposure growth and 1990 factory share, {period} (weighted)")

    cutoffs = df[df["yr"] == 1990]
    q25 = weighted_quantile(cutoffs["mshare90"], cutoffs[w], 0.25)
    q75 = weighted_quantile(cutoffs["mshare90"], cutoffs[w], 0.75)
    df["factory_group"] = np.select(
        [df["mshare90"] >= q75, df["mshare90"] <= q25], ["Most factory-heavy 25%", "Least factory-heavy 25%"],
        "Middle 50%")
    why = (df.groupby(["factory_group", "yr"])
             .apply(lambda g: pd.Series({
                 "factory_share_change_pp": np.average(g["d_sh_empl_mfg"], weights=g[w]),
                 "exposure_growth": np.average(g[EXPOSURE], weights=g[w]),
                 "avg_1990_factory_share": np.average(g["mshare90"], weights=g[w]),
                 "n_regions": len(g),
             }), include_groups=False)
             .reset_index())
    why["period"] = why["yr"].map({1990: "1990s", 2000: "2000s"})

    # Effects in plain terms: coefficient x gap (and the same for the 95% CI).
    plain = results[["version", "version_label", "outcome", "outcome_label", "coef", "ci_low", "ci_high", "pvalue"]].copy()
    for col in ["coef", "ci_low", "ci_high"]:
        plain[f"effect_{col}"] = plain[col] * gap
    plain["unit"] = plain["outcome"].map(UNITS)
    plain = plain.drop(columns=["coef", "ci_low", "ci_high"]).rename(columns={
        "effect_coef": "effect", "effect_ci_low": "effect_ci_low", "effect_ci_high": "effect_ci_high"})

    return pd.DataFrame(numbers), plain, why


def factory_trend(raw):
    """Extra drop in the factory-job rate for a region with 10 more points of
    factory jobs in 1990, holding China exposure fixed, by decade.

    Comes from the 'better control' regression for factory jobs. That model
    keeps ADH's start-of-period factory share and adds 1990 share x decade, so:
      1990s: start-of-period share IS the 1990 share -> slope = b_start + b_1990s
      2000s: 1990 share also moves the 2000 share (slope k) -> slope = b_2000s + k * b_start
    """
    df = pd.read_stata(DATA, convert_categoricals=False)
    d = df[df["yr"] == 2000].copy()
    d["mshare90"] = d["czone"].map(df[df["yr"] == 1990].set_index("czone")["l_shind_manuf_cbp"])
    cov = np.cov(d["l_shind_manuf_cbp"], d["mshare90"], aweights=d["timepwt48"])
    k = cov[0, 1] / cov[1, 1]

    res = raw[("better_control", "d_sh_empl_mfg")]
    names = ["l_shind_manuf_cbp", "1990.yr#c.mshare90", "2000.yr#c.mshare90"]
    b, V = res.params[names].values, res.cov.loc[names, names].values
    rows = []
    for period, weights in [("1990s", np.array([1, 1, 0])), ("2000s", np.array([k, 0, 1]))]:
        weights = 10 * weights
        est, se = weights @ b, np.sqrt(weights @ V @ weights)
        rows.append({"period": period, "effect_pp": est, "se": se,
                     "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se, "k_2000_on_1990_share": k})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- Step 4
UCLA = {
    "blue": "#2774AE", "darker_blue": "#005587", "darkest_blue": "#003B5C",
    "lighter_blue": "#8BB8E8", "lightest_blue": "#DAEBFE",
    "gold": "#FFD100", "darker_gold": "#FFC72C", "darkest_gold": "#FFB81C",
    "gray": "#8C8C8C", "light_gray": "#EEF1F4",
}
VERDICT_STYLE = {  # cell fill, text color, cell word
    "Holds": ("#CDE8C4", "#1E5631", "HOLDS"),
    "Weaker": ("#FFE8A3", "#6B4E00", "WEAKER"),
    "Gone": ("#F6C6C6", "#8B1E1E", "GONE"),
    "Reverses": ("#F6C6C6", "#8B1E1E", "REVERSES"),
    "None": (UCLA["light_gray"], "#555555", "–"),
}
# Google Slides: Arial, 16:9 PNG. Beamer: Computer Modern Sans (cmss10), 4:3, vector PDF + PNG.
STYLES = {
    "google": {"font": ["Arial", "DejaVu Sans"], "base": 17, "width": 12.0, "formats": ["png"]},
    "beamer": {"font": ["cmss10", "DejaVu Sans"], "base": 8, "width": 4.6, "formats": ["pdf", "png"]},
}
HERO_OUTCOMES = ["d_sh_empl_mfg", "d_sh_unempl", "d_sh_nilf", "d_avg_lnwkwage"]


def use_style(name):
    import matplotlib as mpl
    style = STYLES[name]
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams.update({
        "font.family": style["font"],
        "font.size": style["base"],
        "axes.unicode_minus": False,
        "axes.formatter.use_mathtext": False,
        "mathtext.fontset": "cm",
        "text.color": UCLA["darkest_blue"],
        "axes.labelcolor": UCLA["darkest_blue"],
        "xtick.color": UCLA["darkest_blue"],
        "ytick.color": UCLA["darkest_blue"],
        "axes.edgecolor": UCLA["gray"],
        "savefig.dpi": 300,
        "pdf.fonttype": 42,
    })
    return style


def save(fig, folder, stem, style):
    folder.mkdir(parents=True, exist_ok=True)
    for ext in style["formats"]:
        fig.savefig(folder / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.08, facecolor="white")


def fmt(value, outcome):
    unit = "%" if outcome == "d_avg_lnwkwage" else " pp"
    return f"{value:+.2f}{unit}".replace("-", "−")


def scorecard_cell(row):
    if row["version"] == "original":
        if row["verdict"] == "No clear effect":
            return UCLA["light_gray"], "#555555", "No clear\neffect"
        arrow = "▼ Down" if row["coef"] < 0 else "▲ Up"
        return UCLA["lightest_blue"], UCLA["darkest_blue"], arrow
    if row["verdict"] == "Disappears or reverses":
        key = "Reverses" if row["pvalue"] < 0.05 else "Gone"
    elif row["verdict"] in ("Holds", "Weaker"):
        key = row["verdict"]
    else:
        key = "None"
    return VERDICT_STYLE[key]


def plot_scorecard(scorecard, name, folder):
    import matplotlib.pyplot as plt
    style = use_style(name)
    w = style["width"]
    fig, ax = plt.subplots(figsize=(w, w * 0.5))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    columns = ["original", "1990s", "2000s", "better_control"]
    headers = ["Original\nstudy", "1990s\nonly", "2000s\nonly", "With better\ncontrol"]
    label_w, gap = 0.32, 0.012
    col_w = (1 - label_w) / len(columns)
    rows = list(OUTCOMES)
    top, header_h = 0.97, 0.17
    row_h = (top - header_h - 0.13) / len(rows)

    for j, header in enumerate(headers):
        x = label_w + j * col_w + col_w / 2
        ax.text(x, top - header_h / 2, header, ha="center", va="center", weight="bold",
                color=UCLA["darkest_blue"], linespacing=1.1)
    ax.plot([label_w - 0.01, 1], [top - header_h + 0.01] * 2, color=UCLA["blue"], lw=2)

    for i, outcome in enumerate(rows):
        y = top - header_h - (i + 0.5) * row_h
        ax.text(0.005, y, OUTCOMES[outcome], ha="left", va="center", weight="bold")
        for j, version in enumerate(columns):
            cell = scorecard[(scorecard["outcome"] == outcome) & (scorecard["version"] == version)].iloc[0]
            fill, color, word = scorecard_cell(cell)
            x0 = label_w + j * col_w + gap / 2
            ax.add_patch(plt.Rectangle((x0, y - row_h / 2 + gap / 2), col_w - gap, row_h - gap,
                                       facecolor=fill, edgecolor="none"))
            ax.text(x0 + (col_w - gap) / 2, y, word, ha="center", va="center", color=color,
                    weight="bold" if version != "original" else "normal", linespacing=1.0,
                    fontsize=style["base"] * (0.75 if "\n" in word else 0.88 if len(word) > 6 else 1.0))

    ax.text(0.005, 0.04,
            "HOLDS: same direction, statistically reliable      WEAKER: same direction, not reliable\n"
            "GONE: direction flips, not reliable                     REVERSES: direction flips, reliable",
            ha="left", va="center", fontsize=style["base"] * 0.62, color=UCLA["gray"])
    save(fig, folder, "scorecard", style)
    plt.close(fig)


def plot_hero(plain, name, folder):
    import matplotlib.pyplot as plt
    style = use_style(name)
    w = style["width"]
    fig, ax = plt.subplots(figsize=(w, w * 0.52))
    series = [("original", "Original study", UCLA["blue"], UCLA["darker_blue"]),
              ("better_control", "With better control", UCLA["darker_gold"], UCLA["darkest_gold"])]
    height = 0.36
    positions = np.arange(len(HERO_OUTCOMES))[::-1]
    shown = plain["outcome"].isin(HERO_OUTCOMES) & plain["version"].isin([s[0] for s in series])
    span = plain.loc[shown, ["effect_ci_low", "effect_ci_high"]]
    reach = span.abs().max().max()

    for k, (version, label, color, edge) in enumerate(series):
        d = plain[plain["version"] == version].set_index("outcome").loc[HERO_OUTCOMES]
        ys = positions + (height / 2 if k == 0 else -height / 2)
        ax.barh(ys, d["effect"], height=height, color=color, edgecolor=edge, linewidth=0.8, label=label, zorder=2)
        ax.errorbar(d["effect"], ys, xerr=[d["effect"] - d["effect_ci_low"], d["effect_ci_high"] - d["effect"]],
                    fmt="none", ecolor=UCLA["gray"], elinewidth=1.0, capsize=style["base"] * 0.18, alpha=0.8, zorder=3)
        for y, (outcome, r) in zip(ys, d.iterrows()):
            end = r["effect_ci_high"] if r["effect"] >= 0 else r["effect_ci_low"]
            ax.text(end + np.sign(r["effect"] or 1) * reach * 0.03, y, fmt(r["effect"], outcome),
                    ha="left" if r["effect"] >= 0 else "right", va="center",
                    fontsize=style["base"] * 0.82, weight="bold", color=UCLA["darkest_blue"])

    ax.axvline(0, color=UCLA["darkest_blue"], lw=1.2, zorder=4)
    ax.set_xlim(-reach * 1.3, reach * 1.3)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:g}".replace("-", "−"))
    ax.set_yticks(positions)
    ax.set_yticklabels([OUTCOMES[o] for o in HERO_OUTCOMES], weight="bold")
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Extra change in a heavily vs. lightly exposed region, 2000–2007")
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color=UCLA["light_gray"], zorder=0)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    ax.annotate("Bars: best estimate. Thin lines: range of plausible values (95%).\n"
                "Jobs, unemployment and workforce in percentage points of working-age adults; pay in %.",
                xy=(0.5, 0), xycoords=ax.xaxis.label, xytext=(0, -4), textcoords="offset points",
                ha="center", va="top", fontsize=style["base"] * 0.62, color=UCLA["gray"])
    save(fig, folder, "hero_chart", style)
    plt.close(fig)


def plot_why(trend, name, folder):
    import matplotlib.pyplot as plt
    style = use_style(name)
    w = style["width"]
    fig, ax = plt.subplots(figsize=(w * 0.8, w * 0.5))
    colors = [UCLA["lighter_blue"], UCLA["blue"]]
    xs = np.arange(len(trend))
    ax.bar(xs, trend["effect_pp"], width=0.55, color=colors, edgecolor=UCLA["darker_blue"], zorder=2)
    ax.errorbar(xs, trend["effect_pp"], yerr=[trend["effect_pp"] - trend["ci_low"], trend["ci_high"] - trend["effect_pp"]],
                fmt="none", ecolor=UCLA["gray"], elinewidth=1.0, capsize=style["base"] * 0.3, zorder=3)
    for x, r in zip(xs, trend.itertuples()):
        ax.text(x + 0.31, r.effect_pp / 2, f"{r.effect_pp:.1f} pp".replace("-", "−"), ha="left", va="center",
                weight="bold", fontsize=style["base"] * 1.05)
    ratio = trend["effect_pp"].iloc[1] / trend["effect_pp"].iloc[0]
    ax.text(0.5, 1.04, f"≈{ratio:.0f}× faster decline in the 2000s, at the same China exposure",
            transform=ax.transAxes, ha="center", va="bottom", weight="bold", fontsize=style["base"] * 0.95)
    ax.axhline(0, color=UCLA["darkest_blue"], lw=1.2)
    ax.set_xticks(xs)
    ax.set_xticklabels(["1990s", "2000s"], weight="bold")
    ax.set_xlim(-0.6, 1.9)
    ax.set_ylim(trend["ci_low"].min() * 1.1, 0.05)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace("-", "−"))
    ax.set_ylabel("Extra drop in factory-job rate (pp)")
    for side in ["top", "right", "bottom"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color=UCLA["light_gray"], zorder=0)
    ax.text(0.0, -0.12, "Region with 10 more points of factory jobs in 1990 vs. one with fewer, at the same China "
            "exposure.\nThe original study forces both bars to be equal, so the 2000s gap gets blamed on China.",
            transform=ax.transAxes, fontsize=style["base"] * 0.62, color=UCLA["gray"], ha="left", va="top")
    save(fig, folder, "why_chart", style)
    plt.close(fig)


# ---------------------------------------------------------------- Step 3
VERDICT_RULE = (
    "Verdict rule (vs. the original study): if the original effect is statistically significant (p < 0.05), "
    "a check gets 'Holds' when its estimate has the same sign and p < 0.05; 'Weaker' when it has the same sign "
    "but p >= 0.05; 'Disappears or reverses' when its sign flips. If the original found no clear effect "
    "(p >= 0.05), the check gets 'No clear effect' unless it is significant, in which case it is flagged."
)


def verdicts(results):
    original = results[results["version"] == "original"].set_index("outcome")
    rows = []
    for _, r in results.iterrows():
        base = original.loc[r["outcome"]]
        direction = "increase" if r["coef"] > 0 else "decrease"
        if r["version"] == "original":
            if r["pvalue"] < 0.05:
                symbol, text = ("▼" if r["coef"] < 0 else "▲"), f"Significant {direction}"
            else:
                symbol, text = "–", "No clear effect"
        elif base["pvalue"] >= 0.05:
            if r["pvalue"] < 0.05:
                symbol, text = "!", f"Significant {direction} (original found none)"
            else:
                symbol, text = "–", "No clear effect"
        elif np.sign(r["coef"]) != np.sign(base["coef"]):
            symbol, text = "❌", "Disappears or reverses"
        elif r["pvalue"] < 0.05:
            symbol, text = "✅", "Holds"
        else:
            symbol, text = "⚠️", "Weaker"
        rows.append({
            "outcome": r["outcome"], "outcome_label": r["outcome_label"],
            "version": r["version"], "version_label": r["version_label"],
            "symbol": symbol, "verdict": text,
            "coef": r["coef"], "pvalue": r["pvalue"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- Step 5
def period_difference_test():
    """Do the 1990s and 2000s effects differ? One stacked 2SLS where every
    variable (controls, exposure, instrument) gets its own slope per decade.
    Point estimates equal the separate-period regressions; the test uses the
    joint state-clustered covariance."""
    from linearmodels.iv import IV2SLS
    from ADH_Assignment1_python import CONTROLS

    df = pd.read_stata(DATA, convert_categoricals=False)
    regions = [c for c in df.columns if c.startswith("reg")]
    df["_cons"] = 1.0
    late = (df["yr"] == 2000).astype(float)
    period = {"90": 1 - late, "00": late}

    def split(columns):
        return pd.DataFrame({f"{c}_{p}": df[c] * d for c in columns for p, d in period.items()})

    exog = split(CONTROLS + regions + ["_cons"])
    endog, instruments = split([EXPOSURE]), split([INSTRUMENT])
    rows = []
    for outcome in OUTCOMES:
        keep = df[[outcome, EXPOSURE, INSTRUMENT, "timepwt48", "statefip"] + CONTROLS + regions].notna().all(axis=1)
        keep &= df["timepwt48"] > 0
        res = IV2SLS(df.loc[keep, outcome], exog[keep], endog[keep], instruments[keep],
                     weights=df.loc[keep, "timepwt48"]).fit(
            cov_type="clustered", clusters=df.loc[keep, "statefip"], debiased=False)
        b90, b00 = res.params[f"{EXPOSURE}_90"], res.params[f"{EXPOSURE}_00"]
        V = res.cov.loc[[f"{EXPOSURE}_90", f"{EXPOSURE}_00"], [f"{EXPOSURE}_90", f"{EXPOSURE}_00"]].values
        se = np.sqrt(V[0, 0] + V[1, 1] - 2 * V[0, 1])
        z = (b00 - b90) / se
        from scipy.stats import norm
        rows.append({"outcome": outcome, "outcome_label": OUTCOMES[outcome], "coef_1990s": b90,
                     "coef_2000s": b00, "difference": b00 - b90, "se_difference": se,
                     "pvalue": 2 * norm.sf(abs(z))})
    return pd.DataFrame(rows)


def coef_cell(coef, se, p):
    return f"{coef:.3f}{stars(p)}", f"({se:.3f})"


def full_results_table(results):
    """Outcomes x versions, coefficient with stars over (SE), plus N and first-stage F."""
    header = ["", "Original study", "1990s only", "2000s only", "With better control"]
    body = []
    for outcome, label in OUTCOMES.items():
        d = results[results["outcome"] == outcome].set_index("version")
        cells = [coef_cell(d.loc[v, "coef"], d.loc[v, "se"], d.loc[v, "pvalue"]) for v in VERSION_ORDER]
        body.append([label] + [c[0] for c in cells])
        body.append([""] + [c[1] for c in cells])
    first = results.drop_duplicates("version").set_index("version")
    body.append(["Regions × periods (N)"] + [f"{int(first.loc[v, 'nobs']):,}" for v in VERSION_ORDER])
    body.append(["Instrument strength (F)"] + [f"{first.loc[v, 'fs_F']:.1f}" for v in VERSION_ORDER])
    note = ("2SLS estimates of the effect of a $1,000-per-worker rise in Chinese import exposure (instrumented with "
            "Chinese imports to 8 other rich countries). Outcomes are 10-year changes: employment, unemployment and "
            "workforce shares in percentage points of working-age adults; pay in log points. All models include ADH's "
            "full controls and census-division dummies, are weighted by population and cluster SEs by state. "
            "'With better control' adds a separate slope on the 1990 factory share for each decade. "
            "Significance: *** 1%, ** 5%, * 10%.")
    return pd.DataFrame(body, columns=header), note


def replication_table(results):
    rows = []
    original = results[results["version"] == "original"].set_index("outcome")
    for outcome, (coef, se) in ADH_PUBLISHED.items():
        r = original.loc[outcome]
        rows.append([OUTCOMES[outcome], f"{coef:.3f}", f"({se:.3f})", f"{r['coef']:.3f}", f"({r['se']:.3f})",
                     f"{r['coef'] - coef:+.3f}".replace("+0.000", "0.000").replace("-0.000", "0.000")])
    header = ["", "ADH published", "SE", "Our replication", "SE", "Difference"]
    note = ("ADH (2013) Table 5 Panel B, all education levels (first four rows) and Table 6 Panel A, column 1 (pay). "
            "Our replication runs the professor's code on the ADH replication file; N = 1,444 (722 regions × 2 periods).")
    return pd.DataFrame(rows, columns=header), note


def first_stage_table(results):
    first = results.drop_duplicates("version").set_index("version")
    rows = [[first.loc[v, "version_label"], f"{first.loc[v, 'fs_coef']:.3f}", f"({first.loc[v, 'fs_se']:.3f})",
             f"{first.loc[v, 'fs_F']:.1f}", "Strong" if first.loc[v, "fs_F"] > 10 else "Weak"]
            for v in VERSION_ORDER]
    header = ["Version", "First-stage coefficient", "SE", "F-statistic", "Verdict"]
    note = ("First stage: US exposure regressed on the instrument (exposure to Chinese imports in 8 other rich "
            "countries) plus all controls. An F-statistic above 10 is the usual rule of thumb for a strong instrument. "
            "ADH report 0.631 (0.087) for the original specification (Table 3, column 6).")
    return pd.DataFrame(rows, columns=header), note


def period_test_table(test):
    rows = [[r.outcome_label, f"{r.coef_1990s:.3f}", f"{r.coef_2000s:.3f}", f"{r.difference:+.3f}",
             f"({r.se_difference:.3f})", f"{r.pvalue:.3f}"] for r in test.itertuples()]
    header = ["", "1990s only", "2000s only", "Difference", "SE", "p-value"]
    note = ("Test that the 1990s and 2000s effects are equal, from one stacked regression with decade-specific "
            "slopes on every variable (same point estimates as the separate regressions; state-clustered SEs).")
    return pd.DataFrame(rows, columns=header), note


def plot_table(table, note, name, folder, stem):
    import matplotlib.pyplot as plt
    style = use_style(name)
    w = style["width"]
    n_rows, n_cols = len(table) + 1, len(table.columns)
    first_w = 0.28
    col_w = (1 - first_w) / (n_cols - 1)
    row_h = 0.42 if name == "google" else 0.2
    fig, ax = plt.subplots(figsize=(w, row_h * (n_rows + 2.2)))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, n_rows + 2.2)
    size = style["base"] * 0.72

    def x_of(j):
        return 0.005 if j == 0 else first_w + (j - 0.5) * col_w

    top = n_rows + 1.7
    for j, h in enumerate(table.columns):
        ax.text(x_of(j), top, h, ha="left" if j == 0 else "center", va="center", weight="bold", fontsize=size)
    ax.plot([0, 1], [top - 0.5] * 2, color=UCLA["blue"], lw=1.6)
    for i, row in enumerate(table.itertuples(index=False)):
        y = top - 1 - i
        for j, value in enumerate(row):
            ax.text(x_of(j), y, value, ha="left" if j == 0 else "center", va="center", fontsize=size,
                    color=UCLA["gray"] if str(value).startswith("(") else UCLA["darkest_blue"],
                    weight="bold" if j == 0 and value else "normal")
    ax.plot([0, 1], [top - n_rows + 0.5] * 2, color=UCLA["blue"], lw=1.0)
    import textwrap
    ax.text(0.005, top - n_rows + 0.1, textwrap.fill(note, 150 if name == "google" else 120), ha="left", va="top",
            fontsize=style["base"] * 0.5, color=UCLA["gray"])
    save(fig, folder, stem, style)
    plt.close(fig)


def to_latex(table, note, path):
    """Booktabs table to \\input into Beamer (needs \\usepackage{booktabs})."""
    def esc(text):
        return str(text).replace("%", r"\%").replace("$", r"\$").replace("&", r"\&").replace("×", r"$\times$")
    cols = "l" + "c" * (len(table.columns) - 1)
    lines = [r"\begin{tabular}{" + cols + "}", r"\toprule",
             " & ".join(esc(c) for c in table.columns) + r" \\", r"\midrule"]
    lines += [" & ".join(esc(v) for v in row) + r" \\" for row in table.itertuples(index=False)]
    lines += [r"\bottomrule", r"\end{tabular}", "",
              r"{\tiny " + esc(note) + "}"]
    path.write_text("\n".join(lines) + "\n")


def plot_coefficients(results, name, folder):
    import matplotlib.pyplot as plt
    style = use_style(name)
    w = style["width"]
    fig, axes = plt.subplots(1, len(OUTCOMES), figsize=(w, w * 0.42), sharey=True)
    colors = [UCLA["blue"], UCLA["lighter_blue"], UCLA["darker_blue"], UCLA["darkest_gold"]]
    labels = ["Original study", "1990s only", "2000s only", "With better control"]
    ys = np.arange(len(VERSION_ORDER))[::-1]
    for ax, (outcome, title) in zip(axes, OUTCOMES.items()):
        d = results[results["outcome"] == outcome].set_index("version").loc[VERSION_ORDER]
        for y, color, (_, r) in zip(ys, colors, d.iterrows()):
            ax.errorbar(r["coef"], y, xerr=[[r["coef"] - r["ci_low"]], [r["ci_high"] - r["coef"]]],
                        fmt="o", color=color, ecolor=color, elinewidth=1.6, capsize=style["base"] * 0.2,
                        markersize=style["base"] * 0.45)
        ax.axvline(0, color=UCLA["gray"], lw=1, ls="--")
        ax.set_title(title, fontsize=style["base"] * 0.8, weight="bold")
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", labelsize=style["base"] * 0.6)
        ax.xaxis.set_major_formatter(lambda v, _: f"{v:g}".replace("-", "−"))
        for side in ["top", "right", "left"]:
            ax.spines[side].set_visible(False)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels(labels, fontsize=style["base"] * 0.7)
    axes[0].tick_params(axis="y", length=0)
    fig.supxlabel("Effect of a $1,000-per-worker rise in Chinese import exposure (95% confidence interval)",
                  fontsize=style["base"] * 0.7)
    fig.tight_layout()
    save(fig, folder, "coefficient_plot", style)
    plt.close(fig)


def backup_assets(results, test):
    tables = {
        "full_results_table": full_results_table(results),
        "replication_check": replication_table(results),
        "instrument_strength": first_stage_table(results),
        "period_difference_test": period_test_table(test),
    }
    with pd.ExcelWriter(BACKUP / "tables.xlsx") as xlsx:
        for stem, (table, note) in tables.items():
            table.to_csv(BACKUP / f"{stem}.csv", index=False)
            table.to_excel(xlsx, sheet_name=stem[:31], index=False)
            pd.DataFrame({"note": [note]}).to_excel(xlsx, sheet_name=stem[:31], index=False,
                                                    startrow=len(table) + 2, header=False)
            for name in STYLES:
                plot_table(table, note, name, BACKUP / name, stem)
            to_latex(table, note, (BACKUP / "beamer" / f"{stem}.tex"))
    for name in STYLES:
        plot_coefficients(results, name, BACKUP / name)


def main():
    MAIN.mkdir(parents=True, exist_ok=True)
    BACKUP.mkdir(parents=True, exist_ok=True)

    results, interactions, raw = collect_results()
    results.to_csv(BACKUP / "all_results.csv", index=False)
    interactions.to_csv(BACKUP / "factory_share_controls.csv", index=False)

    numbers, plain, why = slide_numbers(results)
    trend = factory_trend(raw)
    numbers.to_csv(BACKUP / "key_numbers.csv", index=False)
    plain.to_csv(BACKUP / "effects_plain_terms.csv", index=False)
    why.to_csv(BACKUP / "why_factory_heavy_regions.csv", index=False)
    trend.to_csv(BACKUP / "why_factory_trend_by_decade.csv", index=False)

    scorecard = verdicts(results)
    scorecard.to_csv(BACKUP / "scorecard_verdicts.csv", index=False)
    (BACKUP / "scorecard_rule.txt").write_text(VERDICT_RULE + "\n")

    for name in STYLES:
        plot_scorecard(scorecard, name, MAIN / name)
        plot_hero(plain, name, MAIN / name)
        plot_why(trend, name, MAIN / name)

    test = period_difference_test()
    test.to_csv(BACKUP / "period_difference_test_raw.csv", index=False)
    backup_assets(results, test)

    return results, interactions, numbers, plain, why, scorecard, trend, test


if __name__ == "__main__":
    main()
