SELECT
	isbn,
	book_title,
	book_author AS author,
	year_of_publication AS publication_year,
	publisher,
	image_url_s,
    book_title_lc
FROM
    books
WHERE (book_title, [index]) IN (
    SELECT
        DISTINCT book_title,
        MIN([index])
    FROM
        books
    WHERE 
        book_title_lc IN (?) 
    AND
        year_of_publication IS NOT NULL
    GROUP BY
        book_title_lc
)
ORDER BY
    book_title ASC;