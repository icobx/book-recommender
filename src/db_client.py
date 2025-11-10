import logging
import sqlite3
from pathlib import Path

from src.config import db_config
from src.utils import preprocess

logger = logging.getLogger(__name__)


class Singleton(type):
    """Singleton metaclass.

    Attributes:
        _instances: Dictionary of existing instances of children classes.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call method of the metaclass.

        Returns:
            Instance of the child class.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        else:
            cls._instances[cls].__init__(*args, **kwargs)

        return cls._instances[cls]


class DatabaseClient(metaclass=Singleton):
    """DatabaseClient (singleton) class provides an interface for connecting to and
    managing local database.

    Attributes:
        conn: Database connection object.
    """

    def __init__(self) -> None:
        """Initialize DatabaseClient class.

        Open connection. Run init scripts and populate tables if not yet populated.
        """
        self.kaggle_path = None

        self.open_connection()
        self.run_init_scripts()
        self.populate_tables()

    def open_connection(self):
        """Open database connection."""
        logger.info("Opening DB connection.")
        self.conn = sqlite3.connect(db_config.db_path)

    def close_connection(self):
        """Close database connection."""
        logger.info("Closing DB connection.")
        if self.conn:
            self.conn.close()
            self.conn = None

    def ensure_connection(self):
        """Ensure database connection is open."""
        if not self.conn:
            self.open_connection()

    def get_cursor(self) -> sqlite3.Cursor:
        """Get database connection cursor required for executing database commands.

        Returns:
            Cursor object.
        """
        self.ensure_connection()

        return self.conn.cursor()

    def is_empty(self, table_name: str) -> bool:
        """Check if table with provided table_name is empty.

        Args:
            table_name: Table name.

        Returns:
            True if table is empty, else False.
        """
        self.validate_table_name(table_name)

        return not bool(
            self.get_cursor()
            .execute(f"SELECT EXISTS (SELECT 1 FROM {table_name});")
            .fetchone()[0]
        )

    def validate_table_name(self, table_name: str):
        """Validate whether a given table name is recognized.

        Args:
            table_name: The name of the table to validate.

        Raises:
            ValueError: If `table_name` is not among expected names.
        """
        if table_name not in db_config.table_names_set:
            msg = f"Arg `table_name` must be one of {db_config.table_names}"
            logger.exception(msg)
            raise ValueError(msg)

    def run_init_scripts(self):
        """Run initialization SQL scripts for database setup.

        Executes all SQL files in the `db_scripts` directory that match
        the pattern `m_*.sql`. Scripts are run in sorted order.
        """
        logger.info("Running DB init scripts.")
        for mf in sorted(db_config.db_scripts.glob("m_*.sql")):
            with open(mf, "r") as handle:
                logger.info("Running %s script.", mf.stem)
                self.conn.executescript(handle.read())
                self.conn.commit()

    def populate_tables(self):
        """Populate the database tables with data.

        For each table defined in the config:
        - If it is already populated, skip it.
        - If it is `rated_books`, populate it using a pre-written SQL script.
        - Otherwise, preprocess raw data and insert it into the database.
        """
        logger.info("Populating DB tables.")
        for tn in db_config.table_names:
            if not self.is_empty(tn):
                logger.info("Table %s is not empty. Skipping.", tn)
                continue

            if tn == "rated_books":
                logger.info("Populating rated_books table.")
                with open(
                    db_config.db_scripts / "s_populate_rated_books.sql", "r"
                ) as handle:
                    self.conn.executescript(handle.read())
                    self.conn.commit()

                continue

            logger.info("Preprocessing data for table %s.", tn)
            table, self.kaggle_path = preprocess(tn, self.kaggle_path)

            logger.info("Writing to database.")
            table.to_sql(tn, self.conn, if_exists="replace")
            self.conn.commit()

    def drop_table(self, table_name: str):
        """Drop a table from the database.

        Args:
            table_name: The name of the table to be dropped.

        Raises:
            ValueError: If `table_name` is invalid.
        """
        self.validate_table_name(table_name)

        self.get_cursor().execute(f"DROP TABLE {table_name}")
        self.conn.commit()
