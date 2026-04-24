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
key concept in the paper: the metric, the model, the
explanations and the data itself.

> **For teaching &amp; exploration only.** The four live demos are
> deliberately simplified pedagogical tools: toy models,
> synthetic datasets and in-browser re-fits designed to build intuition
> for the concepts in the paper. They are **not** the production model
> from the article and should **not** be used for inference,
> decision-making or policy. The peer-reviewed methodology is
> documented in the paper
> (<https://doi.org/10.1007/s42001-022-00171-x>) and all data and code
> are open access at the authors&rsquo; OSF repository
> (<https://osf.io/agz5e/>).

## Interactive sections

- **Explore the Data**: loads the exact 7,855-case cohort from
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
- **Understanding ROC-AUC**: a dummy-model demo of two
  overlapping score distributions plus the ROC curve, driven by sliders
  for class separation, decision threshold and positive-class
  prevalence. Readers see first-hand which factors move AUC and which
  only move the operating point, plus how precision reacts to class
  prevalence.
- **Gradient Boosting in Action**: a full in-browser gradient
  boosting classifier trained on *days elapsed* &times; *age at
  missingness*. A **Training data** toggle switches between a 400-point
  stratified sample of the real paper cohort (default) and a pure
  synthetic demo, so readers can compare the decision surface the
  paper's data actually produces against a textbook example. Sliders
  control the number of boosting iterations, learning rate and tree
  depth; the decision surface and training log-loss curve update in
  real time. A dedicated **Reset to paper** button restores the paper
  defaults (30 trees, &eta;=0.30, depth 1, paper cohort).
- **Explaining Predictions with SHAP**: an exact-Shapley
  explainer over four user-tunable features (days elapsed, age,
  municipality size, sex). A **Model & background** toggle switches the
  scoring function between a toy analytical logistic model and a
  logistic model fitted on the paper's 7,855-case cohort (four main
  effects plus two interactions, IRLS-estimated); the background and
  beeswarm populations follow suit. A waterfall plot decomposes the
  live prediction into feature-level contributions, while a beeswarm
  summarizes SHAP values across 80 cases. A **Reset to paper** button
  restores the representative case under the paper model.

## Structure

```
missing_adults/
|-- index.html              # single-file website (HTML + inline CSS + JS)
|-- data/
|   |-- cohort.json         # compact cohort used by the interactive explorer
|   `-- paper_demo.json     # precomputed GBC + SHAP artifacts (paper cohort)
|-- data-raw/               # (not published) raw CSV + preprocessing script
|   |-- desaparecidos_colombia.csv
|   `-- preprocess.py
|-- README.md
`-- .gitignore
```

There are **no build steps and no runtime dependencies** for the
website: the whole page is self-contained in `index.html`, uses
Google Fonts (`Inter`) via CDN, ships with an inline SVG favicon and
fetches `data/cohort.json` plus a small (~10&nbsp;KB)
`data/paper_demo.json` on demand. All four teaching demos (AUC, GBC,
SHAP, data explorer) run entirely client-side in plain JavaScript.

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

### Regenerating `paper_demo.json`

The GBC and SHAP demos can optionally use a **paper cohort** data
source. The artifacts they consume (logistic-model coefficients,
stratified training sample, SHAP background and beeswarm populations)
are precomputed once and saved into `data/paper_demo.json`. To
reproduce the file deterministically from `cohort.json`:

```bash
python3 -m pip install --user numpy  # if not already installed
python3 data-raw/build_paper_demo.py \
  --in data/cohort.json \
  --out data/paper_demo.json
```

The IRLS fit uses a fixed seed so the output is byte-identical across
runs (~10 KB).

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
- Original open data: [Datos Abiertos Colombia &middot; SIRDEC](https://www.datos.gov.co/Justicia-y-Derecho/Desaparecidos-Colombia-hist-rico-a-os-1930-a-junio/8hqm-7fdt)

## License

The article is published under the Creative Commons Attribution 4.0
International License (CC BY 4.0). This website re-uses content of the
article under the same license.
