import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request, responses, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

import src.models as models
import src.utils as utils
from src.book_recommender import BookRecommender


@asynccontextmanager
async def book_recommender_init_lifespan(app: FastAPI):
    """FastAPI lifespan context manager for initializing the BookRecommender.

    This function sets up the `BookRecommender` instance and attaches it
    to the application's state during startup. On shutdown, it closes connection
    to the database.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Allows FastAPI to proceed with its startup lifecycle.
    """
    utils.setup_logging()
    app.state.book_recommender = BookRecommender()

    yield

    app.state.book_recommender.db.close_connection()


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

templates = Jinja2Templates(directory="templates")

logger = logging.getLogger(__name__)


@app.get("/", response_class=responses.HTMLResponse)
def home(request: Request):
    """Returns the HTML homepage of the app.

    Loads and returns the static HTML content from `static/index.html`.

    Returns:
        HTML content of the homepage.
    """
    return templates.TemplateResponse("index.html", {"request": request})


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
    logger.info("Responding to recommend request.")
    return models.RecommendResponseBody(
        **request.app.state.book_recommender.recommend(request_body)
    )


@app.get("/autocomplete", response_model=models.AutocompleteResponseBody)
async def autocomplete(
    request: Request,
    q: str = Query(..., min_length=3, description="Partial book title."),
) -> models.AutocompleteResponseBody:
    """API endpoint to get book titles suggestions based on provided query.

    Args:
        request: FastAPI request object, used to access app state.
        q: Query for suggestions. Defaults to Query(..., min_length=3, description='Partial book title.').

    Returns:
        AutocompleteResponseBody object with list of suggestions under `suggestions` key.
    """
    logger.info("Responding to autocomplete request.")
    return models.AutocompleteResponseBody(
        suggestions=request.app.state.book_recommender.get_book_titles_by_title(
            q.lower()
        )
    )
