from datasets import load_dataset
import pandas as pd
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import re


DATASET_ID = "SetFit/amazon_reviews_multi_en"
SPLIT = "train"
SAMPLE_SIZE = 5000
OUTPUT_DIR = Path("analysis_outputs")


STOPWORDS = {
    "the", "and", "for", "this", "that", "with", "you", "was", "but", "are",
    "not", "have", "they", "from", "his", "her", "she", "him", "our", "your",
    "its", "very", "one", "all", "can", "had", "has", "were", "out", "get",
    "would", "there", "their", "what", "when", "which", "about", "also",
    "just", "too", "use", "used", "using", "buy", "bought", "like", "really",
    "product", "item", "amazon", "ordered", "received"
}


def find_text_column(df):
    candidates = ["text", "review", "review_body", "content", "sentence", "comment"]

    for column in candidates:
        if column in df.columns:
            return column

    text_columns = df.select_dtypes(include="object").columns

    if len(text_columns) == 0:
        return None

    return max(text_columns, key=lambda col: df[col].astype(str).str.len().mean())


def find_label_column(df, text_column):
    candidates = ["label", "rating", "stars", "overall", "score", "sentiment"]

    for column in candidates:
        if column in df.columns and column != text_column:
            return column

    return None


def clean_words(text):
    words = re.findall(r"[a-z]{3,}", str(text).lower())
    return [word for word in words if word not in STOPWORDS]


def make_ngrams(words, n):
    return [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]


def top_terms(texts, ngram_size=1, top_n=30):
    counter = Counter()

    for text in texts.dropna():
        words = clean_words(text)

        if ngram_size == 1:
            terms = words
        else:
            terms = make_ngrams(words, ngram_size)

        counter.update(terms)

    return pd.DataFrame(counter.most_common(top_n), columns=["term", "count"])


def add_sentiment_group(df, label_column):
    df = df.copy()

    if label_column is None:
        df["sentiment_group"] = "unknown"
        return df

    labels = pd.to_numeric(df[label_column], errors="coerce")

    if labels.notna().any():
        df["sentiment_group"] = "neutral"
        df.loc[labels <= labels.quantile(0.35), "sentiment_group"] = "negative"
        df.loc[labels >= labels.quantile(0.65), "sentiment_group"] = "positive"
        return df

    label_text = df[label_column].astype(str).str.lower()

    df["sentiment_group"] = "neutral"
    df.loc[label_text.str.contains("negative|bad|poor|1|2"), "sentiment_group"] = "negative"
    df.loc[label_text.str.contains("positive|good|great|4|5"), "sentiment_group"] = "positive"

    return df


def make_column_summary(df):
    return pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[col].dtype) for col in df.columns],
        "non_null": [df[col].notna().sum() for col in df.columns],
        "missing": [df[col].isna().sum() for col in df.columns],
        "missing_pct": [round(df[col].isna().mean() * 100, 2) for col in df.columns],
        "unique_values": [df[col].nunique() for col in df.columns],
    })


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
    dataset = dataset.shuffle(seed=42).select(range(SAMPLE_SIZE))

    df = pd.DataFrame(dataset)

    text_column = find_text_column(df)
    label_column = find_label_column(df, text_column)

    df = add_sentiment_group(df, label_column)

    overview = pd.DataFrame([{
        "dataset_id": DATASET_ID,
        "rows_loaded": len(df),
        "columns_loaded": len(df.columns),
        "text_column": text_column,
        "label_column": label_column,
    }])

    column_summary = make_column_summary(df)

    sentiment_counts = (
        df["sentiment_group"]
        .value_counts()
        .reset_index()
    )
    sentiment_counts.columns = ["sentiment_group", "count"]

    negative_reviews = df[df["sentiment_group"] == "negative"][text_column]
    positive_reviews = df[df["sentiment_group"] == "positive"][text_column]

    negative_words = top_terms(negative_reviews, ngram_size=1)
    positive_words = top_terms(positive_reviews, ngram_size=1)

    negative_phrases = top_terms(negative_reviews, ngram_size=2)
    positive_phrases = top_terms(positive_reviews, ngram_size=2)

    df.head(100).to_csv(OUTPUT_DIR / "sample_rows.csv", index=False)

    with pd.ExcelWriter(OUTPUT_DIR / "analysis_summary.xlsx") as writer:
        overview.to_excel(writer, sheet_name="overview", index=False)
        column_summary.to_excel(writer, sheet_name="column_summary", index=False)
        sentiment_counts.to_excel(writer, sheet_name="sentiment_counts", index=False)
        negative_words.to_excel(writer, sheet_name="negative_words", index=False)
        positive_words.to_excel(writer, sheet_name="positive_words", index=False)
        negative_phrases.to_excel(writer, sheet_name="negative_phrases", index=False)
        positive_phrases.to_excel(writer, sheet_name="positive_phrases", index=False)

    save_bar_chart(
        sentiment_counts.sort_values("count"),
        x_column="count",
        y_column="sentiment_group",
        title="review sentiment distribution",
        filename="sentiment_distribution.png"
    )

    save_bar_chart(
        negative_phrases.sort_values("count"),
        x_column="count",
        y_column="term",
        title="top negative review phrases",
        filename="negative_phrases.png"
    )

    save_bar_chart(
        positive_phrases.sort_values("count"),
        x_column="count",
        y_column="term",
        title="top positive review phrases",
        filename="positive_phrases.png"
    )

    print("done. upgraded analysis saved in analysis_outputs/")


if __name__ == "__main__":
    main()