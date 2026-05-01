# market dataset finder

a python portfolio project for discovering, ranking, and analysing public e-commerce and product-review datasets.

## what it does

- searches hugging face for e-commerce, product-review, customer behaviour, and market-research datasets
- removes duplicate dataset results
- scores datasets using relevance, downloads, likes, metadata quality, licence/access checks, and keyword matching
- classifies datasets by likely use case
- exports a formatted excel shortlist
- analyses one selected amazon review dataset
- compares positive and negative review language
- exports summary tables and charts

## project files

- `main.py` - searches and ranks datasets
- `analyse_dataset.py` - analyses a selected product-review dataset
- `requirements.txt` - python dependencies
- `.gitignore` - excludes generated outputs and local environment files

## outputs

the project can generate:

- `dataset_results.csv`
- `dataset_results.xlsx`
- `analysis_outputs/analysis_summary.xlsx`
- `analysis_outputs/negative_phrases.png`
- `analysis_outputs/positive_phrases.png`
- `analysis_outputs/sentiment_distribution.png`

generated outputs are not committed to git because they can be recreated by running the scripts.

## how to run

create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1