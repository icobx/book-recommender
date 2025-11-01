from pathlib import Path

import pandas as pd

import src.models as models
from src.utils import clean_text, download_from_kaggle, to_snake_case


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

    KAGGLE_HANDLE = "arashnic/book-recommendation-dataset"
    DATA_PATH = Path("data")
    STRING_COLS = [
        "book_title",
        "book_author",
        "publisher",
        "book_title_lc",
        "book_author_lc",
        "publisher_lc",
    ]
    NON_LC_BOUND = 3
    MIN_N_RATINGS = 8

    def __init__(self):
        """Initialize BookRecommender class.

        Data are downloaded (if they are not already) and loaded here.
        """
        if not (self.DATA_PATH / "merged.csv").exists():
            self.preprocess()

        self.data = pd.read_csv(
            self.DATA_PATH / "merged.csv",
            na_values=["nan"],
            dtype={c: "string" for c in self.STRING_COLS},
        )

    def __call__(self, request: models.RecommendRequestBody) -> dict[str, any]:
        """Returns book recommendations based on a given book title.

        Args:
            request: A request object with the target book title and number of top recommendations to return.

        Returns:
            A dictionary containing the original book title,
            the number of recommendations returned, and a list of recommended books as `RecommendResponseRecord` objects.
        """
        corrs = self.calcualte_correlations(book_title=request.book_title)
        top_n = request.top_n if request.top_n > 0 else len(corrs)

        corrs = corrs[:top_n]

        return {
            "book_title": request.book_title,
            "top_n": top_n,
            "recommended_books": [
                models.RecommendResponseRecord(**r) for r in corrs[:top_n]
            ],
        }

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
        book_readers = self.data.loc[
            self.data.book_title_lc == (book_title_lc := book_title.lower()), "user_id"
        ].unique()

        if len(book_readers) == 0:
            raise ValueError(f"Book {book_title} is not in the database.")

        other_books_of_book_readers = self.data.loc[
            self.data.user_id.isin(book_readers)
        ]

        n_ratings_per_book = (
            other_books_of_book_readers.groupby("book_title_lc")["user_id"]
            .count()
            .reset_index()
            .rename(columns={"user_id": "n_ratings"})
        )

        books_to_compare = n_ratings_per_book.loc[
            n_ratings_per_book.n_ratings >= self.MIN_N_RATINGS, "book_title_lc"
        ]

        if books_to_compare.empty:
            raise ValueError(
                "Not enough ratings by the relevant reviewers to continue."
            )

        ratings_of_book_readers = other_books_of_book_readers.loc[
            other_books_of_book_readers.book_title_lc.isin(books_to_compare),
            ["user_id", "book_rating", "book_title_lc", "book_title"],
        ]

        ratings_of_book_readers_nodup = (
            ratings_of_book_readers.groupby(["user_id", "book_title_lc"])["book_rating"]
            .mean()
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
            curr_book_subset = ratings_of_book_readers.loc[
                ratings_of_book_readers.book_title_lc == bt
            ]

            correlations.append(
                {
                    "book_title": curr_book_subset.book_title.values[0],
                    "correlation_with_selected_book": correlation,
                    "average_rating": curr_book_subset.book_rating.mean(),
                }
            )

        return sorted(
            correlations,
            key=lambda x: x["correlation_with_selected_book"],
            reverse=True,
        )

    def preprocess(self):
        """Downloads and preprocesses the book dataset from Kaggle.

        1. Downloads the dataset if not already present.
        2. Cleans text columns (trims, lowercases, removes noise).
        3. Filters ratings > 0.
        4. Merges books and ratings into a single CSV file (`merged.csv`).
        """
        kaggle_path = download_from_kaggle(self.KAGGLE_HANDLE)

        books = pd.read_csv(
            kaggle_path / "Books.csv", sep=",", on_bad_lines="warn", encoding="cp1251"
        )
        books.columns = map(to_snake_case, books.columns)
        books["year_of_publication"] = (
            pd.to_numeric(books["year_of_publication"], errors="coerce")
            .astype("Int64")
            .replace([0], pd.NA)
        )
        for c in self.STRING_COLS[: self.NON_LC_BOUND]:
            books[c] = books / [c].astype("string").str.strip()
            books[c] = books[c].map(clean_text)
            books[f"{c}_lc"] = books[c].str.lower()

        books.to_csv(self.DATA_PATH / "books.csv", index=False, na_rep="nan")

        ratings = pd.read_csv(kaggle_path / "Ratings.csv", sep=",", on_bad_lines="warn")
        ratings.columns = map(to_snake_case, ratings.columns)
        ratings = ratings.loc[ratings["book_rating"] > 0]
        ratings.to_csv(self.DATA_PATH / "ratings.csv", index=False, na_rep="nan")

        merged = ratings.merge(books, how="inner", on="isbn")
        merged.to_csv(self.DATA_PATH / "merged.csv", index=False, na_rep="nan")
