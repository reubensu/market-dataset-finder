from datetime import datetime
from pathlib import Path


def clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").strip()


def shorten_text(value, max_length=300) -> str:
    text = clean_text(value)
    if len(text) <= max_length:
        return text
    return text[:max_length].strip() + "..."


def join_list(value, max_items=12) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(clean_text(item) for item in list(value)[:max_items])
    return clean_text(value)


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_run_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
