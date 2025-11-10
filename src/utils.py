import html
import logging
import re
from pathlib import Path
from typing import Literal

import ftfy
import kagglehub
import pandas as pd

from src.config import LoggingConfig, config


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
    """Load and preprocess the Books dataset from the Kaggle directory.

    If the path is not provided, downloads the dataset using the Kaggle handle.
    Performs column renaming, text cleaning, and normalization of publication years.

    Args:
        kaggle_path: Optional path to the local Kaggle dataset directory.

    Returns:
        A tuple containing the preprocessed books DataFrame and the dataset path used.
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
    """Load and preprocess the Ratings dataset from the Kaggle directory.

    If the path is not provided, downloads the dataset using the Kaggle handle.
    Performs column renaming and filters out zero ratings.

    Args:
        kaggle_path: Optional path to the local Kaggle dataset directory.

    Returns:
        A tuple containing the preprocessed ratings DataFrame and the dataset path used.
    """
    if kaggle_path is None:
        kaggle_path = download_from_kaggle(config.kaggle_handle)

    ratings = pd.read_csv(kaggle_path / "Ratings.csv", sep=",", on_bad_lines="warn")
    ratings.columns = map(to_snake_case, ratings.columns)
    ratings = ratings.loc[ratings["book_rating"] > 0]

    return ratings, kaggle_path


def preprocess(
    table_name: Literal["books", "ratings"], kaggle_path: str | None
) -> tuple[pd.DataFrame, str]:
    """Dispatch preprocessing based on table name.

    Calls the appropriate preprocessing function for 'books' or 'ratings'.

    Args:
        table_name: Name of the table to preprocess. Must be either "books" or "ratings".
        kaggle_path: Optional path to the local Kaggle dataset directory.

    Returns:
        A tuple containing the preprocessed DataFrame and the dataset path used.
    """
    if table_name == "books":
        return preprocess_books(kaggle_path)

    if table_name == "ratings":
        return preprocess_ratings(kaggle_path)


def setup_logging():
    """Apply the logging configuration.

    Creates the logs directory if it does not exist and sets up the logging configuration
    defined in LoggingConfig.
    """
    log_config = LoggingConfig().to_dict()

    config.logs_dir.mkdir(exist_ok=True)

    logging.config.dictConfig(log_config)
