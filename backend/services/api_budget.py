"""
Lightweight daily API quota tracker for free-tier-safe external API usage.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, Any


class ApiBudgetManager:
    def __init__(self, file_path: str | None = None, daily_limit: int | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        usage_dir = base_dir / "data" / "usage"
        usage_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = Path(file_path) if file_path else usage_dir / "quota_state.json"
        self.daily_limit = daily_limit if daily_limit is not None else int(os.getenv("DAILY_API_CALL_LIMIT", "80"))
        self._lock = Lock()

    def _today_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _read_state(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {"days": {}}

        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                state = json.load(f)
                if "days" not in state:
                    state["days"] = {}
                return state
        except Exception:
            return {"days": {}}

    def _write_state(self, state: Dict[str, Any]) -> None:
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def can_consume(self, amount: int = 1) -> bool:
        with self._lock:
            state = self._read_state()
            today = self._today_key()
            used = int(state["days"].get(today, 0))
            return (used + amount) <= self.daily_limit

    def consume(self, amount: int = 1) -> Dict[str, int]:
        with self._lock:
            state = self._read_state()
            today = self._today_key()
            used = int(state["days"].get(today, 0)) + amount
            state["days"][today] = used
            self._write_state(state)
            return {
                "date": today,
                "used": used,
                "limit": self.daily_limit,
                "remaining": max(self.daily_limit - used, 0),
            }

    def status(self) -> Dict[str, int | str]:
        with self._lock:
            state = self._read_state()
            today = self._today_key()
            used = int(state["days"].get(today, 0))
            return {
                "date": today,
                "used": used,
                "limit": self.daily_limit,
                "remaining": max(self.daily_limit - used, 0),
            }
