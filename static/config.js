export const REC_BOOKS_COL_MAPPING = Object.freeze({
  image_url_s: "Cover",
  isbn: "ISBN",
  book_title: "Title",
  author: "Author",
  publisher: "Publisher",
  publication_year: "Published",
  average_rating: "Average Rating",
  correlation_with_selected_book: "Recommendation Score",
});

/**
 * Defines user-facing error messages and their visibility.
 * Each error code maps to a message and flag indicating if it should be shown to the user.
 * @readonly
 * @type {Object<string, {msg: string}>}
 */
export const ERROR_MESSAGES = Object.freeze({
  BOOK_NOT_FOUND: {
    msg: "The book you entered was not found in our database.",
  },
  NOT_ENOUGH_RATINGS: {
    msg: "There are not enough ratings by relevant users to calculate Recommendation Score.",
  },
});
