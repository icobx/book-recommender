import logging
import pandas as pd
import starlette.status as status

import src.models as models
from src.config import config, db_config
from src.db_client import DatabaseClient
from src.exceptions import UserFacingException, ExcCode

logger = logging.getLogger(__name__)


class BookRecommender:
    """A simple collaborative filtering book recommender system.

    Downloads and preprocesses data from a Kaggle dataset (if needed),
    loads it into memory, and computes recommendations based on user
    rating correlations.

    Logic is based on original book_rec.py (currently book_rec_original.py).

    Attributes:
        KAGGLE_HANDLE: String identifier of Kaggle dataset.
        DATA_PATH: Path to the `data` directory.
        STRING_COLS: List of columns of type string.
        NON_LC_BOUND: Index separating non-lowercased and lowercased columns in `STRING_COLS` attribute.
        MIN_N_RATINGS: Minimal number of ratings required for system to be able to recommend books.

        data: Pandas DataFrame containing information about books and their ratings.
    """

    def __init__(self):
        """Initialize BookRecommender class.

        Data are downloaded (if they are not already) and loaded here.
        """
        logger.info("Initializing DatabaseClient.")
        self.db = DatabaseClient()


    def get_book_titles_by_title(self, title: str) -> list[str]:
        records = (
            self.db.get_cursor()
            .execute(db_config.book_titles_by_title_sql, (title.lower(),))
            .fetchall()
        )

        return [r[0] for r in records]

    def get_book_readers(self, title: str) -> list[str]:
        records = (
            self.db.get_cursor()
            .execute(db_config.book_readers_sql, (title,))
            .fetchall()
        )

        return [r[0] for r in records]

    def get_books_by_titles(self, titles: list[str]) -> pd.DataFrame:
        query = db_config.books_by_titles_sql.replace(
            "?", ", ".join(["?"] * len(titles))
        )

        return pd.read_sql_query(query, self.db.conn, params=titles)

    def get_other_books_of_book_readers(self, book_readers: list[str]) -> pd.DataFrame:
        query = db_config.other_books_of_book_readers_sql.replace(
            "?", ", ".join(["?"] * len(book_readers))
        )

        return pd.read_sql_query(query, self.db.conn, params=book_readers)

    def calcualte_correlations(self, book_title: str) -> list[dict[str, str | float]]:
        """Computes Pearson correlations between the given book and other books.

        Filters out books with too few ratings and computes correlations
        only between the selected book and books rated by the same users.

        Args:
            book_title: Title of the book to base recommendations on.

        Returns:
            A list of dictionaries, each containing:
                - 'book_title': Title of a recommended book,
                - 'correlation_with_selected_book': Pearson correlation value,
                - 'average_rating': Average rating by shared users.

        Raises:
            ValueError: If the book is not found in the dataset or
                if there are not enough ratings to compute recommendations.
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
        """Returns book recommendations based on a given book title.

        Args:
            request: A request object with the target book title and number of top recommendations to return.

        Returns:
            A dictionary containing the original book title,
            the number of recommendations returned, and a list of recommended books as `RecommendResponseRecord` objects.
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
            .drop(columns=["book_title_lc"])#[config.ordered_output_cols]
            .to_dict(orient="records")
        )

        return {
            "book_title": request.book_title,
            "top_n": top_n,
            "recommended_books": [
                models.RecommendResponseRecord(**r) for r in recommended_books
            ],
        }
