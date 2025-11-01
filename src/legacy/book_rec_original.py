# import
import numpy as np
import pandas as pd

# load ratings
ratings = pd.read_csv("data/old/BX-Book-Ratings.csv", encoding="cp1251", sep=";")

# exit()
ratings = ratings[ratings["Book-Rating"] != 0]

# load books
books = pd.read_csv(
    "data/old/BX-Books.csv", encoding="cp1251", sep=";", on_bad_lines="warn"
)
# x = books.groupby(["ISBN", "Book-Title"]).count()
# print(x["Book-Author"].unique())
# exit()
# print(len(books["ISBN"]), len(books["ISBN"].unique()))
# exit()
# users_ratigs = pd.merge(ratings, users, on=['User-ID'])
dataset = pd.merge(ratings, books, on=["ISBN"])
dataset_lowercase = dataset.apply(
    lambda x: x.str.lower() if (x.dtype == "object") else x
)
# print(dataset.loc[dataset["User-ID"] == 254, ["User-ID", "Book-Title", "Book-Rating"]])

tolkien_readers = dataset_lowercase["User-ID"][
    (
        dataset_lowercase["Book-Title"]
        == "the fellowship of the ring (the lord of the rings, part 1)"
    )
    & (dataset_lowercase["Book-Author"].str.contains("tolkien"))
]
x = dataset_lowercase.loc[
    dataset_lowercase["Book-Title"]
    == "the fellowship of the ring (the lord of the rings, part 1)"
]
# print(x)
y = x.loc[x["Book-Author"].str.contains("tolkien")]
# print(y[["ISBN", "Book-Rating", "Book-Author"]])
# print(tolkien_readers)
# exit()
tolkien_readers2 = tolkien_readers.unique()
tolkien_readers = tolkien_readers.tolist()
tolkien_readers = np.unique(tolkien_readers)

# print(sorted(tolkien_readers) == )
# print(sorted(tolkien_readers2))
# exit()
# final dataset
books_of_tolkien_readers = dataset_lowercase[
    (dataset_lowercase["User-ID"].isin(tolkien_readers))
]

# Number of ratings per other books in dataset
number_of_rating_per_book = (
    books_of_tolkien_readers.groupby(["Book-Title"]).agg("count").reset_index()
)
# print(number_of_rating_per_book["User-ID"].unique())
# exit()

# select only books which have actually higher number of ratings than threshold
books_to_compare = number_of_rating_per_book["Book-Title"][
    number_of_rating_per_book["User-ID"] >= 8
]
books_to_compare = books_to_compare.tolist()

ratings_data_raw = books_of_tolkien_readers[["User-ID", "Book-Rating", "Book-Title"]][
    books_of_tolkien_readers["Book-Title"].isin(books_to_compare)
]
# print(ratings_data_raw)
# group by User and Book and compute mean
ratings_data_raw_nodup = ratings_data_raw.groupby(["User-ID", "Book-Title"])[
    "Book-Rating"
].mean()
# print(ratings_data_raw_nodup)

# reset index to see User-ID in every row
ratings_data_raw_nodup = ratings_data_raw_nodup.to_frame().reset_index()

# print(ratings_data_raw_nodup)
dataset_for_corr = ratings_data_raw_nodup.pivot(
    index="User-ID", columns="Book-Title", values="Book-Rating"
)
# print(dataset_for_corr)
# exit()
LoR_list = ["the fellowship of the ring (the lord of the rings, part 1)"]

result_list = []
worst_list = []

# for each of the trilogy book compute:
for LoR_book in LoR_list:
    # Take out the Lord of the Rings selected book from correlation dataframe
    dataset_of_other_books = dataset_for_corr.copy(deep=False)
    # print(dataset_of_other_books)
    dataset_of_other_books.drop([LoR_book], axis=1, inplace=True)
    # print(dataset_of_other_books)

    # empty lists
    book_titles = []
    correlations = []
    avgrating = []
    # print(dataset_for_corr[LoR_book])
    # corr computation
    for book_title in list(dataset_of_other_books.columns.values):
        # print(dataset_of_other_books[book_title])
        book_titles.append(book_title)
        # print(dataset_for_corr[LoR_book].corr(dataset_of_other_books[book_title]))
        correlations.append(
            dataset_for_corr[LoR_book].corr(dataset_of_other_books[book_title])
        )
        # print(ratings_data_raw[ratings_data_raw["Book-Title"] == book_title])
        # NOTE: broken
        # tab = (
        #     ratings_data_raw[ratings_data_raw["Book-Title"] == book_title]
        #     .groupby(ratings_data_raw["Book-Title"])
        #     .mean()
        # )
        tab = ratings_data_raw.loc[
            ratings_data_raw["Book-Title"] == book_title, "Book-Rating"
        ].mean()
        # print("tab")
        # print(tab)
        # avgrating.append(tab["Book-Rating"].min())
        avgrating.append(tab)
    # final dataframe of all correlation of each book
    corr_fellowship = pd.DataFrame(
        list(zip(book_titles, correlations, avgrating)),
        columns=["book", "corr", "avg_rating"],
    )
    # print(corr_fellowship)
    corr_fellowship.head()

    # top 10 books with highest corr
    result_list.append(corr_fellowship.sort_values("corr", ascending=False).head(10))

    # worst 10 books
    worst_list.append(corr_fellowship.sort_values("corr", ascending=False).tail(10))

print("Correlation for book:", LoR_list[0])
# print("Average rating of LOR:", ratings_data_raw[ratings_data_raw['Book-Title']=='the fellowship of the ring (the lord of the rings, part 1'].groupby(ratings_data_raw['Book-Title']).mean()))
rslt = result_list[0]
print(rslt)
