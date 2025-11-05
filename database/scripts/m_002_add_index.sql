CREATE INDEX IF NOT EXISTS idx_books_book_title_lc
ON books(book_title_lc);

CREATE INDEX IF NOT EXISTS idx_rated_books_book_title_lc
ON rated_books(book_title_lc);