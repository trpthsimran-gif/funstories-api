# Fun Stories API

A REST API built with FastAPI serving short, light-hearted original fictional stories across genres like Comedy, Quirky, Silly, Absurd, Twist Ending, and Feel-Good.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (On Windows, if `pip` doesn't work directly, use `py -m pip install -r requirements.txt`. If you get "No module named pip", first run `py -m ensurepip --upgrade`.)

2. Run the server (use a free port - 8000-8004 may already be taken by other projects):
   ```bash
   uvicorn main:app --reload --port 8005
   ```
   (On Windows: `py -m uvicorn main:app --reload --port 8005`)

3. Open your browser:
   - API root: http://127.0.0.1:8005/
   - Interactive Swagger docs: http://127.0.0.1:8005/docs

## Endpoints

| Method | Endpoint                | Description                                         |
|--------|---------------------------|------------------------------------------------------|
| GET    | `/`                        | Welcome message + API guide                          |
| GET    | `/stories`                 | Paginated list of stories (filter by genre)          |
| GET    | `/stories/{id}`            | Get a single story by ID                              |
| GET    | `/stories/random`          | Get one random story                                  |
| GET    | `/stories/search?q=...`    | Search stories by keyword                             |
| GET    | `/genres`                  | List all genres                                       |

## Examples

```
GET /stories
GET /stories?page=1&limit=5
GET /stories?genre=Comedy
GET /stories/random
GET /stories/1
GET /stories/search?q=cat
GET /genres
```

## Project Structure

```
funstories-api/
├── main.py
├── data/
│   └── stories.json    # Seed dataset (30 original fun stories)
├── requirements.txt
└── README.md
```

## Data

Seeded with 30 original short fictional stories across 6 genres: Comedy, Quirky, Silly, Absurd, Twist Ending, and Feel-Good.

## Next steps / ideas to extend

- Add more stories (currently 30)
- Add a `POST /stories` endpoint to submit new stories
- Move to a real database (SQLite) for easier growth
- Deploy online (e.g., Render) for a public URL
