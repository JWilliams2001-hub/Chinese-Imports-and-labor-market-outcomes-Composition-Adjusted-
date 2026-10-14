"""Python equivalent of ADH_Assignment1.do (20 weighted 2SLS regressions).

Install once: python -m pip install pandas linearmodels
Run: python ADH_Assignment1.py
Or:  python ADH_Assignment1.py /path/to/workfile_china.dta

Uses only workfile_china.dta. Prints the full regression results, in the
same order as the Stata do-file. Requires no Stata installation.
"""

import sys
from pathlib import Path

import pandas as pd
from linearmodels.iv import IV2SLS


DATA = Path("/Users/jvogel/Dropbox/Teaching/UCLA MA/Lectures/Assignments/Assignment 1/ADH_replication/dta/workfile_china.dta")
OUTCOMES = [
    "d_sh_empl_mfg", "d_sh_empl_nmfg", "d_sh_unempl", "d_sh_nilf",
    "d_avg_lnwkwage",
]
CONTROLS = [
    "l_shind_manuf_cbp", "l_sh_popedu_c", "l_sh_popfborn", "l_sh_empl_f",
    "l_sh_routine33", "l_task_outsource",
]


def run(data_path=DATA, display=True):
    df = pd.read_stata(data_path, convert_categoricals=False)
    # Stata reg* expands in dataset order.
    regions = [column for column in df.columns if column.startswith("reg")]
    controls = CONTROLS + regions
    df["_cons"] = 1.0

    # Stata abbreviates czone as cz.
    # Exact counterpart of: bys cz: egen mshare90=max(l_shind_manuf_cbp*(yr==1990))
    df["mshare90"] = (df["l_shind_manuf_cbp"] * (df["yr"] == 1990)).groupby(df["czone"], dropna=False).transform("max")
    # egen creates a float by default in Stata; preserve that rounding.
    df["mshare90"] = df["mshare90"].astype("float32").astype("float64")
    # i.yr#c.mshare90 includes BOTH year-specific slopes.
    interactions = []
    for year in sorted(df["yr"].dropna().unique()):
        name = f"{int(year)}.yr#c.mshare90"
        df[name] = df["mshare90"] * (df["yr"] == year)
        interactions.append(name)

    results = []

    def estimate(outcome, sample, exog, label):
        columns = [outcome, "d_tradeusch_pw", "d_tradeotch_pw_lag", "timepwt48", "statefip"] + exog + ["_cons"]
        data = sample[columns].dropna()
        data = data.loc[data["timepwt48"] > 0]
        result = IV2SLS(
            dependent=data[outcome],
            exog=data[exog + ["_cons"]],
            endog=data[["d_tradeusch_pw"]],
            instruments=data[["d_tradeotch_pw_lag"]],
            weights=data["timepwt48"],
        ).fit(cov_type="clustered", clusters=data["statefip"], debiased=False)
        # debiased=False matches ivregress without the small option:
        # unadjusted cluster covariance, normal z tests, and Wald chi-square.
        results.append((label, outcome, result))
        if display:
            print(f"\n{label}: {outcome}\n{result.summary}")

    # Do not stack periods I and II: Table 5 Panel B and Table 6 all-worker wages.
    for year, label in [(1990, "1990–2000"), (2000, "2000–2007")]:
        for outcome in OUTCOMES:
            estimate(outcome, df.loc[df["yr"] == year], controls, label)

    # Stack periods: baseline, then time-varying effect of 1990 manufacturing share.
    for outcome in OUTCOMES:
        estimate(outcome, df, controls + ["t2"], "Stacked baseline")
        # Match the order of controls used in the original do-file.
        varying_controls = (CONTROLS + regions if outcome == "d_avg_lnwkwage"
                            else CONTROLS[:1] + regions + CONTROLS[1:])
        estimate(outcome, df, interactions + varying_controls + ["t2"],
                 "Stacked with year-specific 1990 manufacturing-share slopes")
    return results


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else DATA)
