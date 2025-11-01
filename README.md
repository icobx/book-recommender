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

To get response you will need an API client like famous [Postman](https://www.postman.com/) or a browser extension:

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

Directory should contain data files.

### 2023-holidays.csv [<sub>[&larrhk;]</sub>](/data/2023-holidays.csv)

File containing USA holidays for year 2023. Converted from `2023-list-of-holidays.pdf`.  
Used to populate `holidays_table` database table.

Example:
| date | holiday |
|----------|----------------|
| 2023-1-1 | New Year's Day |

### energy.csv [<sub>[&larrhk;]</sub>](/data/energy.csv)

Main data file. It contains energy consumption of buildings as time series.
Used to populate `energy_table` database table.

Example:
| building_id | timezone | timestamp | cumulative_energy_kwh |
|-------------|------------------|------------------------|-----------------------|
| Building E | America/New_York | 2023-04-26 11:00:00+00 | 5685135838.296798 |

### events.csv [<sub>[&larrhk;]</sub>](/data/events.csv)

File which holds information about issuer, program name, interval and timezone of past
events. This information is important for CBL window calculation. Details can be found in
`customer-baseline-load-procedure.pdf`, chapter **5.1.1**.

Used to populate `events_table` database table.

Example:
| ISO | utility_id | program_name | event_start | event_end | timezone |
|-------|------------|--------------|---------------------------|---------------------------|------------------|
| NYISO | ConEd | SCR | 2023-02-22 16:00:00-05:00 | 2023-02-22 17:00:00-05:00 | America/New_York |

> Please note: Files are purposely ignored by git.

### results_examples [<sub>[&larrhk;]</sub>](/data/results_examples/)

This directory holds three different examples of requests to and responses form the baseline endpoint.

#### example_a [<sub>[&larrhk;]</sub>](/data/results_examples/example_a)

Request done for weekend day. Granularity is 5 min.

#### example_b [<sub>[&larrhk;]</sub>](/data/results_examples/example_b)

Request with start and end timestamps being two different dates (end is at midnight). Granularity is 1 hour.

#### example_e [<sub>[&larrhk;]</sub>](/data/results_examples/example_e)

Request with start being midnight. Granularity is 15min.

## doc [<sub>[&larrhk;]</sub>](/doc)

Directory contains provided pdf documents:

- `2023-list-of-holidays.pdf`
- `customer-baseline-load-procedure.pdf`
  - Contains CBL calculation methodology.
- `DS-DEV Assignment 2024.pdf`
  - Contains instructions for this assignment.

## sqlite [<sub>[&larrhk;]</sub>](/sqlite)

Once the API is started, [SQLite](https://www.sqlite.org/index.html) database file `baseline.db` will be created here.

## src [<sub>[&larrhk;]</sub>](/src)

Directory holds all of the source code for this project. It contains `baseline`[<sub>[&larrhk;]</sub>](src/baseline/), `database`[<sub>[&larrhk;]</sub>](src/database/), `experiments`[<sub>[&larrhk;]</sub>](src/experiments/) and `models`[<sub>[&larrhk;]</sub>](src/models/)
directories described below, and following files:

### api.py [<sub>[&larrhk;]</sub>](/src/api.py)

It is an entry point of the application, FastAPI `app` object is initialized here.

It contains definitions of

- `baseline_client_init_lifespan`, which is a function that takes care of initialization and teardown of `BaselineClient`
  class before API startup and after it's shutdown, and
- `baseline` function which defines `/baseline/` API endpoint and handles
  any potential exceptions.

### config.py [<sub>[&larrhk;]</sub>](/src/config.py)

Contains `Config` dataclass, which holds generic application parameters, as member attributes.

### baseline [<sub>[&larrhk;]</sub>](/src/baseline/)

Directory containing all of the CBL calculation logic in two files:

#### baseline_client.py [<sub>[&larrhk;]</sub>](/src/baseline/baseline_client.py)

Contains `BaselineClient` class definition. This class contains core of the baseline calculation logic.

Class is initialized via `baseline_client_init_lifespan` function during API startup. During initialization a
`DatabaseClient` is initialized, which creates connection to database and sets it up if needed. Tables `events_table`
and `holiday_table`, being small, are loaded and store as member attributes of this class.

Class then waits till its `calculate_baseline` method is called by `baseline` endpoint, which triggers the CBL calculation.
At this point, relevant subset of `energy_table` is loaded from the database and based on request start timestamp being
a weekday or weekend, respective `calculate_baseline_weekday/weekend` function is called. Specific code snippets in
these functions are divided by the comments referencing sections in `customer-baseline-load-procedure.pdf`.

#### utils.py [<sub>[&larrhk;]</sub>](/src/baseline/utils.py)

Contains utility funtions used by `BaselineClient`.

### database [<sub>[&larrhk;]</sub>](/src/database/)

Directory containing all of the database manipulation logic.

#### database_client.py [<sub>[&larrhk;]</sub>](/src/database/database_client.py)

Contains `DatabaseClient` class definition. This class contains core of the database manipulation logic.

Class is initilized by `BaselineClient` during API startup. Initialization opens connection to the database at
`DatbaseConfig.db_path`. If the database at this location does not exist yet, it will be created. Once the connection
is established, tables are created, if they don't exist yet, and populated if they are empty.

Class loads tables when `load_table` method is called by `BaselineClient` object.

During the API teardown in `baseline_client_init_lifespan`, the connection is closed by `BaselineClient` object before
it itself is cleared.

#### database_config.py [<sub>[&larrhk;]</sub>](/src/database/database_config.py)

Contains `DatabaseConfig` dataclass, which holds database-related application parameters, as member attributes.

#### utils.py [<sub>[&larrhk;]</sub>](/src/database/utils.py)

Contains utility funtions used by `DatabaseClient`.

### experiments [<sub>[&larrhk;]</sub>](/src/experiments)

Directory contains code developed during experimentation phase. File `cbl_experiment.ipynb`[<sub>[&larrhk;]</sub>](/src/experiments/cbl_experiment.ipynb) was used as a playground
notebook for testing various data transformations. File `api_experiment.py`[<sub>[&larrhk;]</sub>](/src/experiments/api_experiment.py) was used during API development.

### models [<sub>[&larrhk;]</sub>](/src/models)

Directory containing [Pydantic](https://docs.pydantic.dev/latest/) models and validators.

#### models.py [<sub>[&larrhk;]</sub>](/src/models/models.py)

File contains definitions of following models:

- `BaselineRequestBody`

  - Represents user request body. It validates it's inputs implicitly, via standard and custom validators described below,
    and explicitly via model validator `check_valid_interval`, which validates whether interval enclosed by user-provided
    `start` and `end` is reasonable. Namely, whether `start` is less than `end`, whether their delta is not longer than
    one day and whether the interval does not cross midnight.
  - Also serializes `start` and `end` as ISO8601-formatted string.

- `BaselineResponseRecord`

  - Represents one record in results (`BaselineResponseBody.records`).

- `BaselineResponseBody`
  - Represents baseline endpoint response body

Also custom validated types are initialized here.

#### validators.py [<sub>[&larrhk;]</sub>](/src/models/validators.py)

File contains custom `Pydantic.AfterValidator`s and functions they are based on. They validate format of timezone being
`Pytz`, format of timestamp being ISO8601 and having timezone information and granularity being one of three permitted
`(5min, 15min, 1hour)`. Timestamp is also converted to `pandas.Timestamp` and `1hour` granularity to `1h`.

These validators are implicitly called by `BaselineRequestBody`.

## tests [<sub>[&larrhk;]</sub>](/src/tests)

Directory contains unit tests. Inner structure of this directory follows the structure of `src` directory.

> Please note: Tests coverage is very small due to lack of time, however I tried to showcase various techniques like
> use of fixtures, mocking, parametrization.

---

## Author

Jakub Fedorko @ <jakub.fedorko@icloud.com>
