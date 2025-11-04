from pathlib import Path
import sqlite3

from utils import preprocess

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
    """DatabaseClient singleton class provides an interface for connecting to and
    managing local database.

    Attributes:
        conn: Database connection object.
    """
    DB_DIR = Path("database")
    DB_PATH = DB_DIR / "books.db"
    DB_SCRIPTS = DB_DIR / "scripts"
    TABLES_NAMES = [
        "books",
        "ratings",
        "rated_books"
    ]
    TABLE_NAMES_SET = set(TABLES_NAMES)

    def __init__(self) -> None:
        """Initialize DatabaseClient class."""
        self.kaggle_path = None

        self.open_connection()
        self.init_tables()
        self.populate_tables()

    def open_connection(self):
        """Open database connection."""
        self.conn = sqlite3.connect(self.DB_PATH)

    def close_connection(self):
        """Close database connection."""
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
        if table_name not in self.TABLE_NAMES_SET:
            raise ValueError(f"Arg `table_name` must be one of {self.TABLES_NAMES}")

    def init_tables(self):
        for mf in sorted(self.DB_SCRIPTS.glob('m_*.sql')):
            with open(mf, "r") as handle:
                self.conn.executescript(handle.read())
                self.conn.commit()
    
    def populate_tables(self):
        for tn in self.TABLES_NAMES:
            if not self.is_empty(tn):
                continue

            if tn == "rated_books":
                with open(self.DB_SCRIPTS / "s_populate_rated_books.sql", "r") as handle:
                    self.conn.executescript(handle.read()) 
                    self.conn.commit()
                
                continue

            table, self.kaggle_path = preprocess(tn, self.kaggle_path)

            table.to_sql(tn, self.conn, if_exists="replace")
            self.conn.commit()
        
        

    def drop_table(self, table_name: str):
        self.validate_table_name(table_name)    

        self.get_cursor().execute(f"DROP TABLE {table_name}")
        self.conn.commit()
    


x = DatabaseClient()
# x.drop_table('books')
# x.drop_table('ratings')
# x.run_migrations()

# for tn in x.TABLES_NAMES:
#     x.drop_table(tn)