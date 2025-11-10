from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """General configuration for dataset and preprocessing.

    Attributes:
        data_dir: Path to the local data directory.
        logs_dir: Path to the directory for log files.
        kaggle_handle: Identifier of the Kaggle dataset.
        string_cols: Columns in the dataset expected to be strings.
        non_lc_bound: Index separating columns that should be lowercased.
        min_n_ratings: Minimum number of ratings needed to consider a book for recommendations.
    """

    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")
    kaggle_handle: str = "arashnic/book-recommendation-dataset"
    string_cols: list[str] = field(
        default_factory=lambda: [
            "book_title",
            "book_author",
            "publisher",
            "book_title_lc",
        ]
    )
    non_lc_bound: int = 3
    min_n_ratings: int = 8


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for database file locations and SQL scripts.

    Attributes:
        db_dir: Directory where the SQLite database is stored.
        db_path: Full path to the SQLite database file.
        db_scripts: Path to the directory containing SQL query files.
        table_names: Names of all expected tables.
        table_names_set: Set version of `table_names` for quick lookup.
        book_readers_sql: SQL script for selecting readers of a book.
        other_books_of_book_readers_sql: SQL script to find other books rated by same users.
        books_by_titles: SQL script to get metadata for a list of books by title.
    """

    db_dir: Path = Path("database")
    db_path: Path = db_dir / "books.db"
    db_scripts: Path = db_dir / "scripts"
    table_names: list[str] = field(
        default_factory=lambda: ["books", "ratings", "rated_books"]
    )
    table_names_set: set[str] = field(init=False)

    book_readers_sql: str = field(init=False)
    other_books_of_book_readers_sql: str = field(init=False)
    books_by_titles: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "table_names_set", set(self.table_names))

        for script_fn in [
            "s_book_readers",
            "s_other_books_of_book_readers",
            "s_books_by_titles",
            "s_book_titles_by_title",
        ]:
            object.__setattr__(
                self,
                f"{script_fn[2:]}_sql",
                (self.db_scripts / f"{script_fn}.sql").read_text(encoding="utf-8"),
            )


@dataclass(frozen=True)
class LoggingFormatterConfig:
    """Defines format string for a log formatter.

    Attributes:
        format: Format string used by the logging formatter.
    """

    format: str = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"


@dataclass(frozen=True)
class LoggingHandlerConfig:
    """Configuration for a log handler.

    Attributes:
        class_: Logging handler class path.
        formatter: Name of the formatter to use.
        level: Minimum log level for this handler.
        extra: Dictionary of additional handler-specific config values (e.g., filename).
    """

    class_: str
    formatter: str
    level: str
    extra: dict[str, any] = field(default_factory=dict)

    def to_dict(self):
        """Convert the handler config to dictionary format used by logging.config.dictConfig()."""
        data = {
            "class": self.class_,
            "formatter": self.formatter,
            "level": self.level,
            **self.extra,
        }
        return data


@dataclass(frozen=True)
class LoggingLoggerConfig:
    """Configuration for a logger.

    Attributes:
        handlers: List of handler names to attach to the logger.
        level: Log level (e.g. INFO, DEBUG).
        propagate: Whether log messages should bubble up to the root logger.
    """

    handlers: list[str]
    level: str
    propagate: bool


@dataclass(frozen=True)
class LoggingConfig:
    """Top-level configuration for logging.

    Contains formatter, handler, and logger definitions in a structure
    compatible with `logging.config.dictConfig`.

    Attributes:
        version: Logging config version (always 1).
        disable_existing_loggers: Whether to disable loggers not explicitly configured.
        formatters: Dict of named formatter configurations.
        handlers: Dict of named handler configurations.
        loggers: Dict of named logger configurations (e.g., for uvicorn).
        root: Root logger configuration.
    """

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict[str, LoggingFormatterConfig] = field(
        default_factory=lambda: {
            "default": LoggingFormatterConfig(),
        }
    )
    handlers: dict[str, LoggingHandlerConfig] = field(
        default_factory=lambda: {
            "console": LoggingHandlerConfig(
                class_="logging.StreamHandler",
                formatter="default",
                level="INFO",
                extra={"stream": "ext://sys.stdout"},
            ),
            "file": LoggingHandlerConfig(
                class_="logging.handlers.RotatingFileHandler",
                formatter="default",
                level="INFO",
                extra={
                    "filename": "logs/app.log",
                    "maxBytes": 10_485_760,
                    "backupCount": 3,
                },
            ),
        }
    )
    loggers: dict[str, LoggingLoggerConfig] = field(
        default_factory=lambda: {
            "uvicorn": LoggingLoggerConfig(
                handlers=["console", "file"], level="INFO", propagate=False
            ),
            "uvicorn.error": LoggingLoggerConfig(
                handlers=["console", "file"], level="INFO", propagate=False
            ),
            "uvicorn.access": LoggingLoggerConfig(
                handlers=["console", "file"], level="INFO", propagate=False
            ),
        }
    )
    root: LoggingLoggerConfig = field(
        default_factory=lambda: LoggingLoggerConfig(
            handlers=["console", "file"], level="INFO", propagate=False
        )
    )

    def to_dict(self) -> dict[str, any]:
        """Convert dataclass to dict suitable for dictConfig()."""
        return {
            "version": self.version,
            "disable_existing_loggers": self.disable_existing_loggers,
            "formatters": {name: asdict(fmt) for name, fmt in self.formatters.items()},
            "handlers": {
                name: handler.to_dict() for name, handler in self.handlers.items()
            },
            "loggers": {name: asdict(logger) for name, logger in self.loggers.items()},
            "root": asdict(self.root),
        }


config: Config = Config()
db_config: DatabaseConfig = DatabaseConfig()
