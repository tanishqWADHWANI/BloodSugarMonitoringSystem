Running the Blood Sugar Monitoring System (development)

This document outlines quick manual steps to run the backend, apply DB fixes, and open the frontend for local/Codespaces testing.

Prerequisites
```markdown
Running the Blood Sugar Monitoring System (development)

This document describes how to run the app in a HTTP-only local development setup.

Prerequisites
- docker (for MySQL container)
- python3 (3.10+), pip
- A static file server for the frontend (we use Python's simple server in examples)

Start backend locally
1. Create a Python virtualenv and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. Start the backend (development):

```bash
cd backend
# set envs as needed, e.g.:
export FLASK_ENV=development
# optionally restrict CORS origins (comma-separated), e.g.:
export CORS_ORIGINS="http://localhost:5500"
python3 app.py
```

Apply DB schema and triggers (idempotent)
1. If MySQL runs in a container called `bsm-mysql`, run:

```bash
./backend/init_db_idempotent.sh bsm-mysql
```

2. If the container uses a different root password or name, pass them as env vars or arguments.

Frontend (static pages)
- Serve `frontend/` with any static server (e.g. `python3 -m http.server 5500` from `frontend/`) and open `http://127.0.0.1:5500/specialist.html`.

Notes about remote previews (Codespaces)
- This repository is configured for HTTP-only local development. Remote preview environments (Codespaces, GitHub.dev) often expose the preview page over HTTPS which can cause mixed-content blocking when the backend is HTTP. For reliable testing, prefer one of these approaches:
  - Run the frontend and backend locally on your machine and open `http://127.0.0.1:5500/specialist.html` in your local browser.
  - If using Codespaces and you must use the browser preview, forward the backend port (5000) and access the forwarded URL from a full browser tab (not the preview iframe). You may need to paste an explicit API base URL into the Specialist page diagnostics (the override input) to point the frontend to the forwarded backend.

Frontend override keys (in-browser)
- `BSM_API_BASE` (localStorage): explicit API base URL to use (example: `http://127.0.0.1:5000/api`). If set, this overrides defaults.
- The frontend defaults to HTTP for local development and will use `http://<host>:5000/api` when no override is present.

Run headless smoke test
```bash
./scripts/headless_smoke_test.sh
```

If you want, I can open a PR that reverts any HTTPS-first UI/README guidance and keeps the repository in an HTTP-only developer flow.

```
The Specialist page includes a diagnostics box that lets you choose how the frontend should call the backend:
