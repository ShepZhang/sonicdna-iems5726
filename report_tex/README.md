# Group43 Report — LaTeX / Overleaf source

This folder is a self-contained Overleaf project. Everything the
report needs (text + images) lives inside; `pdflatex` produces the
final PDF.

## Folder layout

```
report_tex/
├── Group43_report.tex         ← main file (compile this)
├── README.md                  ← you are here
├── figures/                   ← analysis figures (8 PNGs)
│   ├── 01_feature_distributions.png
│   ├── 02_correlation_heatmap.png
│   ├── 03_metagenre_distribution.png
│   ├── 04_pca_global_map.png
│   ├── 05_centroid_radars.png
│   ├── 06_arch_mvp.png
│   ├── 07_arch_production.png
│   └── moodprint_smoke_chill.png
└── screenshots/               ← live-app UI screenshots
    ├── 01_dashboard.png
    ├── 02_universes.png
    ├── 03_insights.png
    └── 06_sidebar.png
```

## Compile on Overleaf (recommended)

1. Visit https://www.overleaf.com → **New Project → Upload Project**.
2. Select the entire `report_tex/` folder (or a zip of it).
   Overleaf will preserve the `figures/` and `screenshots/`
   sub-directories automatically.
3. Set the main document to `Group43_report.tex` (it usually
   auto-detects).
4. Compiler: **pdfLaTeX** (default).
5. Click **Recompile** → download `Group43_report.pdf`.

## Compile locally (optional)

If you have a TeX distribution installed (TeX Live / MacTeX / MiKTeX):

```bash
cd report_tex
pdflatex Group43_report.tex
pdflatex Group43_report.tex   # second pass for the ToC + cross-refs
```

Or with `latexmk` (handles the multi-pass automatically):

```bash
cd report_tex
latexmk -pdf Group43_report.tex
```

## Things to fill in before submission

The .tex source still contains three placeholder URLs you need to
replace (search for `<your-username>` and `<YOUR_FOLDER_ID>`):

| Search for                           | Replace with                                |
|--------------------------------------|---------------------------------------------|
| `<YOUR_FOLDER_ID>` (in §3.5)         | Google Drive folder ID for `models/*.pkl`   |
| `<your-username>` in HuggingFace URL | Your HF Spaces handle                       |
| `<your-username>` in GitHub URL      | Your GitHub username                        |

Also, after you submit the report to VeriGuide and save the receipt
PNG, drop it in this folder as `veriguide.png` and replace the
red placeholder block at the bottom of `Group43_report.tex` with:

```latex
\begin{center}
  \includegraphics[width=\linewidth]{veriguide.png}
\end{center}
```

## Why LaTeX (not Word)?

* The vinyl MoodPrint and the four UI screenshots are large PNGs;
  Word frequently re-flows them across page breaks. LaTeX's `[H]`
  float placement (via the `float` package) keeps every figure
  exactly where you put it.
* Math symbols like $\alpha$, $\sigma$, $|r| < 0.5$ render with
  proper kerning instead of inline-text approximations.
* Section headings are colored uniformly (`sdNavy`), captions are
  italic 9 pt grey, links are colored — all defined once in the
  preamble, instead of touched-up paragraph by paragraph.
