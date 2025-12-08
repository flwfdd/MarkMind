# Server (MarkMind)

This is the FastAPI server for the MarkMind app.

## Requirements

- Python >= 3.14 (as declared in `pyproject.toml`)
- Optional: use `pyenv`, `asdf`, or `venv` to manage Python versions

## Setup

Create and activate a virtual environment, then install the package (editable install recommended for development):

```bash
# In the `server` folder
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
# .\.venv\Scripts\activate

# Install editable and dependencies
python -m pip install --upgrade pip
pip install -e .
```

This will install the `fastapi[standard]` dependency (and `uvicorn`) declared in `pyproject.toml`.

## Development

Run the server using `uvicorn`, which enables auto-reload during development:

```bash
# in the server directory
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If the `uvicorn` CLI is not found after installing dependencies, ensure the virtual environment is activated or run via Python module:

```bash
# Using python -m
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Now visit `http://127.0.0.1:8000/` in your browser — you should receive a JSON response from the sample route.

## API Docs

FastAPI exposes interactive API docs by default with:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Testing

Use `curl`, HTTPie, or a browser to test the root endpoint:

```bash
curl http://127.0.0.1:8000/
# Expected: {"Hello": "From MarkMind!"}
```

## Adding Dependencies

To add a new runtime dependency for development, update `pyproject.toml` under `dependencies` and install it:

```bash
pip install <library>
# or
pip install -e .
```

## Tips

- Use `pipx` or `venv` for a clean environment.
- If you're using Docker, you can create a simple Dockerfile to run the FastAPI server.
- For production use, run Uvicorn with a process manager such as `gunicorn` or via a container.

***
Created by adding development notes for the server and helpful commands.
