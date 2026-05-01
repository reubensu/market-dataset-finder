# Market Dataset Finder

A small Python portfolio project for discovering public e-commerce, product-review, and market-research datasets, ranking them transparently, exporting a useful shortlist, and analysing one selected review dataset for exploratory market insight.

The project is intentionally beginner-friendly: two runnable scripts, small helper modules, minimal dependencies, and generated outputs that can be recreated at any time.

## Features

- Searches Hugging Face datasets with several e-commerce, product-review, retail, and market-research keywords.
- Removes duplicate dataset results.
- Pulls useful metadata where available, including dataset id, downloads, likes, tags, licence, language, task categories, access status, description, and last modified date.
- Scores datasets using transparent component scores:
  - `relevance_score`
  - `popularity_score`
  - `metadata_quality_score`
  - `overall_score`
- Adds a practical decision label:
  - `strong candidate`
  - `review manually`
  - `secondary`
  - `check licence`
  - `check access`
  - `low priority`
- Exports `dataset_results.xlsx` and `dataset_results.csv`.
- Analyses a selected review dataset, defaulting to `SetFit/amazon_reviews_multi_en`.
- Shuffles before sampling to avoid taking a biased first slice.
- Detects text and label/rating columns.
- Compares negative and positive review language.
- Exports Excel summary tables, charts, sample rows, and a cautious insight report.

## Project Structure

```text
market-dataset-finder/
  main.py                  # dataset discovery entry point
  analyse_dataset.py       # review analysis entry point
  requirements.txt
  README.md
  .gitignore
  src/
    config.py
    dataset_search.py
    scoring.py
    excel_export.py
    review_analysis.py
    utils.py
```

## Install

Create a fresh virtual environment.

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the project was copied from another computer, delete the old `.venv` folder first and recreate it locally.

## Run Dataset Discovery

```bash
python main.py
```

Optional smaller or larger search:

```bash
python main.py --limit 20
```

Outputs:

- `dataset_results.xlsx`
- `dataset_results.csv`
- `run_log.txt`

The Excel file includes filters, frozen headers, readable column widths, wrapped text, decision labels, ranking, and score components.

## Run Review Analysis

```bash
python analyse_dataset.py
```

Optional custom dataset and sample size:

```bash
python analyse_dataset.py --dataset SetFit/amazon_reviews_multi_en --sample-size 5000
```

Outputs in `analysis_outputs/`:

- `analysis_summary.xlsx`
- `sample_rows.csv`
- `sentiment_distribution.png`
- `negative_phrases.png`
- `positive_phrases.png`
- `insight_summary.md`
- `run_log.txt`

## What The Project Demonstrates

- Public dataset discovery
- Metadata cleaning and deduplication
- Transparent scoring logic
- Excel export and formatting with `openpyxl`
- Hugging Face dataset loading
- Basic exploratory text analysis
- Positive vs negative review comparison
- Clear, reproducible command-line workflows

## Limitations

- Hugging Face metadata is inconsistent, so licence, language, task, and description fields may be missing.
- Search results still require manual review before choosing a dataset for serious analysis.
- Popularity is log-scaled and treated as one weak signal, not proof that a dataset is useful.
- The default Amazon review dataset may not represent Shopee, TikTok Shop, Malaysia, or any specific local market.
- Phrase counts are exploratory and do not understand sarcasm, product category, authenticity, or review context.
- No paid APIs, credentials, scraping, dashboards, or large language models are used by default.

## Possible Next Improvements

- Add a small test suite for scoring and column detection.
- Add optional CSV input support for analysing a local review dataset.
- Add manual category tagging after reviewing the shortlist.
- Add simple product-category comparisons when a dataset includes category fields.
