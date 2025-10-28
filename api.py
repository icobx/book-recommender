import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi import responses, staticfiles
from fastapi.middleware.cors import CORSMiddleware

from book_recommender import BookRecommender
import models

async def book_recommender_init_lifespan(app: FastAPI):
    app.state.book_recommender = BookRecommender()

    yield

    app.state.book_recommender.data = None


app = FastAPI(
    title='Book Recommender API',
    version='0.0.0',
    # description=...,
    lifespan=book_recommender_init_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # Or set specific origins like ["http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],  # Allows Content-Type, Authorization, etc.
)

app.mount("/static", staticfiles.StaticFiles(directory='static'), name='static')

@app.get('/', response_class=responses.HTMLResponse)
def home():
    with open('static/index.html') as handle:
        return handle.read()

@app.post("/recommend", response_model=models.RecommendResponseBody)
async def recommend(
    request: Request,
    request_body: models.RecommendRequestBody
) -> models.RecommendResponseBody:
    # recommender = 
    try:
        return request.app.state.book_recommender(request_body)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "type": str(type(e)),
                "msg": str(e),
                "input": request_body.model_dump(),
                # "traceback": traceback.format_exc()
            },
        )


@app.get("/search_titles")
def search_titles(request: Request):
    data = request.app.state.book_recommender.data
    # return data[data["book_title"].str.contains(q, case=False)]["book_title"].unique().tolist()
    # return data.loc[data.book_title.str.contains(q, case=False), 'book_title'].unique().tolist()
    return data.book_title.unique().tolist()