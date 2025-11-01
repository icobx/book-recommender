import traceback

from fastapi import FastAPI, HTTPException, Request, responses, staticfiles
from fastapi.middleware.cors import CORSMiddleware

import src.models as models
from src.book_recommender import BookRecommender


async def book_recommender_init_lifespan(app: FastAPI):
    """FastAPI lifespan context manager for initializing the BookRecommender.

    This function sets up the `BookRecommender` instance and attaches it
    to the application's state during startup. On shutdown, it clears the
    in-memory dataset.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Allows FastAPI to proceed with its startup lifecycle.
    """
    app.state.book_recommender = BookRecommender()

    yield

    app.state.book_recommender.data = None


app = FastAPI(
    title="Book Recommender API",
    version="0.0.0",
    # description=...,
    lifespan=book_recommender_init_lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")


@app.get("/", response_class=responses.HTMLResponse)
def home():
    """Returns the HTML homepage of the app.

    Loads and returns the static HTML content from `static/index.html`.

    Returns:
        HTML content of the homepage.
    """
    with open("static/index.html") as handle:
        return handle.read()


@app.post("/recommend", response_model=models.RecommendResponseBody)
async def recommend(
    request: Request, request_body: models.RecommendRequestBody
) -> models.RecommendResponseBody:
    """API endpoint to get book recommendations.

    Uses the initialized `BookRecommender` to generate recommendations
    based on the given input book title and number of recommendations.

    Args:
        request: FastAPI request object, used to access app state.
        request_body: The request payload
            containing `book_title` and `top_n`.

    Returns:
        Recommendation results.

    Raises:
        HTTPException: If an error occurs during recommendation computation.
    """
    try:
        return request.app.state.book_recommender(request_body)

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "input": request_body.model_dump(),
                "type": str(type(e)),
                "traceback": traceback.format_exc()
            },
        )


@app.get("/search_titles")
def search_titles(request: Request):
    data = request.app.state.book_recommender.data
    # return data[data["book_title"].str.contains(q, case=False)]["book_title"].unique().tolist()
    # return data.loc[data.book_title.str.contains(q, case=False), 'book_title'].unique().tolist()
    return data.book_title.unique().tolist()
