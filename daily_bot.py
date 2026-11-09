import argparse
import csv
import os
import time
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Import after loading .env so environment settings are available.
from tradingagents.default_config import build_default_config
from tradingagents.graph.trading_graph import TradingAgentsGraph


WATCHLIST_FILE = ROOT / "watchlist.txt"
SUMMARY_FILE = ROOT / "daily_summary.csv"

# "social" is the framework's internal name for its sentiment analyst.
ANALYSTS = ("market", "social", "news", "fundamentals")

DELAY_BETWEEN_TICKERS = 30
RETRY_DELAY = 30

CSV_FIELDS = [
    "run_timestamp",
    "date",
    "ticker",
    "decision",
    "status",
    "report_html",
    "error",
]


def read_watchlist():
    """Read unique stock symbols from watchlist.txt."""
    if not WATCHLIST_FILE.is_file():
        raise FileNotFoundError(f"Watchlist not found: {WATCHLIST_FILE}")

    tickers = []
    seen = set()

    for line in WATCHLIST_FILE.read_text(encoding="utf-8").splitlines():
        ticker = line.split("#", 1)[0].strip().upper()

        if ticker and ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)

    if not tickers:
        raise ValueError("watchlist.txt contains no stock symbols.")

    return tickers


def append_summary(row):
    """Append one result to the CSV, creating it with headers if needed."""
    write_header = (
        not SUMMARY_FILE.exists() or SUMMARY_FILE.stat().st_size == 0
    )

    with SUMMARY_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)

        if write_header:
            writer.writeheader()

        writer.writerow(row)


def is_transient_error(error):
    """Identify common errors that may succeed on a retry."""
    message = str(error).lower()

    transient_errors = (
        "429",
        "503",
        "resource_exhausted",
        "unavailable",
        "timeout",
        "timed out",
        "connecterror",
        "connection reset",
        "remoteprotocolerror",
        "server disconnected",
        "without sending a response",
        "ssl",
        "readerror",
        "10054",
         "forcibly closed by the remote host",
    )

    return any(term in message for term in transient_errors)


def main():
    parser = argparse.ArgumentParser(
        description="Run TradingAgents against a stock watchlist."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N tickers, useful for testing.",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1.")

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY is missing. Check your project's .env file."
        )

    config = build_default_config()

    if config.get("llm_provider") != "google":
        raise RuntimeError(
            "Expected Google as the configured LLM provider. "
            "Check TRADINGAGENTS_LLM_PROVIDER in .env."
        )

    tickers = read_watchlist()

    if args.limit is not None:
        tickers = tickers[:args.limit]

    run_date = date.today().isoformat()

    print(f"TradingAgents daily bot | Date: {run_date}")
    print(f"Tickers queued: {', '.join(tickers)}")

    engine = TradingAgentsGraph(
        selected_analysts=ANALYSTS,
        debug=False,
        config=config,
    )

    for index, ticker in enumerate(tickers):
        run_timestamp = datetime.now().isoformat(timespec="seconds")
        row = {
            "run_timestamp": run_timestamp,
            "date": run_date,
            "ticker": ticker,
            "decision": "",
            "status": "ERROR",
            "report_html": "",
            "error": "",
        }

        print(f"\n[{index + 1}/{len(tickers)}] Analyzing {ticker}...")

        for attempt in range(1, 3):
            try:
                state, decision = engine.propagate(ticker, run_date)
                report_dir = engine.save_reports(state, ticker, html=True)

                row["decision"] = str(decision)
                row["status"] = "SUCCESS"
                row["report_html"] = str(
                    Path(report_dir).parent / "complete_report.html"
                )
                row["error"] = ""

                print(f"{ticker}: {decision}")
                print(f"Report saved: {row['report_html']}")
                break

            except Exception as error:
                row["error"] = (
                    f"{type(error).__name__}: {str(error)[:300]}"
                )

                print(f"{ticker} attempt {attempt} failed: {row['error']}")

                if attempt == 1 and is_transient_error(error):
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    break

        append_summary(row)

        if index < len(tickers) - 1:
            print(f"Waiting {DELAY_BETWEEN_TICKERS} seconds...")
            time.sleep(DELAY_BETWEEN_TICKERS)

    print("\nRun finished.")
    print(f"Summary CSV: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()