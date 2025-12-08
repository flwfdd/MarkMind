# MarkMind

This repository contains two main parts:

- `client/` — Vue 3 + Vite frontend
- `server/` — FastAPI backend

See `client/README.md` and `server/README.md` for project-specific development details.

## Quick-start (Development)

Open two terminals and run the client and server separately.

Terminal 1 — Server:

```bash
cd server
uv sync
uv run fastapi dev main.py
```

Terminal 2 — Client:

```bash
cd client
pnpm install
pnpm dev
```

The client runs (by default) at `http://localhost:5173` and will talk to the backend at `http://127.0.0.1:8000/`.

## Contributing

Please follow the instructions in `client/README.md` and `server/README.md` for code-style checks, linters, and how to run the app locally. If you add new endpoints or change an API contract, please update docs or tests.

