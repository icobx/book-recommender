from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class Config:
    data_dir: Path = Path("data")
    kaggle_handle: str = "arashnic/book-recommendation-dataset"
    string_cols: list[str] = field(default_factory=lambda: [
        "book_title",
        "book_author",
        "publisher",
        "book_title_lc",
    ])
    non_lc_bound: int = 3
