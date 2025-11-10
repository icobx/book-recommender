# Book Recommendation API Service

Project contains the implementation of a simple API that provides book recommendations based on collaborative filtering.

The API exposes a single `POST` endpoint `/recommend`, which returns books similar to the one specified by the user.

The recommendation logic is based on user rating similarity using Pearson correlation, calculated across books that were read by the same users.

The API was created as a job application assignment:  
**Book Recommendation Productionalization Task** as described in the original assignment brief.

---

## Getting started

### Installation

To install required packages, run the following command from the project root directory:

```bash
pip install -r requirements.txt
```

### Running API

To start the local API server, write the following command from the project root directory:

```bash
uvicorn src.main:app --reload
```

The API server will be listening at [http://0.0.0.0:8000](http://0.0.0.0:8000) and the API documentation will be available
at [http://0.0.0.0:8000/docs](http://0.0.0.0:8000/docs).

### Getting response

To interact with the app, you can use frontend application served at `http://128.0.0.1:8000`
or you can make direct requests using an API client like famous [Postman](https://www.postman.com/) or a browser extension:

| Browser        | Extension                                                                                                                                                    |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Firefox        | [RESTED](https://addons.mozilla.org/en-GB/firefox/addon/rested/?utm_source=addons.mozilla.org&utm_medium=referral&utm_content=search)                        |
| Google Chrome  | [Yet Another REST Client](https://chromewebstore.google.com/detail/yet-another-rest-client/ehafadccdcdedbhcbddihehiodgcddpl?hl=en-GB&utm_source=ext_sidebar) |
| Microsoft Edge | [Boomerang - SOAP & REST Client](https://microsoftedge.microsoft.com/addons/detail/boomerang-soap-rest-c/bhmdjpobkcdcompmlhiigoidknlgghfo)                   |

Once in API client:

1. set the request type to `POST`
1. enter Baseline API URL to Baseline API with endpoint `http://0.0.0.0:8000/baseline`
1. add following pair to Headers `Content-Type: application/json`
1. add request body, for example:
   ```json
   {
     "book_title": "1984",
     "top_n": 5
   }
   ```
1. hit the send button.

You should receive **response** like this:

```json
{
  "book_title": "1984",
  "top_n": 2,
  "recommended_books": [
    {
      "book_title": "Animal Farm",
      "correlation_with_selected_book": 0.8218627490477836,
      "average_rating": 8.65
    },
    {
      "book_title": "Slaughterhouse Five or the Children's Crusade: A Duty Dance With Death",
      "correlation_with_selected_book": 0.7233642332556182,
      "average_rating": 8
    }
  ]
}
```

# Project structure

Description of files, directories and their contents.

> Please note: In the root directory there are `Dockerfile` and `.dockerignore` files which usually indicates a possibility
> to run the solution as a docker image, however due to technical issues with my computer I haven't been able to test it.

## data [<sub>[&larrhk;]</sub>](/data)

Directory containing static data.

## database[<sub>[&larrhk;]</sub>](/database)

Directory containing database `books.db` and `scripts` directory.

### scripts

Directory containing sql scripts used in application.

## logs

Directory where logs are persisted.

## src [<sub>[&larrhk;]</sub>](/src)

Directory contains backend logic and `legacy` directory.

### legacy

Directory containing original script used as part of the assignment.

### api.py [<sub>[&larrhk;]</sub>](/src/api.py)

This file contains endpoints definitions. FastAPI `app` object is initialized here.

### book_recommender.py

Class `BookRecommender` which contains main business logic is defined here.

### config.py [<sub>[&larrhk;]</sub>](/src/config.py)

Contains `Config`, `DatabaseConfig`, `LoggingFormatterConfig`, `LoggingLoggerConfig`, `LoggingConfig` dataclasses.

Also instances of `Config` and `DatabaseConfig` are instantiated here.

### db_client.py

The file contains `DatabaseClient` class which holds the logic for manipulating with the database.

### exceptions.py

Contains custom extention of the `fastapi.HTTPException` called `UserFacingException` and enum with status codes `ExcCode`.

### models.py

Contains pydantic-based model classes for request and reponse bodies.

### utils.py

Contains utility functions used throughout the app.

## static

Directory contains .js and .css files associated with the index.html (frontend).

### styles

Directory containing styling sheets.

#### styles.css

Stylsheet for the frontend app.

### config.js

File containing mappings used in frontend.

### script.js

This file contains all of the frontend logic.

## templates

Directory contains frontend HTML templates.

### index.html

File containing frontend structure. It is served by FastAPI.

## tests [<sub>[&larrhk;]</sub>](/src/tests)

Directory contains unit tests. Inner structure of this directory follows the structure of `src` directory.

> Please note: Tests coverage is very small due to lack of time, however I tried to showcase various techniques like
> use of fixtures, mocking, parametrization.

---

## Author

Jakub Fedorko @ <jakub.fedorko@icloud.com>
