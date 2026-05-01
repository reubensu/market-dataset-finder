import pandas as pd
from huggingface_hub import HfApi

from src.config import SEARCH_TERMS
from src.scoring import calculate_component_scores, classify_dataset, create_decision, infer_use_case
from src.utils import clean_text, join_list, shorten_text


def search_huggingface_datasets(limit_per_term: int = 20) -> pd.DataFrame:
    api = HfApi()
    rows = []

    for term in SEARCH_TERMS:
        print(f"searching Hugging Face datasets for: {term}")
        try:
            datasets = api.list_datasets(search=term, limit=limit_per_term, full=True)
            for dataset in datasets:
                rows.append(dataset_to_row(dataset, term))
        except Exception as exc:
            print(f"warning: search failed for '{term}': {exc}")

    if not rows:
        raise RuntimeError(
            "No datasets were returned. Check your internet connection or try a smaller search."
        )

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["dataset_id"]).copy()

    score_rows = df.apply(lambda row: calculate_component_scores(row.to_dict()), axis=1)
    scores = pd.DataFrame(list(score_rows))
    df = pd.concat([df.reset_index(drop=True), scores], axis=1)

    decisions = df.apply(lambda row: create_decision(row.to_dict()), axis=1)
    df["decision"] = [item[0] for item in decisions]
    df["decision_rank"] = [item[1] for item in decisions]
    df["reason"] = [item[2] for item in decisions]

    columns = [
        "source", "search_term", "dataset_id", "category", "use_case",
        "downloads", "likes", "relevance_score", "popularity_score",
        "metadata_quality_score", "overall_score", "decision_rank", "decision",
        "reason", "access", "licence", "language", "task_categories", "tags",
        "last_modified", "description", "url",
    ]

    df = df[columns]
    df = df.sort_values(
        by=["decision_rank", "overall_score", "relevance_score", "downloads"],
        ascending=[True, False, False, False],
    )

    return df


def dataset_to_row(dataset, search_term: str) -> dict:
    dataset_id = clean_text(getattr(dataset, "id", ""))
    description = shorten_text(getattr(dataset, "description", ""), max_length=500)
    tags = join_list(getattr(dataset, "tags", []))
    card_data = get_card_data(dataset)

    licence = first_card_value(card_data, ["license", "licence", "license_name"])
    language = first_card_value(card_data, ["language", "languages"])
    task_categories = first_card_value(card_data, ["task_categories", "task_ids"])

    access = "gated" if getattr(dataset, "gated", False) else "public"
    last_modified = clean_text(
        getattr(dataset, "last_modified", None)
        or getattr(dataset, "lastModified", None)
        or getattr(dataset, "created_at", None)
    )

    category_text = f"{dataset_id} {search_term} {description} {tags} {task_categories}"
    category = classify_dataset(category_text)

    return {
        "source": "Hugging Face",
        "search_term": search_term,
        "dataset_id": dataset_id,
        "category": category,
        "use_case": infer_use_case(category),
        "downloads": int(getattr(dataset, "downloads", 0) or 0),
        "likes": int(getattr(dataset, "likes", 0) or 0),
        "access": access,
        "licence": licence,
        "language": language,
        "task_categories": task_categories,
        "tags": tags,
        "last_modified": last_modified,
        "description": description,
        "url": f"https://huggingface.co/datasets/{dataset_id}",
    }


def get_card_data(dataset) -> dict:
    card_data = getattr(dataset, "card_data", None)

    if card_data is None:
        return {}
    if isinstance(card_data, dict):
        return card_data
    if hasattr(card_data, "to_dict"):
        return card_data.to_dict()
    return {}


def first_card_value(card_data: dict, names: list[str]) -> str:
    for name in names:
        value = card_data.get(name)
        if value:
            return join_list(value)
    return ""
