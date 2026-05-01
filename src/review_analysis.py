from collections import Counter
import os
from pathlib import Path
import re

from datasets import load_dataset

os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib_cache").resolve()))

import matplotlib.pyplot as plt
import pandas as pd

from src.config import CUSTOM_STOPWORDS
from src.excel_export import save_multi_sheet_workbook
from src.utils import now_string, write_run_log


TEXT_COLUMN_CANDIDATES = [
    "text", "review", "review_text", "review_body", "content", "sentence",
    "comment", "body", "summary",
]

LABEL_COLUMN_CANDIDATES = [
    "label", "rating", "stars", "overall", "score", "sentiment",
    "star_rating", "review_rating",
]


def run_review_analysis(
    dataset_id: str,
    split: str,
    sample_size: int,
    output_dir: Path,
    seed: int = 42,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"loading dataset: {dataset_id} ({split})")
    try:
        dataset = load_dataset(dataset_id, split=split)
    except Exception as exc:
        raise RuntimeError(
            f"Could not load dataset '{dataset_id}'. Check the dataset name, split, and internet connection."
        ) from exc

    available_rows = len(dataset)
    rows_to_sample = min(sample_size, available_rows)
    print(f"shuffling before sampling {rows_to_sample:,} of {available_rows:,} rows")
    dataset = dataset.shuffle(seed=seed).select(range(rows_to_sample))

    df = pd.DataFrame(dataset)
    text_column = find_text_column(df)
    if text_column is None:
        raise RuntimeError("No suitable text column was found in the selected dataset.")

    label_column = find_label_column(df, text_column)
    if label_column is None:
        raise RuntimeError("No suitable label/rating column was found in the selected dataset.")

    df = add_sentiment_group(df, label_column)

    sentiment_counts = (
        df["sentiment_group"]
        .value_counts()
        .rename_axis("sentiment_group")
        .reset_index(name="count")
    )

    negative_reviews = df.loc[df["sentiment_group"] == "negative", text_column]
    positive_reviews = df.loc[df["sentiment_group"] == "positive", text_column]

    negative_words = top_terms(negative_reviews, ngram_size=1, top_n=30)
    positive_words = top_terms(positive_reviews, ngram_size=1, top_n=30)
    negative_phrases = top_terms(negative_reviews, ngram_size=2, top_n=30)
    positive_phrases = top_terms(positive_reviews, ngram_size=2, top_n=30)

    overview = pd.DataFrame([{
        "dataset_id": dataset_id,
        "split": split,
        "rows_available": available_rows,
        "rows_sampled": len(df),
        "columns_loaded": len(df.columns),
        "text_column": text_column,
        "label_column": label_column,
        "run_time": now_string(),
    }])

    column_summary = make_column_summary(df)
    sample_rows = df.head(100)

    workbook_path = output_dir / "analysis_summary.xlsx"
    save_multi_sheet_workbook(
        {
            "overview": overview,
            "column_summary": column_summary,
            "sentiment_counts": sentiment_counts,
            "negative_words": negative_words,
            "positive_words": positive_words,
            "negative_phrases": negative_phrases,
            "positive_phrases": positive_phrases,
            "sample_rows": sample_rows,
        },
        workbook_path,
    )

    sample_rows.to_csv(output_dir / "sample_rows.csv", index=False)

    save_bar_chart(
        sentiment_counts.sort_values("count"),
        x_column="count",
        y_column="sentiment_group",
        title="Review sentiment distribution",
        filename=output_dir / "sentiment_distribution.png",
    )
    save_bar_chart(
        negative_phrases.sort_values("count").tail(15),
        x_column="count",
        y_column="term",
        title="Top negative two-word phrases",
        filename=output_dir / "negative_phrases.png",
    )
    save_bar_chart(
        positive_phrases.sort_values("count").tail(15),
        x_column="count",
        y_column="term",
        title="Top positive two-word phrases",
        filename=output_dir / "positive_phrases.png",
    )

    insight_path = output_dir / "insight_summary.md"
    insight_path.write_text(
        build_insight_summary(
            dataset_id=dataset_id,
            split=split,
            rows_sampled=len(df),
            sentiment_counts=sentiment_counts,
            negative_phrases=negative_phrases,
            positive_phrases=positive_phrases,
        ),
        encoding="utf-8",
    )

    write_run_log(
        output_dir / "run_log.txt",
        [
            f"Run time: {now_string()}",
            f"Dataset: {dataset_id}",
            f"Split: {split}",
            f"Rows sampled: {len(df)}",
            "Generated: analysis_summary.xlsx",
            "Generated: sample_rows.csv",
            "Generated: sentiment_distribution.png",
            "Generated: negative_phrases.png",
            "Generated: positive_phrases.png",
            "Generated: insight_summary.md",
        ],
    )

    return {
        "rows_sampled": len(df),
        "text_column": text_column,
        "label_column": label_column,
        "output_dir": output_dir,
    }


def find_text_column(df: pd.DataFrame) -> str | None:
    for column in TEXT_COLUMN_CANDIDATES:
        if column in df.columns:
            return column

    text_columns = list(df.select_dtypes(include=["object", "string"]).columns)
    if not text_columns:
        return None

    return max(text_columns, key=lambda col: df[col].astype(str).str.len().mean())


def find_label_column(df: pd.DataFrame, text_column: str) -> str | None:
    for column in LABEL_COLUMN_CANDIDATES:
        if column in df.columns and column != text_column:
            return column

    for column in df.columns:
        if column == text_column:
            continue
        numeric_values = pd.to_numeric(df[column], errors="coerce")
        if numeric_values.notna().mean() > 0.8 and numeric_values.nunique() <= 20:
            return column

    return None


def add_sentiment_group(df: pd.DataFrame, label_column: str) -> pd.DataFrame:
    df = df.copy()
    labels = pd.to_numeric(df[label_column], errors="coerce")

    if labels.notna().any():
        min_label = labels.min()
        max_label = labels.max()

        df["sentiment_group"] = "neutral"
        if min_label == max_label:
            return df

        low_cutoff = min_label + ((max_label - min_label) / 3)
        high_cutoff = min_label + ((max_label - min_label) * 2 / 3)
        df.loc[labels <= low_cutoff, "sentiment_group"] = "negative"
        df.loc[labels >= high_cutoff, "sentiment_group"] = "positive"
        return df

    label_text = df[label_column].astype(str).str.lower()
    df["sentiment_group"] = "neutral"
    df.loc[label_text.str.contains("negative|bad|poor|terrible|1|2", na=False), "sentiment_group"] = "negative"
    df.loc[label_text.str.contains("positive|good|great|excellent|4|5", na=False), "sentiment_group"] = "positive"
    return df


def clean_words(text: str) -> list[str]:
    words = re.findall(r"[a-z][a-z']{2,}", str(text).lower())
    return [word for word in words if word not in CUSTOM_STOPWORDS]


def make_ngrams(words: list[str], n: int) -> list[str]:
    return [" ".join(words[index:index + n]) for index in range(len(words) - n + 1)]


def top_terms(texts: pd.Series, ngram_size: int, top_n: int) -> pd.DataFrame:
    counter = Counter()

    for text in texts.dropna():
        words = clean_words(text)
        terms = words if ngram_size == 1 else make_ngrams(words, ngram_size)
        counter.update(terms)

    return pd.DataFrame(counter.most_common(top_n), columns=["term", "count"])


def make_column_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[column].dtype) for column in df.columns],
        "non_null": [int(df[column].notna().sum()) for column in df.columns],
        "missing": [int(df[column].isna().sum()) for column in df.columns],
        "missing_pct": [round(float(df[column].isna().mean() * 100), 2) for column in df.columns],
        "unique_values": [int(df[column].nunique(dropna=True)) for column in df.columns],
    })


def save_bar_chart(data: pd.DataFrame, x_column: str, y_column: str, title: str, filename: Path) -> None:
    if data.empty:
        return

    plt.figure(figsize=(10, 6))
    plt.barh(data[y_column].astype(str), data[x_column])
    plt.title(title)
    plt.xlabel(x_column.replace("_", " "))
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def build_insight_summary(
    dataset_id: str,
    split: str,
    rows_sampled: int,
    sentiment_counts: pd.DataFrame,
    negative_phrases: pd.DataFrame,
    positive_phrases: pd.DataFrame,
) -> str:
    negative_top = negative_phrases.head(8)
    positive_top = positive_phrases.head(8)

    return f"""# Insight Summary

## Dataset

- Dataset: `{dataset_id}`
- Split: `{split}`
- Rows sampled: {rows_sampled:,}
- Run time: {now_string()}

## Sentiment Distribution

{sentiment_counts.to_markdown(index=False)}

## Common Negative Complaint Phrases

{negative_top.to_markdown(index=False)}

## Common Positive Praise Phrases

{positive_top.to_markdown(index=False)}

## Cautious Commercial Insights

1. Negative phrase patterns can help identify possible product quality, expectation, delivery, or usability themes worth checking manually.
2. Positive phrase patterns can reveal language customers use when products meet expectations, feel good value, or solve a practical problem.
3. Comparing positive and negative wording can support product page improvements, such as clearer descriptions and stronger expectation-setting.
4. Repeated complaint phrases may suggest categories for manual tagging in a larger review-mining workflow.
5. These outputs are exploratory signals, not proof of broad market behaviour.

## Limitations

- This analysis uses a sampled public Hugging Face dataset, so it may not represent the full original dataset.
- Amazon reviews may not represent Shopee, TikTok Shop, Malaysia, or any specific local market.
- Sentiment groups are inferred from the available label/rating column and should be checked before commercial decisions.
- Word and phrase counts do not understand sarcasm, context, product category, or review authenticity.
- The findings should be treated as starting points for manual review and deeper analysis.
"""
