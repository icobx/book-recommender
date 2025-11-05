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
    min_n_ratings: int = 8


@dataclass(frozen=True)
class DatabaseConfig:
    db_dir: Path = Path("database")
    db_path: Path = db_dir / "books.db"
    db_scripts: Path = db_dir / "scripts"
    table_names: list[str] = field(default_factory=lambda: [
        "books",
        "ratings",
        "rated_books"
    ])
    table_names_set: set[str] = field(init=False)

    book_readers_sql: str = field(init=False)
    other_books_of_book_readers_sql: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "table_names_set", set(self.table_names))
        object.__setattr__(
            self,
            "book_readers_sql",
            (self.db_scripts / "s_book_readers.sql").read_text(encoding="utf-8")
        )
        object.__setattr__(
            self,
            "other_books_of_book_readers_sql",
            (self.db_scripts / "s_other_books_of_book_readers.sql").read_text(encoding="utf-8")
        )


config: Config = Config()
db_config: DatabaseConfig = DatabaseConfig()