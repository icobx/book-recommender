import logging
import html
import re
from pathlib import Path

import ftfy
import kagglehub
import pandas as pd

from src.config import config, LoggingConfig



def to_snake_case(text: str) -> str:
    """Convert a string to snake_case.

    Args:
        text: Text to convert to snake case.

    Returns:
        Text converted to snake case.
    """
    text = re.sub(r"[\-\s]+", "_", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    return text.lower()


def clean_text(text: str) -> str:
    """Clean text using ftfy and unescape html notation.

    Args:
        text: Text to clean.

    Returns:
        Clean text.
    """
    if not isinstance(text, str):
        return text

    return html.unescape(ftfy.fix_text(text))


def download_from_kaggle(handle: str) -> Path:
    """Download dataset from Kaggle.

    Args:
        handle: String identifier of a dataset on Kaggle.

    Returns:
        Path to the downloaded datset.
    """
    return Path(kagglehub.dataset_download(handle))


def preprocess_books(kaggle_path: str | None = None) -> tuple[pd.DataFrame, str]:
    """Downloads and preprocesses the book dataset from Kaggle.

    1. Downloads the dataset if not already present.
    2. Cleans text columns (trims, lowercases, removes noise).
    3. Filters ratings > 0.
    4. Merges books and ratings into a single CSV file (`merged.csv`).
    """
    if kaggle_path is None:
        kaggle_path = download_from_kaggle(config.kaggle_handle)

    books = pd.read_csv(
        kaggle_path / "Books.csv", sep=",", on_bad_lines="warn", encoding="cp1251"
    )
    books.columns = map(to_snake_case, books.columns)
    books["year_of_publication"] = (
        pd.to_numeric(books["year_of_publication"], errors="coerce")
        .astype("Int64")
        .replace([0], pd.NA)
    )
    for c in config.string_cols[: config.non_lc_bound]:
        books[c] = books[c].astype("string").str.strip()
        books[c] = books[c].map(clean_text)

    books["book_title_lc"] = books["book_title"].str.lower()

    return books, kaggle_path


def preprocess_ratings(kaggle_path: str | None = None) -> tuple[pd.DataFrame, str]:
    if kaggle_path is None:
        kaggle_path = download_from_kaggle(config.kaggle_handle)

    ratings = pd.read_csv(kaggle_path / "Ratings.csv", sep=",", on_bad_lines="warn")
    ratings.columns = map(to_snake_case, ratings.columns)
    ratings = ratings.loc[ratings["book_rating"] > 0]

    return ratings, kaggle_path


def preprocess(table_name: str, kaggle_path: str | None) -> tuple[pd.DataFrame, str]:
    if table_name == "books":
        return preprocess_books(kaggle_path)

    if table_name == "ratings":
        return preprocess_ratings(kaggle_path)


def setup_logging():
    """Apply the logging configuration."""
    log_config = LoggingConfig().to_dict()

    config.logs_dir.mkdir(exist_ok=True)

    logging.config.dictConfig(log_config)