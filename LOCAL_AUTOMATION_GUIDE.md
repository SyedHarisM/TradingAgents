# TradingAgents — Local Automation Guide

This guide covers the custom watchlist runner and the lightweight dashboard added to the upstream TradingAgents framework.

## What the project does

- Reads stock symbols from `watchlist.txt`.
- Runs TradingAgents analysis for each symbol using the Google Gemini provider configured in `.env`.
- Retries one time for recognised temporary connection/API failures.
- Saves a complete HTML report for each successful analysis.
- Appends the ticker, decision, status, report path and error (if any) to `daily_summary.csv`.
- Builds a local `dashboard.html` with run totals, latest decisions and links to available reports.

This is a research/paper-analysis project. It does not connect to a live broker or submit real-money orders.

## Existing installation

For the current machine, the virtual environment and dependencies are already installed. Extract these files into the project root:

- `dashboard.py`
- `run_daily.bat`
- `install_dashboard.bat`
- `LOCAL_AUTOMATION_GUIDE.md`

The project root is the folder containing `daily_bot.py`, `watchlist.txt`, `.env` and `.venv`.

Double-click `install_dashboard.bat` once. It adds `dashboard.html` to `.gitignore`, checks the dashboard script, generates the local page from your existing CSV, and opens it in your browser.

## Run the dashboard

Generate or refresh it without making another API call:

```cmd
.venv\Scripts\python.exe dashboard.py
start dashboard.html
```

The dashboard reads `daily_summary.csv`. Report links open only when the corresponding HTML report file still exists on this computer.

## Run the full automation

Run the batch file from the project folder:

```cmd
run_daily.bat
```

It runs `daily_bot.py` and then refreshes the dashboard, even if the bot reports an error. It uses the existing `.venv` Python interpreter and does not need a new package installation.

For a quick one-stock test, run the Python runner directly:

```cmd
.venv\Scripts\python.exe daily_bot.py --limit 1
```

For the complete watchlist:

```cmd
.venv\Scripts\python.exe daily_bot.py
```

## Configure Windows Task Scheduler

Create a daily task at a time that suits you:

1. Open **Task Scheduler** and select **Create Basic Task**.
2. Name it `TradingAgents Daily Bot` and choose **Daily**.
3. Select the desired run time.
4. For the action, choose **Start a program**.
5. Program/script: `C:\Windows\System32\cmd.exe`
6. Add arguments: `/c "FULL_PROJECT_PATH\run_daily.bat"` (replace `FULL_PROJECT_PATH` with the actual folder path).
7. Start in: the project folder (the directory containing `run_daily.bat`).
8. Save the task. Initially, use **Run only when user is logged on** to keep the setup simple.

The PC must be powered on, awake and connected to the internet at the scheduled time. The task uses the API key stored in the local `.env` file. Do not put the API key in the task arguments or commit `.env` to GitHub.

## Configuration

The runner expects these settings in `.env`:

- `GOOGLE_API_KEY` — your private Google AI API key.
- `TRADINGAGENTS_LLM_PROVIDER=google`
- Quick and deep model settings configured to a Gemini model available to your account.

The tested configuration used `gemini-3.5-flash-lite` for quick and deep analysis, English output, one debate round and one risk round. Keep the exact settings aligned with the installed TradingAgents version and your available API quota.

Edit `watchlist.txt` to change the list of symbols. Use one Yahoo Finance ticker per line.

## Backtesting and presentation notes

The completed historical sweep in this project evaluated AAPL and NVDA over four ticker/date cells. All four were resolved. The observed results were indicative only: Hold (2 samples) had mean alpha of +1.45%; Overweight (2 samples) had a 0% directional hit rate and mean alpha of -5.15%. This sample is too small to establish reliable strategy performance.

For a short demonstration:

1. Show `watchlist.txt` with AAPL, NVDA and MSFT.
2. Show `daily_bot.py` and explain watchlist processing, transient-error retry and CSV logging.
3. Open `dashboard.html` and show latest decisions and report links.
4. Open one `complete_report.html` analysis report.
5. Show the backtest result and explain that it is a small research evaluation, not proof of profitability.

Never describe the outputs as guaranteed trading signals or financial advice.
