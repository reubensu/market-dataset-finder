import argparse

from src.config import (
    ANALYSIS_OUTPUT_DIR,
    DEFAULT_ANALYSIS_DATASET,
    DEFAULT_ANALYSIS_SPLIT,
    DEFAULT_RANDOM_SEED,
    DEFAULT_SAMPLE_SIZE,
)
from src.review_analysis import run_review_analysis


def main():
    parser = argparse.ArgumentParser(description="Analyse a selected product-review dataset.")
    parser.add_argument("--dataset", default=DEFAULT_ANALYSIS_DATASET, help="Hugging Face dataset id.")
    parser.add_argument("--split", default=DEFAULT_ANALYSIS_SPLIT, help="Dataset split to load.")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE, help="Rows to sample after shuffling.")
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed for shuffling.")
    args = parser.parse_args()

    try:
        result = run_review_analysis(
            dataset_id=args.dataset,
            split=args.split,
            sample_size=args.sample_size,
            output_dir=ANALYSIS_OUTPUT_DIR,
            seed=args.seed,
        )
    except Exception as exc:
        print(f"error: {exc}")
        raise SystemExit(1)

    print(f"done. analysed {result['rows_sampled']:,} rows.")
    print(f"text column: {result['text_column']}")
    print(f"label column: {result['label_column']}")
    print(f"outputs saved in: {result['output_dir']}")


if __name__ == "__main__":
    main()
