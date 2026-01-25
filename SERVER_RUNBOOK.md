# Server Runbook (tmux)

These are the minimal commands to start Nordicamo on the server (in tmux), using the existing `.venv`.
We do not use nohup; use tmux for both backend and frontend.

## Backend (FastAPI)

```bash
tmux new -s namo-backend
cd /home/frede/NAMO_nov25/backend
source .venv/bin/activate
export DB_HOST=127.0.0.1
export DB_PORT=5432
export DB_NAME=namo_db
export DB_USER=namo_user
export DB_PASSWORD=namo_password
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Detach: `Ctrl-b d`

## Frontend (Streamlit)

```bash
tmux new -s namo-frontend
cd /home/frede/NAMO_nov25/frontend
source .venv/bin/activate
export NAMO_API_BASE_URL=http://127.0.0.1:8001
streamlit run app.py --server.port 8501
```

Detach: `Ctrl-b d`

## Notes

- Run each block in its own tmux session.
- Streamlit prints a lot of `use_container_width` warnings; those are harmless.
- Backend URL (server-local): `http://127.0.0.1:8001`
- Frontend URL (server-local): `http://127.0.0.1:8501`

## When to rebuild clean_articles

Run the dashboard refresh script whenever you load new data into the full `articles` table
or change filter rules in `scripts/dashboard_filter_rules.txt`.

```bash
cd /home/frede/NAMO_nov25
source backend/.venv/bin/activate
python scripts/from_fulldb_to_dashboard.py --config scripts/dashboard_filter_rules.txt
```

After running it, the dashboard updates immediately (no restart required), but you may need
to refresh the frontend to clear cached responses.

## Troubleshooting: Port 8001 already in use

If the backend exits with `Errno 98` (address already in use), find and kill the process:

```bash
lsof -i :8001
kill -9 <PID>
```

Then restart the backend. If it keeps coming back, check for a running tmux session and stop it:

```bash
tmux ls
tmux kill-session -t namo-backend
```
