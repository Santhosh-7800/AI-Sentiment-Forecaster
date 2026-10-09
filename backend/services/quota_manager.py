"""
API Quota Management System
Tracks and manages free tier API quotas to prevent errors
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

<<<<<<< HEAD

DEFAULT_QUOTAS = {
    "gemini": 50,
    "newsapi": 100,
    "gnews": 100,
}

=======
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
class QuotaManager:
    """Manages API quotas for free tier services"""

    def __init__(self):
        self.quota_file = Path("data/quota_tracker.json")
        self.quota_file.parent.mkdir(exist_ok=True)
        self._load_quotas()

    def _load_quotas(self):
        """Load quota data from file"""
        if self.quota_file.exists():
            try:
                with open(self.quota_file, 'r') as f:
                    data = json.load(f)
                    self.quotas = data
            except Exception as e:
                logger.warning(f"Failed to load quota file: {e}")
                self._init_quotas()
        else:
            self._init_quotas()

    def _init_quotas(self):
        """Initialize quota tracking"""
<<<<<<< HEAD
        self.quotas = {}
        for service, max_daily in DEFAULT_QUOTAS.items():
            self.quotas[service] = {
                "requests_today": 0,
                "max_daily": max_daily,
                "reset_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "exhausted": False
            }
        self._save_quotas()

    def _ensure_service(self, service: str):
        """Ensure quota state exists for service (supports new fallback providers)."""
        if service in self.quotas:
            return

        max_daily = DEFAULT_QUOTAS.get(service, 100)
        self.quotas[service] = {
            "requests_today": 0,
            "max_daily": max_daily,
            "reset_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "exhausted": False
=======
        self.quotas = {
            "gemini": {
                "requests_today": 0,
                "max_daily": 50,  # Free tier limit
                "reset_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "exhausted": False
            },
            "newsapi": {
                "requests_today": 0,
                "max_daily": 100,  # Free tier limit
                "reset_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "exhausted": False
            }
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
        }
        self._save_quotas()

    def _save_quotas(self):
        """Save quota data to file"""
        try:
            with open(self.quota_file, 'w') as f:
                json.dump(self.quotas, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save quota file: {e}")

    def _check_reset(self, service: str):
        """Check if quota should reset"""
<<<<<<< HEAD
        self._ensure_service(service)
        quota = self.quotas.get(service, {})
        reset_value = quota.get("reset_time", "")
        try:
            reset_time = datetime.fromisoformat(reset_value)
        except Exception:
            reset_time = datetime.now() - timedelta(seconds=1)
=======
        quota = self.quotas.get(service, {})
        reset_time = datetime.fromisoformat(quota.get("reset_time", ""))
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)

        if datetime.now() >= reset_time:
            quota["requests_today"] = 0
            quota["exhausted"] = False
            quota["reset_time"] = (datetime.now() + timedelta(days=1)).isoformat()
            self._save_quotas()
            logger.info(f"[OK] {service.upper()} quota reset")

    def can_use(self, service: str) -> bool:
        """Check if service quota is available"""
        self._check_reset(service)
        quota = self.quotas.get(service, {})

        if quota.get("exhausted"):
            return False

        return quota.get("requests_today", 0) < quota.get("max_daily", 0)

    def consume(self, service: str) -> bool:
        """Consume one request from quota"""
<<<<<<< HEAD
        self._ensure_service(service)
=======
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
        if not self.can_use(service):
            self.quotas[service]["exhausted"] = True
            self._save_quotas()
            logger.warning(f"[WARN] {service.upper()} quota exhausted for today")
            return False

        self.quotas[service]["requests_today"] += 1
        self._save_quotas()
        return True

    def get_status(self, service: str) -> dict:
        """Get quota status"""
        self._check_reset(service)
        quota = self.quotas.get(service, {})
        return {
            "service": service,
            "requests_today": quota.get("requests_today", 0),
            "max_daily": quota.get("max_daily", 0),
            "remaining": quota.get("max_daily", 0) - quota.get("requests_today", 0),
            "exhausted": quota.get("exhausted", False),
            "resets_at": quota.get("reset_time", "")
        }

# Global instance
quota_manager = QuotaManager()
