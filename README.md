# — The China shock, composition-adjusted

Replicates Autor, Dorn & Hanson (2013), "The China Syndrome: Local Labor Market Effects of Import Competition in the United States" (*AER* 103(6)): Table 3, Table 5 (Panel A, columns 1–4, plus Panel B) and Table 6. It then runs Professor Vogel's robustness checks and re-estimates everything with **composition-adjusted** outcomes, which hold each commuting zone's demographic mix fixed over time.

## Layout

```
Project 1/
├── Notebook1_ADH_replication_robustness.ipynb    replication(not composition-adjusted) + robustness checks (ADH's own outcomes)
├── Notebook2_composition_adjusted_outcomes.ipynb builds composition-adjusted outcomes from the original IPUMS data, re-runs everything
├── data/
│   ├── workfile_china.dta        ADH replication data: 722 commuting zones x 2 periods
│   ├── cell_sums.csv             IPUMS aggregates by period x commuting zone x demographic cell (built by Notebook 2)
│   ├── crosswalks/               Dorn's PUMA -> commuting zone crosswalks (1990 and 2000 PUMAs) + their READMEs
│   └── ipums_extract.csv.gz      NOT in this repository
├── output/
│   ├── replication/              tables from Notebook 1 (.csv and .tex)
│   └── composition_adjusted/     tables from Notebook 2 (.csv and .tex) + the merged analysis file
├── provided_code/                Professor Vogel's ADH_Assignment1.do and its Python translation
└── original paper calculations/  screenshots of ADH Tables 3, 5 and 6 for comparison
```

* **Notebook 1** needs only `data/workfile_china.dta`. It checks every replicated cell against the published value and stops with an error if any differ.
* **Notebook 2** runs from the committed `data/cell_sums.csv`, so **you do not need the IPUMS extract** to reproduce the results. The extract is only needed to rebuild `cell_sums.csv` from scratch: delete that file and put the extract at `data/ipums_extract.csv.gz`. If neither file is present, the notebook runs in a clearly labelled synthetic-data test mode whose numbers are meaningless.

## Data

| File | Source | In repo? |
|---|---|---|
| `workfile_china.dta` | ADH replication package, [ddorn.net/data.htm](https://www.ddorn.net/data.htm) (P3) | yes |
| `crosswalks/cw_puma1990_czone.dta`, `cw_puma2000_czone.dta` | Dorn, files E4 and E5 on the same page | yes |
| `cell_sums.csv` | built by Notebook 2 from the IPUMS extract | yes (aggregates only) |
| `ipums_extract.csv.gz` | [IPUMS USA](https://usa.ipums.org/usa/) | **no**: about 360 MB, and IPUMS terms don't allow redistributing microdata |

## Method: For composition adjustment (weights fixed over time)

1. Split each commuting zone's working-age population (16–64) into 40 cells: sex × 5 age groups × 4 education levels.
2. Compute each outcome inside each cell and period: employment-status shares of the population, unemployment rate, labor-force participation, and mean log real weekly wage of wage-and-salary earners.
3. Aggregate the cells with **weights fixed over time**: the cell's share averaged over 1990, 2000 and 2007. Population shares are used for employment outcomes and wage-earner shares for wages; the population-weighted wage version is reported too.
4. Only cells observed in all three years enter, and the weights are normalised once, so every year uses the identical weight vector. This drops under 1% of any commuting zone's population; Notebook 2, section 4a, checks it.
5. Take ten-year-equivalent changes (2000–2007 scaled by 10/7), merge onto ADH's regressors, and run the same 2SLS: imports to the US instrumented by imports to other rich countries, weighted by population share, standard errors clustered by state, column-6 controls.

The "unadjusted rebuild" uses each year's actual shares, which gives the ordinary commuting-zone average. It is built the same way from the same microdata, so comparing it with the adjusted version isolates the effect of the adjustment. It closely tracks ADH's own variables: for example, the manufacturing-share outcome correlates 0.998 with theirs.
