# Predicting the probability of finding missing older adults based on machine learning

Project website for the open-access article:

> Ruiz-Rizzo, A. L., Archila-Mel&eacute;ndez, M. E., & Gonz&aacute;lez Veloza, J. J. F. (2022).
> **Predicting the probability of finding missing older adults based on machine learning.**
> *Journal of Computational Social Science*, 5(2), 1303&ndash;1321.
> <https://doi.org/10.1007/s42001-022-00171-x>

The site summarizes the paper's motivation, data pipeline, feature
importance and results in a single, responsive HTML page inspired by
the layout of project pages such as
[vision-banana.github.io](https://vision-banana.github.io/). Alongside
the narrative, it ships **four live teaching demos** and an
interactive data explorer so readers can build up intuition for every
key concept in the paper &mdash; the metric, the model, the
explanations and the data itself.

## Interactive sections

- **Explore the Data** &mdash; loads the exact 7,855-case cohort from
  the paper and lets readers slice the *found-alive* rate by age, sex,
  municipality size, vulnerability factor and education. Every filter
  change live-updates KPIs, an outcome stack bar, a **subgroup parity
  (identity) plot**, two color-coded stacked histograms and per-subgroup
  breakdowns. The parity plot encodes each subgroup on seven visual
  channels at once: *x* = full-cohort rate, *y* = current-selection
  rate, bubble color = feature family, bubble area = selected-case
  count, vertical whisker = 95% Wilson confidence interval, a thin
  guide line tying each bubble to its baseline position on the diagonal,
  and a hollow marker at that baseline.
- **Understanding ROC-AUC** &mdash; a dummy-model demo of two
  overlapping score distributions plus the ROC curve, driven by sliders
  for class separation, decision threshold and positive-class
  prevalence. Readers see first-hand which factors move AUC and which
  only move the operating point, plus how precision reacts to class
  prevalence.
- **Gradient Boosting in Action** &mdash; a full in-browser gradient
  boosting classifier trained on a synthetic *days elapsed* &times;
  *age at missingness* dataset. Sliders control the number of boosting
  iterations, learning rate and tree depth; the decision surface and
  training log-loss curve update in real time so readers can watch the
  ensemble sharpen and the loss drop.
- **Explaining Predictions with SHAP** &mdash; an exact-Shapley
  explainer over four user-tunable features (days elapsed, age,
  municipality size, sex). A waterfall plot decomposes the live
  prediction into feature-level contributions, while a beeswarm
  summarizes SHAP values across 80 synthetic cases &mdash; the same
  intuition the paper uses to rank its predictors in Fig.&nbsp;3.

## Structure

```
missing_adults/
|-- index.html              # single-file website (HTML + inline CSS + JS)
|-- data/
|   `-- cohort.json         # compact cohort used by the interactive explorer
|-- data-raw/               # (not published) raw CSV + preprocessing script
|   |-- desaparecidos_colombia.csv
|   `-- preprocess.py
|-- README.md
`-- .gitignore
```

There are **no build steps and no runtime dependencies** for the
website &mdash; the whole page is self-contained in `index.html`, uses
Google Fonts (`Inter`) via CDN, ships with an inline SVG favicon and
fetches `data/cohort.json` on demand. All four teaching demos (AUC,
GBC, SHAP, data explorer) run entirely client-side in plain JavaScript.

## Regenerating the cohort data

The interactive explorer reads `data/cohort.json`, a compact JSON
payload derived from the public SIRDEC dump hosted on the paper's
[OSF project](https://osf.io/agz5e/). To reproduce it:

```bash
mkdir -p data-raw
curl -L -o data-raw/desaparecidos_colombia.csv \
  https://osf.io/download/5t4vz/
python3 data-raw/preprocess.py \
  --in data-raw/desaparecidos_colombia.csv \
  --out data/cohort.json
```

The script applies the same filters as the paper (age &ge; 60, cases
reported in Colombia, excluding "found dead" and "presumed forced
disappearance"), buckets municipalities by population and collapses
the long tail of vulnerability factors into a handful of analytical
groups. The resulting file is ~510 KB (pure ASCII, no personal
identifiers).

## Local preview

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

The explorer requires an HTTP server (it uses `fetch()` for the JSON);
opening `index.html` directly via `file://` will load everything
*except* the explorer data.

## Deploy with GitHub Pages

1. Push this repository to GitHub (the remote is already configured to
   `git@github.com:virtualmarioe/missing_adults.git`).
2. In the repository settings, go to **Pages** and set the source to
   the `main` branch, `/ (root)` folder.
3. The site will be published at
   `https://virtualmarioe.github.io/missing_adults/`.

## Sources

- Paper: <https://link.springer.com/article/10.1007/s42001-022-00171-x>
- Data & code (OSF): <https://osf.io/agz5e/>
- Original open data: [Datos Abiertos Colombia &mdash; SIRDEC](https://www.datos.gov.co/Justicia-y-Derecho/Desaparecidos-Colombia-hist-rico-a-os-1930-a-junio/8hqm-7fdt)

## License

The article is published under the Creative Commons Attribution 4.0
International License (CC BY 4.0). This website re-uses content of the
article under the same license.
