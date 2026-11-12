# GW5 En-ROADS: code and data

Data and code behind Figures 2–6, Table 3 and the numbers in Section 4 of
*What If the World Put Nuclear Power First? A Counterfactual Analysis with the
En-ROADS Climate Simulator*.


## Contents

| Path | What it is |
| --- | --- |
| `extract_enroads.js` | Browser routine that exports the data behind the En-ROADS graphs of one simulation to a CSV file |
| `data/enroads_<run>.csv` | Exported data, one file per simulation (En-ROADS v26.11, annual values 2000–2100) |
| `make_figures.py` | Produces the figures, Table 3 and all numbers quoted in Section 4 |
| `figures/` | Output figures (PDF for LaTeX, PNG for preview) |
| `results/table3.csv` | Table 3 with three decimals |
| `results/key_numbers.txt` | Every number quoted in Section 4, grouped by subsection |

## Simulations

| File suffix | Simulation |
| --- | --- |
| `main` | Main scenario |
| `counterfactual` | Nuclear subsidy at status quo (30 %), no breakthrough |
| `no_breakthrough` | 60 % nuclear subsidy, no breakthrough |
| `nuclear_only` | Nuclear policy only, applied to the baseline |
| `ecs_2.5`, `ecs_4.0` | Main scenario with climate sensitivity 2.5 / 4.0 °C |
| `counterfactual_ecs_2.5`, `counterfactual_ecs_4.0` | Counterfactual with climate sensitivity 2.5 / 4.0 °C (nuclear contribution at other climate sensitivities) |
| `pr_0.90`, `pr_1.00` | Main scenario with nuclear progress ratio 0.90 / 1.00 |
| `baseline` | En-ROADS default settings (needed for the baseline energy mix) |

The first line of each CSV holds the En-ROADS link the data were exported
from, so every file can be traced to its settings. The links are also listed in
Appendix A of the report.

## Reproducing

1. **Export the data** (optional – the exported files are included).
   Open a link from Appendix A, close the welcome dialog, open the browser
   console (F12 → Console), type `window.RUN_NAME = "main"` (or another suffix),
   press Enter, then paste the content of `extract_enroads.js` and press Enter.
   Move the downloaded `enroads_<run>.csv` into `data/`.
2. **Make the figures and numbers:**

   ```bash
   pip install numpy pandas matplotlib
   python make_figures.py
   ```

   The script writes the figures to `figures/`, and Table 3 and the key numbers
   to `results/`, and prints both.

## Notes

- Each CSV holds 12 graphs: the 11 used for the figures and *Reduction in GDP
  from Climate Impacts* (% of GDP), quoted in Section 4.4.

- En-ROADS identifies series by line colour; the script relies on the colours
  used in v26.x (black = baseline, blue = current scenario). A future En-ROADS
  version may change them.
- The cumulative nuclear subsidy cost is the sum over 2028–2100 of the
  difference in net government revenue between the counterfactual and the main
  scenario.
- Average GDP per capita growth is the compound annual rate over 2020–2100.
