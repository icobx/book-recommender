import logging

import pandas as pd
import starlette.status as status

import src.models as models
from src.config import config, db_config
from src.db_client import DatabaseClient
from src.exceptions import ExcCode, UserFacingException

logger = logging.getLogger(__name__)


class BookRecommender:
    """A simple filtering book recommender system.

    Downloads and preprocesses data from a Kaggle dataset (if not yet available),
    loads it into a local SQLite database, and computes book recommendations
    based on user rating correlations.

    Logic is based on original book_rec.py (currently src/legacy/book_rec_original.py).

    Attributes:
        db: Instance of `DatabaseClient` providing access to SQLite database.
    """

    def __init__(self):
        """Initialize BookRecommender class.

        Creates an instance of `DatabaseClient`.
        """
        logger.info("Initializing DatabaseClient.")
        self.db = DatabaseClient()

    def get_book_titles_by_title(self, title: str) -> list[str]:
        """Retrieve book titles from the database that partially match a given title.

        Args:
            title: Full or partial book title to search for.

        Returns:
            A list of book titles matching the given query (case-insensitive).
        """
        records = (
            self.db.get_cursor()
            .execute(db_config.book_titles_by_title_sql, (title.lower(),))
            .fetchall()
        )

        return [r[0] for r in records]

    def get_book_readers(self, title: str) -> list[str]:
        """Retrieve IDs of users who rated the specified book.

        Args:
            title: The lowercase title of the book.

        Returns:
            A list of user IDs who rated the given book.
        """
        records = (
            self.db.get_cursor()
            .execute(db_config.book_readers_sql, (title,))
            .fetchall()
        )

        return [r[0] for r in records]

    def get_books_by_titles(self, titles: list[str]) -> pd.DataFrame:
        """Retrieve book records for a list of book titles.

        Args:
            titles: List of book titles to retrieve records for.

        Returns:
            A pandas DataFrame containing records for the given books.
        """
        query = db_config.books_by_titles_sql.replace(
            "?", ", ".join(["?"] * len(titles))
        )

        return pd.read_sql_query(query, self.db.conn, params=titles)

    def get_other_books_of_book_readers(self, book_readers: list[str]) -> pd.DataFrame:
        """Retrieve all books rated by a list of users.

        Args:
            book_readers: List of user IDs who rated the selected book.

        Returns:
            A pandas DataFrame containing all ratings given by these users.
        """
        query = db_config.other_books_of_book_readers_sql.replace(
            "?", ", ".join(["?"] * len(book_readers))
        )

        return pd.read_sql_query(query, self.db.conn, params=book_readers)

    def calcualte_correlations(self, book_title: str) -> pd.DataFrame:
        """Compute correlations between the given book and other books.

        Filters out books with too few ratings and computes correlations
        only between the selected book and books rated by the same users.

        Args:
            book_title: Title of the book to base recommendations on.

        Returns:
            Pandas DataFrame containing book titles, average ratings and recommendation scores.

        Raises:
            UserFacingException: If the book is not found in the database or if
                there are insufficient ratings to compute recommendations.
        """
        book_readers = self.get_book_readers((book_title_lc := book_title.lower()))
        if len(book_readers) == 0:
            msg = f"Book {book_title} is not in the database."
            logger.exception(msg)

            raise UserFacingException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                exc_code=ExcCode.BOOK_NOT_FOUND,
                message=msg,
                input=book_title,
            )

        other_books_of_book_readers = self.get_other_books_of_book_readers(book_readers)

        n_ratings_per_book = (
            other_books_of_book_readers.groupby("book_title_lc")["user_id"]
            .count()
            .reset_index()
            .rename(columns={"user_id": "n_ratings"})
        )

        books_to_compare = n_ratings_per_book.loc[
            n_ratings_per_book.n_ratings >= config.min_n_ratings, "book_title_lc"
        ]
        if len(books_to_compare) < 2:
            msg = "Not enough ratings by the relevant reviewers to continue."
            logger.exception(msg)

            raise UserFacingException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                exc_code=ExcCode.NOT_ENOUGH_RATINGS,
                message=msg,
                input=book_title,
            )

        ratings_of_book_readers = other_books_of_book_readers.loc[
            other_books_of_book_readers.book_title_lc.isin(books_to_compare),
            ["user_id", "book_rating", "book_title_lc"],
        ]

        ratings_of_book_readers_nodup = (
            ratings_of_book_readers.groupby(["user_id", "book_title_lc"])["book_rating"]
            .mean()
            .round(2)
            .to_frame()
            .reset_index()
        )

        df_corr = ratings_of_book_readers_nodup.pivot(
            index="user_id", columns="book_title_lc", values="book_rating"
        )

        correlations = []
        for bt in df_corr.columns:
            if bt == book_title_lc:
                continue

            correlation = df_corr[book_title_lc].corr(df_corr[bt])
            if pd.isna(correlation):
                logger.debug("Correlation for book %s is NaN. Skipping.", bt)
                continue

            if correlation < 0:
                logger.debug("Negative correlation for book %s. Skipping.", bt)
                continue

            curr_book_subset = ratings_of_book_readers.loc[
                ratings_of_book_readers.book_title_lc == bt
            ]

            correlations.append(
                {
                    "book_title_lc": bt,
                    "correlation_with_selected_book": round(correlation, 2),
                    "average_rating": round(curr_book_subset.book_rating.mean(), 2),
                }
            )

        return pd.DataFrame(
            sorted(
                correlations,
                key=lambda x: x["correlation_with_selected_book"],
                reverse=True,
            )
        )

    def recommend(self, request: models.RecommendRequestBody) -> dict[str, any]:
        """Generate book recommendations for a given book.

        Retrieve books rated by similar readers and ranks them
        by correlation strength and average rating.

        Args:
            request: Pydantic model containing the target book title (`book_title`)
                and desired number of recommendations (`top_n`).

        Returns:
            A dictionary with the following keys:
                - 'book_title': The original book title from the request.
                - 'top_n': The number of recommendations returned.
                - 'recommended_books': A list of `RecommendResponseRecord` objects
                    representing recommended books and their metadata.
        """
        logger.info("Calculating correlations.")
        corrs = self.calcualte_correlations(book_title=request.book_title)
        top_n = request.top_n if request.top_n > 0 else len(corrs)
        corrs = corrs.head(top_n)

        logger.info("Getting books by titles.")
        books = self.get_books_by_titles(corrs.book_title_lc.values.tolist())

        logger.info("Merging correlations with books.")
        recommended_books = (
            corrs.merge(books, on="book_title_lc")
            .drop(columns=["book_title_lc"])
            .to_dict(orient="records")
        )

        return {
            "book_title": request.book_title,
            "top_n": top_n,
            "recommended_books": [
                models.RecommendResponseRecord(**r) for r in recommended_books
            ],
        }
