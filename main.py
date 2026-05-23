#!/usr/bin/env python3
"""status_tg_alert – tiny URL monitor with Telegram notifications.

The script runs forever (or until interrupted). It waits ``CHECK_INTERVAL`` seconds between checks
(default 30 s to satisfy the ≥30 s rest preference).

Environment variables required:
    CHECK_URL          – URL to poll (e.g. https://example.com/health)
    TELEGRAM_TOKEN    – Bot token from BotFather
    TELEGRAM_CHAT_ID  – Integer or string ID of the chat ("@username" works)
    CHECK_INTERVAL    – Seconds between polls (optional, default 30)

Optional environment variables (for extended logging):
    LOG_LEVEL          – DEBUG, INFO, WARNING, ERROR (default INFO)
"""

import os
import sys
import time
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHECK_URL = os.getenv("CHECK_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if not all([CHECK_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
    sys.stderr.write(
        "[ERROR] Required env vars: CHECK_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID\n"
    )
    sys.exit(1)

logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------
@dataclass
class StatusSnapshot:
    ok: bool
    code: int
    timestamp: float

    def __str__(self) -> str:
        status = "UP" if self.ok else "DOWN"
        return f"{status} (HTTP {self.code})"

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
async def fetch_status(client: httpx.AsyncClient) -> StatusSnapshot:
    try:
        resp = await client.get(CHECK_URL, timeout=10.0)
        ok = resp.status_code == 200
        return StatusSnapshot(ok=ok, code=resp.status_code, timestamp=time.time())
    except Exception as exc:
        logger.debug("Exception while fetching %s: %s", CHECK_URL, exc)
        return StatusSnapshot(ok=False, code=0, timestamp=time.time())

async def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "disable_web_page_preview": True}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, data=payload, timeout=10.0)
            resp.raise_for_status()
            logger.info("Telegram notification sent: %s", message)
        except Exception as exc:
            logger.error("Failed to send Telegram message: %s", exc)

async def monitor() -> None:
    async with httpx.AsyncClient() as client:
        previous: Optional[StatusSnapshot] = None
        while True:
            current = await fetch_status(client)
            logger.debug("Fetched status: %s", current)
            if previous is not None and current.ok != previous.ok:
                # Status transition detected
                direction = "recovered" if current.ok else "failed"
                msg = (
                    f"🚨 Service *{direction.upper()}* 🚨\n"
                    f"URL: `{CHECK_URL}`\n"
                    f"New state: {current}\n"
                    f"Time: <t:{int(current.timestamp)}:F>"
                )
                await send_telegram(msg)
            previous = current
            await asyncio.sleep(CHECK_INTERVAL)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
import asyncio

if __name__ == "__main__":
    logger.info("Starting status‑tg‑alert – checking %s every %s seconds", CHECK_URL, CHECK_INTERVAL)
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        logger.info("Interrupted by user – exiting.")
        sys.exit(0)
