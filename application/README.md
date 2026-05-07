# SonicDNA · application/

The Streamlit deployment of SonicDNA. The pipeline package lives in
`../source_code/pipeline/` and is imported via `sys.path` injection at
the top of [`app.py`](app.py) so the same code drives notebooks, the
Streamlit UI, and any future Vue + FastAPI rewrite.

## Local development

```bash
# from the project root
python3 -m venv .venv && source .venv/bin/activate
pip install -r source_code/requirements.txt -r application/requirements.txt

# build models + sample CSVs (one-time, ~30s)
cd source_code
python -m pipeline.preprocess
python -m pipeline.cluster
python -m pipeline.build_samples

# run the app
cd ../application
streamlit run app.py
# -> http://localhost:8501
```

## Run with Docker

```bash
# from the project root (NOT application/)
docker build -f application/Dockerfile -t sonicdna .
docker run -p 8501:8501 sonicdna
# -> http://localhost:8501
```

The Docker image self-contains the Kaggle dataset (downloaded at build
time) and all trained models, so cold-start is < 5 seconds and there
is no network call at request time.

## Deploy to HuggingFace Spaces (Streamlit SDK)

The simplest public-demo path is HuggingFace Spaces with the
**Streamlit** runtime:

```bash
# one-time setup
huggingface-cli login                           # paste your write token

# create a new Space backed by Streamlit
huggingface-cli repo create sonicdna --type space --space_sdk streamlit

# push (the Space's README.md frontmatter must declare app_file)
git remote add hf https://huggingface.co/spaces/<your-username>/sonicdna
git push hf main
```

For Spaces to find the entry point, add this YAML frontmatter to the
**top of the project root README.md** before pushing:

```yaml
---
title: SonicDNA
emoji: 🎧
colorFrom: pink
colorTo: indigo
sdk: streamlit
sdk_version: "1.40.2"
app_file: application/app.py
pinned: false
---
```

> Spaces Streamlit runtime does not run scripts at build time, so you
> need to commit the trained models too. Run `python -m pipeline.preprocess`,
> `python -m pipeline.cluster`, and `python -m pipeline.build_samples`
> locally first, then `git add source_code/models/*.pkl
> source_code/data/processed/*.parquet application/samples/*.csv` and
> commit. Files are < 15 MB total, well below the Space limit.

## Files

- `app.py` — Streamlit entry. Sidebar selects sample/upload, 4 tabs.
- `components/` — reserved for future custom components.
- `samples/` — three demo playlists in CSV form.
- `Dockerfile` — production-ready image, build context = project root.
- `docker-compose.yml` — convenience wrapper.
