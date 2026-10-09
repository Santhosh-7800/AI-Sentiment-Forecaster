"""
Alert Engine
============
Reads aggregated analytics, detects anomalies, logs alerts.
Uses rule-based thresholds from config/alerts.yml.

Usage:
    python -m alerts.alert_engine
    python -m alerts.alert_engine --check-once
"""
import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

import yaml
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("alert_engine")

ANALYTICS_DIR = os.path.join(PROJECT_ROOT, "data", "analytics")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "alerts.yml")


def load_config() -> dict:
    """Load alert config from YAML."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    logger.warning(f"Config not found at {CONFIG_PATH}, using defaults")
    return {
        "alerts": {
            "thresholds": {
                "sentiment_spike_percent": 20,
                "sentiment_drop_percent": 15,
                "topic_surge_percent": 30,
                "negative_trend_slope": -0.1,
                "volume_spike_multiplier": 2.0,
                "min_negative_reviews": 3,
            }
        }
    }


def log_alert(alert: dict) -> None:
    """Write alert to log file and console."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_path = os.path.join(LOGS_DIR, "alerts.log")

    line = json.dumps(alert, default=str)
    with open(log_path, "a") as f:
        f.write(line + "\n")

    severity = alert.get("severity", "INFO").upper()
    if severity == "CRITICAL":
        logger.critical(f"ALERT: {alert['message']}")
    elif severity == "WARNING":
        logger.warning(f"ALERT: {alert['message']}")
    else:
        logger.info(f"ALERT: {alert['message']}")


def send_notification(alert: dict, config: dict) -> None:
    """
    Placeholder for email/Slack notifications.
    TODO: Implement email via smtplib and Slack via webhook.
    """
    notif_config = config.get("alerts", {}).get("notification", {})

    if notif_config.get("slack", {}).get("enabled"):
        logger.info(f"[SLACK PLACEHOLDER] Would send: {alert['message']}")

    if notif_config.get("email", {}).get("enabled"):
        logger.info(f"[EMAIL PLACEHOLDER] Would send: {alert['message']}")


def check_alerts() -> List[dict]:
    """
    Run all alert checks against current analytics data.

    Returns:
        List of triggered alert dicts
    """
    config = load_config()
    thresholds = config.get("alerts", {}).get("thresholds", {})
    alerts = []

    # ── Check product sentiment anomalies ──
    product_path = os.path.join(ANALYTICS_DIR, "product_comparison.parquet")
    if os.path.exists(product_path):
        products = pd.read_parquet(product_path)

        if len(products) > 0:
            global_mean = products["mean_score"].mean()
            global_std = products["mean_score"].std()

            for _, row in products.iterrows():
                product = row["product_or_topic"]
                score = row["mean_score"]
                count = row["count"]

                # Sentiment spike/drop detection
                if global_std > 0:
                    z_score = (score - global_mean) / global_std

                    if z_score < -1.5:
                        alert = {
                            "type": "sentiment_drop",
                            "product": product,
                            "severity": "CRITICAL" if z_score < -2.5 else "WARNING",
                            "message": f"Sentiment drop detected for '{product}': score={score:.3f} (z={z_score:.2f})",
                            "details": {
                                "mean_score": round(score, 4),
                                "global_mean": round(global_mean, 4),
                                "z_score": round(z_score, 2),
                                "review_count": int(count),
                            },
                            "timestamp": datetime.now().isoformat(),
                        }
                        alerts.append(alert)

                    elif z_score > 2.0:
                        alert = {
                            "type": "sentiment_spike",
                            "product": product,
                            "severity": "INFO",
                            "message": f"Positive sentiment spike for '{product}': score={score:.3f} (z={z_score:.2f})",
                            "details": {
                                "mean_score": round(score, 4),
                                "global_mean": round(global_mean, 4),
                                "z_score": round(z_score, 2),
                            },
                            "timestamp": datetime.now().isoformat(),
                        }
                        alerts.append(alert)

                # Volume spike check
                avg_count = products["count"].mean()
                multiplier = thresholds.get("volume_spike_multiplier", 2.0)
                if count > avg_count * multiplier:
                    alert = {
                        "type": "volume_spike",
                        "product": product,
                        "severity": "WARNING",
                        "message": f"Volume spike for '{product}': {int(count)} mentions (avg={avg_count:.0f})",
                        "details": {
                            "count": int(count),
                            "avg_count": round(avg_count, 1),
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                    alerts.append(alert)

                # High negative ratio check
                neg_pct = row.get("neg_pct", 0)
                min_neg = thresholds.get("min_negative_reviews", 3)
                neg_count = row.get("neg_count", 0)
                if neg_count >= min_neg and neg_pct > 40:
                    alert = {
                        "type": "quality_concern",
                        "product": product,
                        "severity": "WARNING",
                        "message": f"Quality concern for '{product}': {neg_pct:.0f}% negative reviews ({int(neg_count)} of {int(count)})",
                        "details": {
                            "negative_pct": round(neg_pct, 1),
                            "negative_count": int(neg_count),
                            "total_count": int(count),
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                    alerts.append(alert)

    # ── Check topic surges ──
    topic_path = os.path.join(ANALYTICS_DIR, "topic_trends.parquet")
    if os.path.exists(topic_path):
        topics = pd.read_parquet(topic_path)
        if len(topics) > 0:
            avg_count = topics["count"].mean()
            surge_pct = thresholds.get("topic_surge_percent", 30) / 100

            for _, row in topics.iterrows():
                if row["count"] > avg_count * (1 + surge_pct) and row["topic_id"] != -1:
                    alert = {
                        "type": "topic_surge",
                        "product": row["topic_label"],
                        "severity": "INFO",
                        "message": f"Emerging topic: '{row['topic_label']}' ({int(row['count'])} mentions, avg={avg_count:.0f})",
                        "details": {
                            "topic_id": int(row["topic_id"]),
                            "count": int(row["count"]),
                            "mean_sentiment": round(row["mean_score"], 3),
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                    alerts.append(alert)

    # Log all alerts
    for alert in alerts:
        log_alert(alert)
        send_notification(alert, config)

    if not alerts:
        logger.info("No alerts triggered.")

    return alerts


def run_alert_loop(interval_seconds: int = 3600):
    """
    Run alerts on a schedule (simple loop).

    Args:
        interval_seconds: Check interval in seconds (default: 1 hour)
    """
    logger.info(f"Starting alert monitoring loop (interval: {interval_seconds}s)")
    while True:
        try:
            alerts = check_alerts()
            logger.info(f"Check complete. {len(alerts)} alerts triggered.")
        except Exception as e:
            logger.error(f"Alert check failed: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TrendAI Alert Engine")
    parser.add_argument("--check-once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=3600, help="Loop interval in seconds")
    args = parser.parse_args()

    if args.check_once:
        alerts = check_alerts()
        print(f"\nTriggered {len(alerts)} alerts")
        for a in alerts:
            print(f"  [{a['severity']}] {a['message']}")
    else:
        run_alert_loop(interval_seconds=args.interval)
