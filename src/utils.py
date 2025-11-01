import html
import re
from pathlib import Path

import ftfy
import kagglehub


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
