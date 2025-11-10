import pydantic
import typing_extensions as te


class RecommendRequestBody(pydantic.BaseModel):
    """Request schema for book recommendation queries.

    Attributes:
        book_title: Title of the book to base the recommendations on.
        top_n: Number of top recommendations to return.
    """

    book_title: str
    top_n: int

    @pydantic.field_validator("book_title", mode="before")
    def force_cast_str(book_title: any) -> str:
        """Force cast provided book_title to string.

        Will fail if provided book_title is not able to be cast to string.

        Args:
            book_title: Book title to be cast to string.

        Returns:
            Book title as string.
        """
        return str(book_title)

    @pydantic.field_validator("top_n", mode="after")
    def check_non_neg_top_n(top_n: int) -> int:
        """Validate that `top_n` is non-negative.

        Args:
            top_n: Number of recommendations requested.

        Returns:
            The same value if validation passes.

        Raises:
            ValueError: If `top_n` is negative.
        """
        if top_n < 0:
            raise ValueError("Parameter `top_n` must be non-negative.")

        return top_n


class RecommendResponseRecord(pydantic.BaseModel):
    """Single book recommendation entry.

    Attributes:
        book_title: Title of the recommended book.
        correlation_with_selected_book: Correlation score with the input book.
        average_rating: Average user rating of the recommended book.
    """

    image_url_s: str
    isbn: str
    book_title: str
    author: str
    publication_year: int
    publisher: str
    average_rating: float
    correlation_with_selected_book: float


class RecommendResponseBody(pydantic.BaseModel):
    """Response schema containing book recommendations.

    Attributes:
        book_title: Title of the input book.
        top_n: Number of recommendations returned.
        recommended_books: List of recommended books with scores and metadata.
    """

    book_title: str
    top_n: int
    recommended_books: te.List[RecommendResponseRecord]


class AutocompleteResponseBody(pydantic.BaseModel):
    """Autocomplete schema.

    Attributes:
        suggestions: List of book titles as suggestions.
    """

    suggestions: list[str]
