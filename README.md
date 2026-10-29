# Sprout Smart Canteen

A small Python + HTML + SQLite demo app.

## Deploy on Render
- Runtime / Language: Python
- Build command: `python --version`
- Start command: `python smart_canteen.py`
- Render sets the `PORT` environment variable automatically.

Note: this demo uses SQLite (`canteen.db`). On Render's free web service, local files are ephemeral, so orders and waste logs can be lost when the service restarts, spins down, or redeploys. This is suitable for a class demo, not durable production storage.
