import math

from src.config import (
    NEGATIVE_KEYWORDS,
    POSITIVE_KEYWORDS,
    USEFUL_LANGUAGE_WORDS,
    USEFUL_TASK_WORDS,
)


DECISION_RANKS = {
    "strong candidate": 1,
    "review manually": 2,
    "secondary": 3,
    "check licence": 4,
    "check access": 5,
    "low priority": 6,
}


def classify_dataset(text: str) -> str:
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
    if "market research" in text or "consumer" in text:
        return "market / consumer research"
    if "customer" in text:
        return "customer behaviour / support"
    if "image" in text or "video" in text or "audio" in text:
        return "media dataset"
    return "general / needs review"


def calculate_component_scores(row: dict) -> dict:
    text = " ".join(
        str(row.get(field, ""))
        for field in ["dataset_id", "search_term", "description", "tags", "task_categories"]
    ).lower()

    keyword_score = 0
    for keyword, weight in POSITIVE_KEYWORDS.items():
        if keyword in text:
            keyword_score += weight

    penalty_score = 0
    for keyword, weight in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            penalty_score += weight

    relevance_score = max(min(keyword_score + penalty_score, 60), 0)

    downloads = int(row.get("downloads") or 0)
    likes = int(row.get("likes") or 0)
    download_score = min(math.log10(downloads + 1) * 4.0, 12)
    like_score = min(math.log10(likes + 1) * 3.0, 8)
    popularity_score = round(download_score + like_score, 2)

    metadata_quality_score = calculate_metadata_quality(row)

    access_penalty = 8 if row.get("access") == "gated" else 0
    overall_score = round(
        relevance_score + popularity_score + metadata_quality_score - access_penalty,
        2,
    )

    return {
        "relevance_score": round(relevance_score, 2),
        "popularity_score": popularity_score,
        "metadata_quality_score": metadata_quality_score,
        "overall_score": max(overall_score, 0),
    }


def calculate_metadata_quality(row: dict) -> float:
    score = 0

    if row.get("description"):
        score += 7
    if row.get("licence"):
        score += 6
    if row.get("language"):
        score += 3
    if row.get("task_categories"):
        score += 4
    if row.get("tags"):
        score += 3
    if row.get("last_modified"):
        score += 2

    text = f"{row.get('language', '')} {row.get('task_categories', '')} {row.get('tags', '')}".lower()
    if any(word in text for word in USEFUL_TASK_WORDS):
        score += 3
    if any(word in text for word in USEFUL_LANGUAGE_WORDS):
        score += 2

    return min(score, 30)


def infer_use_case(category: str) -> str:
    if category == "amazon product reviews":
        return "review analysis, sentiment comparison, complaint mining, ratings analysis"
    if category == "shopee / marketplace":
        return "marketplace research and regional e-commerce exploration"
    if category == "product reviews":
        return "consumer sentiment, product feedback, review text analysis"
    if category == "sentiment analysis":
        return "sentiment modelling or language pattern analysis"
    if category == "e-commerce / retail":
        return "online retail, catalogue, transaction, or customer behaviour research"
    if category == "market / consumer research":
        return "exploratory market research and consumer behaviour analysis"
    if category == "customer behaviour / support":
        return "customer support or service pattern analysis; check review fit manually"
    if category == "media dataset":
        return "likely weak fit for text review analysis unless product metadata is included"
    return "manual review needed"


def create_decision(row: dict) -> tuple[str, int, str]:
    category = row.get("category", "")
    overall_score = row.get("overall_score", 0)
    relevance_score = row.get("relevance_score", 0)
    licence = row.get("licence", "")
    access = row.get("access", "")
    downloads = int(row.get("downloads") or 0)

    reasons = []

    if access == "gated":
        decision = "check access"
        reasons.append("access may be restricted")
    elif not licence:
        decision = "check licence"
        reasons.append("licence is missing or unclear")
    elif overall_score >= 75 and relevance_score >= 40:
        decision = "strong candidate"
        reasons.append("high review/e-commerce relevance with usable metadata")
    elif any(word in category for word in ["product reviews", "amazon", "shopee", "sentiment"]):
        decision = "review manually"
        reasons.append("matches the project theme but should be checked for fields and licence")
    elif any(word in category for word in ["retail", "consumer", "customer"]):
        decision = "secondary"
        reasons.append("market-related but may not contain product review text")
    else:
        decision = "low priority"
        reasons.append("weak fit for product-review market analysis")

    if downloads > 0:
        reasons.append("has download activity, but popularity is only one signal")
    if row.get("metadata_quality_score", 0) >= 20:
        reasons.append("metadata is reasonably complete")

    return decision, DECISION_RANKS.get(decision, 99), "; ".join(reasons)
