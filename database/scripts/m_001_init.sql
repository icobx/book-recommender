CREATE TABLE IF NOT EXISTS books (
  isbn TEXT PRIMARY KEY,
  book_title TEXT,
  book_author TEXT,
  year_of_publication INTEGER,
  publisher TEXT,
  image_url_s TEXT,
  image_url_m TEXT,
  image_url_l TEXT,
  book_title_lc TEXT
);

CREATE TABLE IF NOT EXISTS ratings (
  user_id TEXT,
  isbn TEXT,
  book_rating INTEGER,
  PRIMARY KEY (user_id, isbn)
);

CREATE TABLE IF NOT EXISTS rated_books (
  user_id TEXT,
  isbn TEXT,
  book_rating INTEGER,
  book_title_lc TEXT,
  PRIMARY KEY (user_id, isbn)
);