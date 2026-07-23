"""
Fun Stories API
A REST API serving short, light-hearted original fictional stories across genres
like Comedy, Quirky, Silly, Absurd, Twist Ending, and Feel-Good.
"""

import json
import random
import re
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Query

WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_HEADERS = {
    "User-Agent": "FunStoriesAPI/1.0 (educational project)"
}


def extract_sentences(full_text: str) -> list:
    """Break a full Wikipedia article's plain text into clean individual sentence-facts."""
    lines = full_text.split("\n")
    paragraph_lines = [line.strip() for line in lines if len(line.strip()) > 40]
    combined = " ".join(paragraph_lines)
    raw_sentences = re.split(r'(?<=[.!?])\s+', combined)
    sentences = [s.strip() for s in raw_sentences if 30 <= len(s.strip()) <= 500]
    return sentences

app = FastAPI(
    title="Fun Stories API",
    description="A REST API serving short, light-hearted original fictional stories across genres like Comedy, Quirky, Silly, Absurd, Twist Ending, and Feel-Good.",
    version="1.0.0"
)

DATA_FILE = Path(__file__).parent / "data" / "stories.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    stories = json.load(f)


@app.get("/", tags=["Root"])
def root():
    """Welcome message and quick guide."""
    return {
        "message": "Welcome to the Fun Stories API",
        "total_stories": len(stories),
        "docs": "/docs",
        "endpoints": [
            "/stories",
            "/stories/{story_id}",
            "/stories/random",
            "/stories/search?q=keyword",
            "/genres"
        ]
    }


@app.get("/stories", tags=["Stories"])
def get_stories(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
    genre: Optional[str] = Query(None, description="Filter by genre e.g. Comedy, Quirky, Silly, Absurd, Twist Ending, Feel-Good")
):
    """Get a paginated list of fun stories, optionally filtered by genre."""
    result = stories

    if genre:
        result = [s for s in result if s["genre"].lower() == genre.lower()]

    total = len(result)
    start = (page - 1) * limit
    end = start + limit
    paginated = result[start:end]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": paginated
    }


@app.get("/stories/random", tags=["Stories"])
def random_story():
    """Get a single random fun story."""
    return random.choice(stories)


@app.get("/stories/search", tags=["Stories"])
def search_stories(q: str = Query(..., min_length=1, description="Keyword to search across title, story text, genre, tags")):
    """Search stories by keyword across title, story text, genre, and tags."""
    query = q.lower()
    result = [
        s for s in stories
        if query in s["title"].lower()
        or query in s["story"].lower()
        or query in s["genre"].lower()
        or any(query in tag.lower() for tag in s["tags"])
    ]
    return {"query": q, "total": len(result), "results": result}


@app.get("/stories/{story_id}", tags=["Stories"])
def get_story(story_id: int):
    """Get a single fun story by its ID."""
    for s in stories:
        if s["id"] == story_id:
            return s
    raise HTTPException(status_code=404, detail=f"Story with id {story_id} not found")


@app.get("/genres", tags=["Metadata"])
def get_genres():
    """List all distinct story genres."""
    genres = sorted(set(s["genre"] for s in stories))
    return {"total": len(genres), "genres": genres}


@app.get("/wiki/search", tags=["Dynamic"])
def wiki_search(
    q: str = Query(..., min_length=1, description="Any topic to look up live on Wikipedia, not limited to your local dataset"),
    page: int = Query(1, ge=1, description="Page number - increase this and hit Execute again to get more facts"),
    limit: int = Query(50, ge=1, le=2000, description="Number of facts to return per page")
):
    """
    Search Wikipedia LIVE and return the FULL article broken into individual sentence-facts.
    Unlike /stories/search (which only searches your local dataset), this endpoint
    calls Wikipedia's API in real time and can return dozens or hundreds of real facts
    about any topic. Increase 'page' and call again to get more facts from the same article.
    """
    search_params = {"action": "query", "list": "search", "srsearch": q, "format": "json", "srlimit": 1}

    try:
        search_resp = requests.get(WIKI_SEARCH_URL, params=search_params, headers=WIKI_HEADERS, timeout=10)
        search_resp.raise_for_status()
        search_data = search_resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not reach Wikipedia: {str(e)}")

    results = search_data.get("query", {}).get("search", [])
    if not results:
        raise HTTPException(status_code=404, detail=f"No Wikipedia results found for '{q}'")

    title = results[0]["title"]

    extract_params = {"action": "query", "prop": "extracts", "explaintext": 1, "titles": title, "format": "json"}

    try:
        extract_resp = requests.get(WIKI_SEARCH_URL, params=extract_params, headers=WIKI_HEADERS, timeout=10)
        extract_resp.raise_for_status()
        extract_data = extract_resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not fetch Wikipedia article: {str(e)}")

    pages = extract_data.get("query", {}).get("pages", {})
    full_text = next(iter(pages.values()), {}).get("extract", "")

    all_facts = extract_sentences(full_text)
    total = len(all_facts)
    start = (page - 1) * limit
    end = start + limit
    paginated_facts = all_facts[start:end]

    if not paginated_facts and page > 1:
        raise HTTPException(status_code=404, detail=f"No more facts available - '{title}' only has {total} facts total")

    return {
        "query": q,
        "title": title,
        "page": page,
        "limit": limit,
        "total_facts_available": total,
        "facts": paginated_facts,
        "wikipedia_url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
        "source": "Wikipedia (live)"
    }


@app.get("/wiki/random", tags=["Dynamic"])
def wiki_random(limit: int = Query(20, ge=1, le=2000, description="Number of facts to return from the random article")):
    """
    Get facts from a RANDOM Wikipedia article - no search term needed.
    Just hit Execute again and you'll get a completely different article and
    different facts each time, since Wikipedia picks a new random page every call.
    """
    random_params = {"action": "query", "list": "random", "rnnamespace": 0, "rnlimit": 1, "format": "json"}

    try:
        random_resp = requests.get(WIKI_SEARCH_URL, params=random_params, headers=WIKI_HEADERS, timeout=10)
        random_resp.raise_for_status()
        random_data = random_resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not reach Wikipedia: {str(e)}")

    random_pages = random_data.get("query", {}).get("random", [])
    if not random_pages:
        raise HTTPException(status_code=503, detail="Wikipedia did not return a random article")

    title = random_pages[0]["title"]

    extract_params = {"action": "query", "prop": "extracts", "explaintext": 1, "titles": title, "format": "json"}

    try:
        extract_resp = requests.get(WIKI_SEARCH_URL, params=extract_params, headers=WIKI_HEADERS, timeout=10)
        extract_resp.raise_for_status()
        extract_data = extract_resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not fetch Wikipedia article: {str(e)}")

    pages = extract_data.get("query", {}).get("pages", {})
    full_text = next(iter(pages.values()), {}).get("extract", "")

    all_facts = extract_sentences(full_text)

    return {
        "title": title,
        "total_facts_available": len(all_facts),
        "facts": all_facts[:limit],
        "wikipedia_url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
        "source": "Wikipedia (live, random article)"
    }
