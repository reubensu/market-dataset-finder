from pathlib import Path


SEARCH_TERMS = [
    "ecommerce",
    "e-commerce",
    "shopping",
    "product reviews",
    "customer reviews",
    "amazon reviews",
    "product sentiment",
    "consumer behaviour",
    "consumer behavior",
    "market research",
    "online retail",
    "marketplace",
    "shopee product reviews",
]

DEFAULT_SEARCH_LIMIT = 20
DATASET_RESULTS_XLSX = Path("dataset_results.xlsx")
DATASET_RESULTS_CSV = Path("dataset_results.csv")

DEFAULT_ANALYSIS_DATASET = "SetFit/amazon_reviews_multi_en"
DEFAULT_ANALYSIS_SPLIT = "train"
DEFAULT_SAMPLE_SIZE = 5000
DEFAULT_RANDOM_SEED = 42
ANALYSIS_OUTPUT_DIR = Path("analysis_outputs")

POSITIVE_KEYWORDS = {
    "amazon": 16,
    "review": 16,
    "reviews": 16,
    "rating": 12,
    "ratings": 12,
    "product": 12,
    "products": 12,
    "ecommerce": 12,
    "e-commerce": 12,
    "shopping": 10,
    "retail": 10,
    "customer": 9,
    "consumer": 9,
    "sentiment": 9,
    "marketplace": 9,
    "market research": 8,
    "purchase": 7,
    "shopee": 12,
}

NEGATIVE_KEYWORDS = {
    "audio": -18,
    "image": -14,
    "images": -14,
    "video": -16,
    "videos": -16,
    "speech": -14,
    "chatbot": -12,
    "faq": -10,
    "question answering": -10,
    "game": -8,
    "games": -8,
    "medical": -8,
}

USEFUL_TASK_WORDS = {
    "text-classification",
    "sentiment-analysis",
    "classification",
    "text-generation",
    "tabular-classification",
}

USEFUL_LANGUAGE_WORDS = {"en", "english", "multi", "multilingual"}

CUSTOM_STOPWORDS = {
    "the", "and", "for", "this", "that", "with", "you", "was", "but", "are",
    "not", "have", "they", "from", "his", "her", "she", "him", "our", "your",
    "its", "very", "one", "all", "can", "had", "has", "were", "out", "get",
    "would", "there", "their", "what", "when", "which", "about", "also",
    "just", "too", "use", "used", "using", "buy", "bought", "like", "really",
    "product", "products", "item", "items", "amazon", "ordered", "received",
    "order", "delivery", "package", "thing", "things", "got", "make", "made",
    "even", "much", "many", "still", "will", "could", "should", "did", "does",
}
