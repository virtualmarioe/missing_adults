# Predicting the probability of finding missing older adults based on machine learning

Project website for the open-access article:

> Ruiz-Rizzo, A. L., Archila-MelÈndez, M. E., & Gonz·lez Veloza, J. J. F. (2022).
> **Predicting the probability of finding missing older adults based on machine learning.**
> *Journal of Computational Social Science*, 5(2), 1303ñ1321.
> <https://doi.org/10.1007/s42001-022-00171-x>

The site summarizes the paper's motivation, data pipeline, feature
importance and results in a single, responsive HTML page inspired by
the layout of project pages such as
[vision-banana.github.io](https://vision-banana.github.io/).

## Structure

```
missing_adults/
??? index.html     # single-file website (HTML + inline CSS + JS)
??? README.md
```

There are **no build steps and no dependencies** &mdash; the whole
site is self-contained in `index.html`, uses Google Fonts (`Inter`) via
CDN and ships with an inline SVG favicon.

## Local preview

```bash
# from the repo root
python3 -m http.server 8000
# then open http://localhost:8000
```

Or just double-click `index.html`.

## Deploy with GitHub Pages

1. Push this repository to GitHub (the remote is already configured to
   `git@github.com:virtualmarioe/missing_adults.git`).
2. In the repository settings, go to **Pages** and set the source to the
   `main` branch, `/ (root)` folder.
3. The site will be published at
   `https://virtualmarioe.github.io/missing_adults/`.

## Sources

- Paper: <https://link.springer.com/article/10.1007/s42001-022-00171-x>
- Data & code (OSF): <https://osf.io/agz5e/>
- Original open data: [Datos Abiertos Colombia ñ SIRDEC](https://www.datos.gov.co/Justicia-y-Derecho/Desaparecidos-Colombia-hist-rico-a-os-1930-a-junio/8hqm-7fdt)

## License

The article is published under the Creative Commons Attribution 4.0
International License (CC BY 4.0). This website re-uses content of the
article under the same license.
