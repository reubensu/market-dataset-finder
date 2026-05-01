from datasets import load_dataset
import pandas as pd
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import re


DATASET_ID = "SetFit/amazon_reviews_multi_en"
SPLIT = "train[:5000]"
OUTPUT_DIR = Path("analysis_outputs")


STOPWORDS = {
    "the", "and", "for", "this", "that", "with", "you", "was", "but", "are",
    "not", "have", "they", "from", "his", "her", "she", "him", "our", "your",
    "its", "very", "one", "all", "can", "had", "has", "were", "out", "get",
    "would", "there", "their", "what", "when", "which", "about", "also",
    "just", "too", "use", "used", "using", "buy", "bought", "like", "really",
}


def pick_column(df, candidates):
    for column in candidates:
        if column in df.columns:
            return column

    return None


def find_text_column(df):
    candidates = ["text", "review", "review_body", "content", "sentence", "comment"]
    column = pick_column(df, candidates)

    if column:
        return column

    text_like_columns = df.select_dtypes(include="object").columns

    if len(text_like_columns) == 0:
        return None

    return max(
        text_like_columns,
        key=lambda col: df[col].astype(str).str.len().mean()
    )


def find_label_column(df, text_column):
    candidates = ["label", "label_text", "rating", "stars", "overall", "score", "sentiment"]
    column = pick_column(df, candidates)

    if column and column != text_column:
        return column

    return None


def make_column_summary(df):
    return pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[col].dtype) for col in df.columns],
        "non_null": [df[col].notna().sum() for col in df.columns],
        "missing": [df[col].isna().sum() for col in df.columns],
        "missing_pct": [round(df[col].isna().mean() * 100, 2) for col in df.columns],
        "unique_values": [df[col].nunique() for col in df.columns],
    })


def get_top_words(df, text_column, top_n=30):
    text = " ".join(df[text_column].dropna().astype(str).str.lower())

    words = re.findall(r"[a-z]{3,}", text)
    words = [word for word in words if word not in STOPWORDS]

    return pd.DataFrame(
        Counter(words).most_common(top_n),
        columns=["word", "count"]
    )


def save_bar_chart(data, x_column, y_column, title, filename):
    plt.figure(figsize=(10, 6))
    plt.barh(data[y_column].astype(str), data[x_column])
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename)
    plt.close()


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"loading dataset: {DATASET_ID}")
    dataset = load_dataset(DATASET_ID, split=SPLIT)

    df = pd.DataFrame(dataset)

    text_column = find_text_column(df)
    label_column = find_label_column(df, text_column)

    overview = pd.DataFrame([{
        "dataset_id": DATASET_ID,
        "rows_loaded": len(df),
        "columns_loaded": len(df.columns),
        "text_column": text_column,
        "label_column": label_column,
    }])

    column_summary = make_column_summary(df)

    top_words = get_top_words(df, text_column) if text_column else pd.DataFrame()

    if label_column:
        label_counts = (
            df[label_column]
            .value_counts(dropna=False)
            .reset_index()
        )
        label_counts.columns = [label_column, "count"]
    else:
        label_counts = pd.DataFrame()

    df.head(100).to_csv(OUTPUT_DIR / "sample_rows.csv", index=False)

    with pd.ExcelWriter(OUTPUT_DIR / "analysis_summary.xlsx") as writer:
        overview.to_excel(writer, sheet_name="overview", index=False)
        column_summary.to_excel(writer, sheet_name="column_summary", index=False)
        top_words.to_excel(writer, sheet_name="top_words", index=False)
        label_counts.to_excel(writer, sheet_name="label_distribution", index=False)

    if not top_words.empty:
        save_bar_chart(
            data=top_words.sort_values("count"),
            x_column="count",
            y_column="word",
            title="top review words",
            filename="top_words.png"
        )

    if not label_counts.empty:
        save_bar_chart(
            data=label_counts.sort_values("count"),
            x_column="count",
            y_column=label_column,
            title="label distribution",
            filename="label_distribution.png"
        )

    print("done. outputs saved in analysis_outputs/")


if __name__ == "__main__":
    main()