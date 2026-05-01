from huggingface_hub import HfApi
import pandas as pd
import math
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


SEARCH_TERMS = [
    "ecommerce",
    "shopping",
    "product reviews",
    "consumer behaviour",
    "market research",
    "amazon reviews",
    "online retail",
    "customer reviews",
    "product sentiment",
    "marketplace",
    "shopee product reviews",
]


POSITIVE_KEYWORDS = {
    "amazon": 35,
    "review": 35,
    "reviews": 35,
    "product": 30,
    "products": 30,
    "ecommerce": 30,
    "e-commerce": 30,
    "shopping": 25,
    "retail": 25,
    "customer": 20,
    "sentiment": 20,
    "marketplace": 20,
    "rating": 15,
    "ratings": 15,
    "consumer": 15,
    "shopee": 30,
}


NEGATIVE_KEYWORDS = {
    "audio": -40,
    "image": -25,
    "video": -25,
    "chatbot": -20,
    "faq": -15,
    "games": -15,
    "multilingual": -10,
}


def classify_dataset(text):
    text = text.lower()

    if "shopee" in text:
        return "shopee / marketplace"

    if "amazon" in text and "review" in text:
        return "amazon product reviews"

    if "product" in text and "review" in text:
        return "product reviews"

    if "sentiment" in text:
        return "sentiment analysis"

    if "ecommerce" in text or "e-commerce" in text or "retail" in text:
        return "e-commerce / retail"

    if "customer" in text:
        return "customer behaviour / support"

    if "image" in text:
        return "image / visual search"

    return "general / needs review"


def calculate_relevance(dataset_id, search_term, downloads, likes):
    text = f"{dataset_id} {search_term}".lower()

    keyword_score = 0

    for keyword, weight in POSITIVE_KEYWORDS.items():
        if keyword in text:
            keyword_score += weight

    for keyword, weight in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            keyword_score += weight

    popularity_score = math.log10(downloads + 1) * 20
    like_score = math.log10(likes + 1) * 15

    return round(keyword_score + popularity_score + like_score, 2)


def create_decision(category, relevance_score, downloads):
    if relevance_score >= 160 and downloads >= 100:
        return "strong candidate"

    if "product reviews" in category or "amazon" in category or "shopee" in category:
        return "review manually"

    if "image" in category or "support" in category:
        return "secondary"

    return "low priority"


def search_huggingface_datasets(search_term, limit=20):
    api = HfApi()

    datasets = api.list_datasets(
        search=search_term,
        limit=limit
    )

    results = []

    for dataset in datasets:
        dataset_id = dataset.id
        downloads = dataset.downloads or 0
        likes = dataset.likes or 0

        category = classify_dataset(f"{dataset_id} {search_term}")
        relevance_score = calculate_relevance(dataset_id, search_term, downloads, likes)
        decision = create_decision(category, relevance_score, downloads)

        results.append({
            "source": "hugging face",
            "search_term": search_term,
            "dataset_id": dataset_id,
            "category": category,
            "downloads": downloads,
            "likes": likes,
            "relevance_score": relevance_score,
            "decision": decision,
            "url": f"https://huggingface.co/datasets/{dataset_id}"
        })

    return results


def format_excel_file(filename):
    workbook = load_workbook(filename)
    sheet = workbook.active

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for column_cells in sheet.columns:
        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)

        for cell in column_cells:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        sheet.column_dimensions[column_letter].width = min(max_length + 2, 45)

    workbook.save(filename)


def main():
    all_results = []

    for term in SEARCH_TERMS:
        print(f"searching for: {term}")
        results = search_huggingface_datasets(term)
        all_results.extend(results)

    df = pd.DataFrame(all_results)

    df = df.drop_duplicates(subset=["dataset_id"])

    df = df.sort_values(
        by=["relevance_score", "downloads", "likes"],
        ascending=False
    )

    df.to_csv("dataset_results.csv", index=False)
    df.to_excel("dataset_results.xlsx", index=False)

    format_excel_file("dataset_results.xlsx")

    print(f"done. saved {len(df)} unique datasets.")
    print("files created: dataset_results.csv and dataset_results.xlsx")


if __name__ == "__main__":
    main()