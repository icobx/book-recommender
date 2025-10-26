import os
import re
import html
import shutil
import numpy as np
import pandas as pd

import ftfy
import kagglehub

from pathlib import Path
# Download latest version

KAGGLE_HANDLE = "arashnic/book-recommendation-dataset"
DATA_PATH = Path("data")
STRING_COLS = ["book_title", "book_author", "publisher"]
MIN_N_RATINGS = 8


def to_snake_case(text: str) -> str:
    """Convert a string to snake_case."""
    text = re.sub(r"[\-\s]+", "_", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    return text.lower()


#
all_string_cols = [f"{c}_lc" for c in STRING_COLS] + STRING_COLS
df = pd.read_csv(
    "data/merged.csv", na_values=["nan"], dtype={c: "string" for c in all_string_cols}
)
#


# # print(df.head())
# # x = df.loc[(df.book_author_lc.notna()) & (df.book_author_lc.str.contains("tolkien"))]
# # print(x)
# x = df.loc[df.book_author_lc.isna(), "book_author_lc"].values[0]
# df.book_author_lc = df.book_author_lc.astype("string")
# print(df.loc[df.book_author_lc.str.contains("tolkien")])
full_name = "The Fellowship of the Ring (The Lord of the Rings, Part 1)"
# full_name = "Mr Phillips"
# # print(df.iloc[6578]["book_title"])
full_name_lc = full_name.lower()
book_readers = df.loc[df.book_title_lc == full_name_lc, "user_id"].unique()
# print(book_readers)

other_books_of_book_readers = df.loc[df.user_id.isin(book_readers)]
# print(other_books_of_book_readers)

n_ratings_per_book = (
    other_books_of_book_readers.groupby("book_title_lc")["user_id"]
    .count()
    .reset_index()
    .rename(columns={"user_id": "n_ratings"})
)
# print(n_ratings_per_book)

books_to_compare = n_ratings_per_book.loc[
    n_ratings_per_book.n_ratings >= MIN_N_RATINGS, "book_title_lc"
]

if books_to_compare.empty:
    print("df empty; exiting...")
    exit()

# print(books_to_compare)

ratings_of_book_readers = other_books_of_book_readers.loc[
    other_books_of_book_readers.book_title_lc.isin(books_to_compare),
    ["user_id", "book_rating", "book_title_lc"],
]

# print(ratings_of_book_readers)

ratings_of_book_readers_nodup = (
    ratings_of_book_readers.groupby(["user_id", "book_title_lc"])["book_rating"]
    .mean()
    .to_frame()
    .reset_index()
)

# print(ratings_of_book_readers_nodup)

df_corr = ratings_of_book_readers_nodup.pivot(
    index="user_id", columns="book_title_lc", values="book_rating"
)

# print(df_corr)
correlations = []
for book_title in df_corr.columns:
    if book_title == full_name_lc:
        continue

    curr_corr = df_corr[full_name_lc].corr(df_corr[book_title])
    mean_rating = ratings_of_book_readers.loc[
        ratings_of_book_readers.book_title_lc == book_title, "book_rating"
    ].mean()
    # print(curr_corr)
    correlations.append((book_title, curr_corr, mean_rating))

correlations = sorted(correlations, reverse=True, key=lambda x: x[1])
print(correlations[:10])
# print(books_to_compare)
# y = df.loc[df.book_author_lc.isna(), "book_author_lc"].values[0]
# print(x, type(x), y, type(y))
# path = kagglehub.dataset_download("arashnic/book-recommendation-dataset")

# # print("Path to dataset files:", path)
# # for f in [p for p in Path(path).glob("*.csv") if "Users" not in p.name]:
# #     shutil.copy(f, Path("data") / f.name.lower())

# books = pd.read_csv(
#     Path(path) / "Books.csv",
#     sep=",",
#     on_bad_lines="warn",  # , dtype={"Year-Of-Publication": int}
#     # encoding="cp1252",
#     low_memory=False,
# )
# print(books.dtypes)

# mixed_cols = []
# for col in books.columns:
#     types = books[col].map(type).unique()
#     if len(types) > 1:
#         mixed_cols.append((col, types))
# print(mixed_cols)
# # print(books["Year-Of-Publication"].astype("string").str.replace)
#
# # books['']
# books.columns = map(to_snake_case, books.columns)
# print(books.columns)
# print(books)
# print([(x, type(x)) for x in books.book_rating if isinstance(x, int)])


# books["year_of_publication"] = (
#     pd.to_numeric(books["year_of_publication"], errors="coerce")
#     .astype("Int64")
#     .replace([0], pd.NA)
# )
# print(books[["book_title", "year_of_publication"]])
# print(books["year_of_publication"].unique().tolist())
# print(books.loc[books.publisher.str.len() == 0])
#
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    return html.unescape(ftfy.fix_text(text))


# books["publisher"] = books["publisher"].map(clean_text)
# print(books.publisher.unique().tolist())
# print([(c, type(c)) for c in books.book_author.values if not isinstance(c, str)])


def download() -> None:
    return Path(kagglehub.dataset_download(KAGGLE_HANDLE))
    # for f in [p for p in Path(kaggle_dl_path).glob("*.csv") if "Users" not in p.name]:
    # shutil.copy(f, DATA_PATH / f.name.lower())


# download()
def preprocess(save_path: str | Path = "./data"):
    kaggle_path = download()

    books = pd.read_csv(
        kaggle_path / "Books.csv", sep=",", on_bad_lines="warn", encoding="cp1251"
    )
    books.columns = map(to_snake_case, books.columns)
    books["year_of_publication"] = (
        pd.to_numeric(books["year_of_publication"], errors="coerce")
        .astype("Int64")
        .replace([0], pd.NA)
    )
    for c in STRING_COLS:
        books[c] = books[c].astype("string").str.strip()
        books[c] = books[c].map(clean_text)
        books[f"{c}_lc"] = books[c].str.lower()

    save_path = Path(save_path) if not isinstance(save_path, Path) else save_path
    books.to_csv(save_path / "books.csv", index=False, na_rep="nan")

    ratings = pd.read_csv(kaggle_path / "Ratings.csv", sep=",", on_bad_lines="warn")
    ratings.columns = map(to_snake_case, ratings.columns)
    ratings = ratings.loc[ratings["book_rating"] > 0]
    ratings.to_csv(save_path / "ratings.csv", index=False, na_rep="nan")

    merged = ratings.merge(books, how="inner", on="isbn")
    merged.to_csv(save_path / "merged.csv", index=False, na_rep="nan")


# preprocess()


# def fin
# def load() -> tuple[pd.DataFrame, pd.DataFrame]:
#     ratings = pd.read_csv(DATA_PATH / "ratings.csv", sep=",", on_bad_lines="warn")
#     ratings.columns = [c.lower() for c in ratings.columns]
#     ratings = ratings.loc[ratings["book-rating"] > 0]

#     books = pd.read_csv(DATA_PATH / "books.csv", sep=",", on_bad_lines="warn")

#     return ratings, books


# def process(ratings: pd.DataFrame, books: pd.DataFrame):
#
# with open("data/BX-Books.csv", mode="r", encoding="cp1251") as handle:
#     # print(handle.readline())
#     for i, l in enumerate(handle.readlines()):
#         if i == 43666:
#             print(l)
#             x = l.split('";"')
#             print(x)
#             print(len(x))

# x = pd.read_csv(
#     "data/BX-Books.csv",
#     encoding="cp1251",
#     sep='";"',
#     on_bad_lines="warn",
#     engine="python",
# )
# print(x)
# # y = pd.read_csv("data/BX-Books.csv", encoding="cp1251", sep=";", on_bad_lines="warn")
# # print(y)
# # f = x.columns[0].strip('"')
# x.columns = [c.strip('"') for c in x.columns]
# print(x)
# for c in ["ISBN", "Image-URL-L"]:
#     x[c] = x[c].str.strip('"')
# print(x)
