import argparse

from src.config import DATASET_RESULTS_CSV, DATASET_RESULTS_XLSX, DEFAULT_SEARCH_LIMIT
from src.dataset_search import search_huggingface_datasets
from src.excel_export import save_dataframe_workbook
from src.utils import now_string, write_run_log


def main():
    parser = argparse.ArgumentParser(description="Find and rank public market-analysis datasets.")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_SEARCH_LIMIT,
        help="Maximum Hugging Face results per search term.",
    )
    args = parser.parse_args()

    try:
        df = search_huggingface_datasets(limit_per_term=args.limit)
        df.to_csv(DATASET_RESULTS_CSV, index=False)
        save_dataframe_workbook(df, DATASET_RESULTS_XLSX, sheet_name="dataset shortlist")
        write_run_log(
            DATASET_RESULTS_CSV.with_name("run_log.txt"),
            [
                f"Run time: {now_string()}",
                f"Search limit per term: {args.limit}",
                f"Unique datasets found: {len(df)}",
                f"Generated: {DATASET_RESULTS_CSV}",
                f"Generated: {DATASET_RESULTS_XLSX}",
            ],
        )
    except Exception as exc:
        print(f"error: {exc}")
        raise SystemExit(1)

    print(f"done. saved {len(df)} unique datasets.")
    print(f"files created: {DATASET_RESULTS_CSV} and {DATASET_RESULTS_XLSX}")


if __name__ == "__main__":
    main()
