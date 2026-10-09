"""Allow running: python -m reports.generate"""
from reports.generate import *

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="TrendAI Report Generator")
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"], default="weekly")
    parser.add_argument("--format", choices=["pdf", "xlsx", "both"], default="both")
    parser.add_argument("--product", type=str, default=None)
    args = parser.parse_args()

    generated = []
    if args.format in ("pdf", "both"):
        path = generate_pdf_report(args.period, product=args.product)
        if path:
            generated.append(path)
    if args.format in ("xlsx", "both"):
        path = generate_excel_report(args.period, product=args.product)
        if path:
            generated.append(path)

    if generated:
        print(f"\nGenerated reports:")
        for p in generated:
            print(f"  {p}")
