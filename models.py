import pydantic
import typing_extensions as te

class RecommendRequestBody(pydantic.BaseModel):
    book_title: str
    top_n: int

    @pydantic.field_validator('top_n', mode='after')
    def check_non_neg_top_n(top_n) -> int:
        if top_n < 0:
            raise ValueError('Parameter `top_n` must be non-negative.')
    
        return top_n
    

class RecommendResponseRecord(pydantic.BaseModel):
    book_title: str
    correlation_with_selected_book: float
    average_rating: float

class RecommendResponseBody(pydantic.BaseModel):
    book_title: str
    top_n: int
    recommended_books: te.List[RecommendResponseRecord]