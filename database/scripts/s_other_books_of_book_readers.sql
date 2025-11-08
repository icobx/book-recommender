SELECT * FROM rated_books
WHERE user_id IN (?)
order by book_title_lc asc;