from pathlib import Path

import kagglehub
import pytest
from _pytest.monkeypatch import MonkeyPatch

from utils import clean_text, download_from_kaggle, to_snake_case


@pytest.mark.parametrize(
    argnames=("text_to_convert", "expectation"),
    argvalues=[
        ("BookTitle", "book_title"),
        ("Lord of the Rings", "lord_of_the_rings"),
        ("1984", "1984"),
        ("Animal-farm", "animal_farm"),
    ],
    ids=["pascal_case", "regular_title", "only_digits", "with_hyphen"],
)
def test_to_snake_case(text_to_convert: str, expectation: str):
    """Test `to_snake_case` function.

    Args:
        text_to_convert: Text to convert to snake case.
        expectation: Text expected after conversion.
    """
    assert to_snake_case(text_to_convert) == expectation


@pytest.mark.parametrize(
    argnames=("text_to_clean", "expectation"),
    argvalues=[("FranÃ§ais", "Français"), ("Tom &amp; Jerry", "Tom & Jerry")],
    ids=["mojibake", "html_escape"],
)
def test_clean_text(text_to_clean: str, expectation: str):
    """Test `clean_text` function.

    Args:
        text_to_clean: Text to clean.
        expectation: Text expected after cleaning.
    """
    assert clean_text(text_to_clean) == expectation


def test_download_from_kaggle(monkeypatch: MonkeyPatch):
    """Test `download_from_kaggle` function.

    Args:
        monkeypatch: Monkeypatch fixture used for mocking.
            It is passed automatically by pytest.
    """
    mock_path = "user/dataset-handle"

    def mock_dataset_download(handle):
        return str(handle)

    monkeypatch.setattr(kagglehub, "dataset_download", mock_dataset_download)

    result = download_from_kaggle(mock_path)

    assert isinstance(result, Path)
    assert result == Path(mock_path)
