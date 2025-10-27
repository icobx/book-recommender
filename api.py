import contextlib

import fastapi

from new import BookRecommender

br_client = {}

async def book_recommender_init_lifespan(app: fastapi.FastAPI):
    br_client['br'] = BookRecommender()

    yield

    br_client['br'].data = None
    br_client.clear()


app = fastapi.FastAPI(
    title='Book Recommender API',
    version='0.0.0',
    # description=...,
    lifespan=book_recommender_init_lifespan,
)

@app.post("/recommend_book/") # , response_model=...)
async def recommend_book(
    # request_body: models.BookRecommenderRequestBody
): #-> models.BookRecommenderResponseBody:
    # try:
    #     response = 
    pass