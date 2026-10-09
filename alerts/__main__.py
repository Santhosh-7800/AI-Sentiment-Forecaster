"""Allow running: python -m alerts.alert_engine"""
from alerts.alert_engine import check_alerts, run_alert_loop

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TrendAI Alert Engine")
    parser.add_argument("--check-once", action="store_true")
    parser.add_argument("--interval", type=int, default=3600)
    args = parser.parse_args()

    if args.check_once:
        alerts = check_alerts()
        print(f"\nTriggered {len(alerts)} alerts")
        for a in alerts:
            print(f"  [{a['severity']}] {a['message']}")
    else:
        run_alert_loop(interval_seconds=args.interval)
