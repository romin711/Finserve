import argparse
import time
from datetime import datetime

from app import create_app
from app.services.daily_analysis_service import run_dead_stock_analysis


def start_daily_analysis_scheduler(
    interval_seconds=86400,
    iterations=None,
    sales_threshold=10,
    days_threshold=15,
    high_stock_threshold=100,
):
    app = create_app()
    run_count = 0

    while True:
        with app.app_context():
            run_dead_stock_analysis(
                sales_threshold=sales_threshold,
                days_threshold=days_threshold,
                high_stock_threshold=high_stock_threshold,
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Dead stock updated")

        run_count += 1
        if iterations is not None and run_count >= iterations:
            break

        time.sleep(interval_seconds)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simulate automatic daily dead-stock analysis."
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=86400,
        help="How often to run analysis. Default: 86400 (24 hours).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="How many cycles to run. Default: forever.",
    )
    parser.add_argument("--sales-threshold", type=float, default=10)
    parser.add_argument("--days-threshold", type=float, default=15)
    parser.add_argument("--high-stock-threshold", type=float, default=100)
    return parser.parse_args()


def main():
    args = parse_args()
    start_daily_analysis_scheduler(
        interval_seconds=args.interval_seconds,
        iterations=args.iterations,
        sales_threshold=args.sales_threshold,
        days_threshold=args.days_threshold,
        high_stock_threshold=args.high_stock_threshold,
    )


if __name__ == "__main__":
    main()
