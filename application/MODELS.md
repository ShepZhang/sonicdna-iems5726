# Pre-trained Model Artifacts

> Per IEMS5726 instructions ("Do not include your trained model(s) in
> the submission. Submit the link instead.") the binary model files
> are NOT bundled inside `Group43_source.zip`. They can be obtained
> in two equivalent ways:

## Option 1 — Regenerate from the Kaggle dataset (recommended)

The `source_code/pipeline/` package is fully reproducible. From the
project root:

```bash
# 1. Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r source_code/requirements.txt -r application/requirements.txt

# 2. Pull the Kaggle dataset (~110 MB) once
python -c "import kagglehub; print(kagglehub.dataset_download('maharshipandya/-spotify-tracks-dataset'))"
# Copy the printed dataset.csv into source_code/data/raw/

# 3. Train all artifacts (deterministic, ~2 minutes on a recent laptop)
cd source_code
python -m pipeline.preprocess     # 89,740 unique tracks → parquet + scaler.pkl
python -m pipeline.cluster        # KMeans k=8 → kmeans_mood.pkl + pca.pkl
python -m pipeline.build_samples  # three sample CSVs for the app
```

After step 3 the following files appear under `source_code/models/`:

| File | Purpose | Approx. size |
|---|---|---|
| `scaler.pkl` | StandardScaler over 9 audio features | < 1 KB |
| `kmeans_mood.pkl` | KMeans (k=8) over the z-scored space | ~ 5 KB |
| `pca.pkl` | 2-D PCA used by the Insights scatter map | ~ 1 KB |
| `mood_cluster_names.json` | Interpretive name for each cluster id | < 1 KB |
| `meta_genre_counts.json` | Track-count per meta-genre lookup | < 1 KB |
| `figures/*.png` | EDA / centroid / architecture figures | total ~ 1.5 MB |

All training uses fixed random seeds (`random_state=42`,
`n_init=10`), so two independent runs produce byte-identical
artifacts.

## Option 2 — Public source repository on GitHub

The full project (excluding the Kaggle dataset and the trained
artifacts above) is mirrored at:

> **https://github.com/ShepZhang/sonicdna-iems5726**

The repository's `README.md` contains the same Quick-Start
instructions. Cloning it and running the commands above gives the
same result as unzipping `Group43_source.zip` and running the
commands.

## (Optional) Direct download of the trained artifacts

If you would prefer to skip Option 1 and download the pre-trained
artifacts directly, contact the group via the email addresses on the
report's title page. We can then provide a public Google Drive
folder containing the files listed in the table above.

---

This document is provided to satisfy the "link to the trained
model(s)" requirement under IEMS5726 Project Instructions, p. 6.
