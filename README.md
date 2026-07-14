# Moodly — Mood-based Content Recommender

Moodly is a small Flask web app that recommends movies, music, books and blog ideas based on a user's mood and an optional topic. The app calls the Groq AI chat/completions API to generate structured JSON recommendations and serves a single-page UI from `templates/index.html`.

## Features
- Simple single-page UI for selecting a mood and optional topic
- Flask backend endpoint `/generate` that calls Groq AI and returns structured JSON
- In-memory caching for repeated queries
- Health check endpoint at `/health`

## Stack
- Python + Flask
- Groq AI client (groq)
- Frontend: plain HTML/CSS/vanilla JS in `templates/index.html`

## Requirements
- Python 3.8+
- A Groq API key (GROQ_API_KEY) to call the Groq AI API

Recommended (optional) for production:
- Redis (or another external cache) instead of the in-memory CACHE
- Gunicorn or a process manager to run the app

## Environment variables
Create a `.env` file in the project root or set these variables in your environment:

```
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (example)
# FLASK_ENV=production
# PORT=8000
```

Note: The app currently reads GROQ_API_KEY from the environment using python-dotenv.

## Installation (local development)

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate     # Windows (PowerShell)
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your Groq API key to a `.env` file as shown above.

4. Run the app:

```bash
python app.py
```

By default this runs Flask's development server on `http://127.0.0.1:5000`. Open that URL in your browser.

## Running in production

A minimal production setup using Gunicorn (recommended to run behind a reverse proxy like Nginx):

```bash
# install gunicorn if you don't have it
pip install gunicorn

# run (bind to 0.0.0.0 on port 8000)
GROQ_API_KEY=your_groq_api_key gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

Adjust worker count and host/port to suit your deployment.

## Docker (optional)

You can add a Dockerfile if you'd like a containerized deployment. Minimal example (not included in this repo):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV GROQ_API_KEY=""
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

## API

POST /generate
- Content-Type: application/json
- Body: { "mood": "happy", "topic": "sci-fi" }
- Success: 200 JSON response containing keys: `moodSummary`, `movies`, `songs`, `books`, `blogs` (app enforces exactly 3 items per category in the prompt)
- Error: If GROQ_API_KEY is not set, the server returns 500 with a configuration error. If AI output can't be parsed, server may return 500 with the raw response included.

GET /health
- Returns a small JSON object with service status.

## Security & operational notes
- The Groq API key (GROQ_API_KEY) is a sensitive secret. Do NOT commit it to source control.
  - Use environment variables, a secrets manager, or platform-provided secret storage in production.
  - If you accidentally commit keys, rotate them immediately.
- The app currently uses an in-memory CACHE dictionary. For multi-instance deployments or to survive restarts, replace it with Redis or another external cache.
- The Flask development server (used by `python app.py`) is not suitable for production. Use Gunicorn, uWSGI, or a managed hosting platform and place a reverse proxy (e.g. Nginx) in front.

## Possible improvements
- Add robust error handling and retries around the Groq AI call.
- Add request rate-limiting and authentication if the API will be public.
- Replace in-memory cache with Redis and add cache expiration.
- Add unit tests for parsing logic and the `/generate` endpoint (mock Groq client).
- Add Dockerfile and GitHub Actions CI for linting/tests and building image.

## Contributing
Contributions are welcome. Open an issue or submit a pull request describing your change.

## License
This project does not include a license file. Add a license (e.g., MIT) if you want to make the code reusable by others.
