import traceback

from fastapi import FastAPI, HTTPException, Query, Request, responses, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from rapidfuzz import process

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

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=responses.HTMLResponse)
def home(request: Request):
    """Returns the HTML homepage of the app.

    Loads and returns the static HTML content from `static/index.html`.

    Returns:
        HTML content of the homepage.
    """
    # with open("static/index.html") as handle:
    #     return handle.read()
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
    try:
        return models.RecommendResponseBody(**request.app.state.book_recommender(request_body))

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "input": request_body.model_dump(),
                "type": str(type(e)),
                "traceback": traceback.format_exc(),
            },
        )


@app.get("/autocomplete", response_model=models.AutocompleteResponseBody)
async def autocomplete(
    request: Request,
    q: str = Query(..., min_length=3, description="Partial book title."),
    limit: int = Query(10, ge=1, le=50, description="Max number of suggestions."),
) -> models.AutocompleteResponseBody:
    """API endpoint to get book titles suggestions based on provided query.

    Args:
        request: FastAPI request object, used to access app state.
        q: Query for suggestions. Defaults to Query(..., min_length=3, description='Partial book title.').
        limit: Number of returned suggestions.
            Defaults to Query(10, ge=1, le=50, description='Max number of suggestions.').

    Returns:
        Dictionary with list of suggestions under `suggestions` key.
    """
    return models.AutocompleteResponseBody(
        suggestions=request.app.state.book_recommender.get_book_titles_by_title(
            q.lower()
        )
    )
