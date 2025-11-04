INSERT INTO rated_books
SELECT 
    r.user_id,
    r.isbn,
    r.book_rating,
    b.book_title_lc
FROM ratings r
JOIN books b ON r.isbn = b.isbn;