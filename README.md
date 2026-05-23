# status‑tg‑alert

A **tiny** Python project that:

* Periodically fetches a URL (or any health‑check endpoint).
* Detects a change in HTTP status (e.g. 200 → non‑200 or vice‑versa).
* Sends a short Telegram message via Bot API to a configured chat.
* Runs inside a lightweight Docker container.
* Is backed by a **lean CI/CD** pipeline (GitHub Actions) that:
  * Runs fast lint & unit tests on every PR.
  * Builds a Docker image with `docker/build-push-action`.
  * Pushes to GitHub Container Registry with immutable `sha` tags.
  * Optionally deploys to a cheap VPS/Cloud‑Run on merge to `main`.

## Why this project?
* Demonstrates best‑practice CI for **tiny repos** (see the `ci.yml` workflow).
* Shows **Telegram status alerts**, a favorite of TopherBot.
* Stays under the 30 s “rest” rule by sleeping between checks.
* Minimal footprint – only a few files, no heavy frameworks.

## Quick start (local)
```bash
# 1. Clone the repo
git clone https://github.com/your‑user/status‑tg‑alert.git
cd status‑tg‑alert

# 2. Create a virtual env and install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Set required env vars (see .env.example)
export CHECK_URL="https://example.com/health"
export TELEGRAM_TOKEN="123456:ABCdef..."
export TELEGRAM_CHAT_ID="-123456789"

# 4. Run the watcher (default interval = 30 s)
python -m status_tg_alert
```

## Docker
```bash
# Build (the CI does the same)
DOCKER_BUILDKIT=1 docker build -t ghcr.io/<owner>/status-tg-alert:latest .

# Run (mount a .env file for secrets)
docker run -d --restart unless-stopped \
  --name status-tg-alert \
  --env-file .env \
  ghcr.io/<owner>/status-tg-alert:latest
```

## CI/CD overview
* **PR workflow** – Lint (`ruff`), type‑check (`mypy`), unit tests (`pytest`) – all under 2 min.
* **Build workflow** – Runs on merge to `main`; builds immutable Docker image tagged with `sha-<git‑sha>` and pushes to GHCR.
* **Deploy workflow (optional)** – If you provide `DEPLOY_HOST` and `SSH_KEY` secrets, the workflow will SSH into the host, pull the new image, and restart the container.
* **Cost‑saving patterns** – Heavy steps (Docker build) only on merge; preview environments are opt‑in via PR label `[preview]`.

## License
MIT – see `LICENSE`.

---
*Enjoy the tiny‑project vibes and feel free to extend it (e.g., add Slack integration, health‑check JSON parsing, or exponential back‑off).*