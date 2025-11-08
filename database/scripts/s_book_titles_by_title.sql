SELECT DISTINCT book_title
FROM books
WHERE book_title_lc LIKE '%' || ? || '%';