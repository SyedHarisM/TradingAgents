"""Generate a lightweight, local HTML dashboard from daily_summary.csv.

No web framework, database, or external assets are required.
Run directly with: python dashboard.py
"""
from __future__ import annotations

import csv
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMMARY_FILE = ROOT / "daily_summary.csv"
OUTPUT_FILE = ROOT / "dashboard.html"


def load_rows() -> list[dict[str, str]]:
    """Load run history; return an empty list before the first run."""
    if not SUMMARY_FILE.is_file():
        return []
    with SUMMARY_FILE.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def report_link(value: str) -> str:
    """Return a local file URL only when the saved report really exists."""
    if not value:
        return ""
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if not candidate.is_file():
        return ""
    return candidate.resolve().as_uri()


def build_dashboard(rows: list[dict[str, str]]) -> str:
    rows = sorted(rows, key=lambda row: str(row.get("run_timestamp") or ""), reverse=True)
    total = len(rows)
    successes = sum((row.get("status") or "").upper() == "SUCCESS" for row in rows)
    failures = total - successes
    rate = (successes / total * 100) if total else 0.0

    latest_by_ticker: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = (row.get("ticker") or "").strip().upper()
        if ticker:
            latest_by_ticker.setdefault(ticker, row)

    ticker_cards = []
    for ticker, row in sorted(latest_by_ticker.items()):
        status = (row.get("status") or "UNKNOWN").upper()
        status_class = "success" if status == "SUCCESS" else "error"
        decision = escape(str(row.get("decision") or "No decision"))
        url = report_link(row.get("report_html", ""))
        report = (
            f'<a class="report-link" href="{escape(url, quote=True)}">Open report ↗</a>'
            if url else '<span class="muted">Report unavailable</span>'
        )
        ticker_cards.append(
            '<article class="ticker-card">'
            f'<div class="ticker-top"><span class="ticker">{escape(ticker)}</span>'
            f'<span class="status {status_class}">{escape(status)}</span></div>'
            f'<div class="decision">{decision}</div>'
            f'<div class="ticker-foot"><span>{escape(str(row.get("date") or "—"))}</span>{report}</div>'
            '</article>'
        )

    activity_rows = []
    for row in rows[:15]:
        status = (row.get("status") or "UNKNOWN").upper()
        status_class = "success" if status == "SUCCESS" else "error"
        url = report_link(row.get("report_html", ""))
        report = (
            f'<a class="report-link" href="{escape(url, quote=True)}">View ↗</a>'
            if url else '<span class="muted">—</span>'
        )
        activity_rows.append(
            '<tr>'
            f'<td>{escape(str(row.get("run_timestamp") or "—"))}</td>'
            f'<td class="table-ticker">{escape(str(row.get("ticker") or "—"))}</td>'
            f'<td>{escape(str(row.get("decision") or "—"))}</td>'
            f'<td><span class="status {status_class}">{escape(status)}</span></td>'
            f'<td>{report}</td>'
            '</tr>'
        )

    if ticker_cards:
        ticker_content = '<div class="ticker-grid">' + "".join(ticker_cards) + '</div>'
    else:
        ticker_content = (
            '<div class="empty">No analyses recorded yet. '
            'Run <code>python daily_bot.py</code> to begin.</div>'
        )

    activity_content = "".join(activity_rows) or (
        '<tr><td colspan="5" class="empty-row">No run history available yet.</td></tr>'
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Local TradingAgents stock analysis activity dashboard">
<title>TradingAgents | Daily Dashboard</title>
<style>
:root {{ color-scheme: dark; --bg:#0b1220; --panel:#121d2d; --panel2:#172437; --line:#26384d; --text:#edf4fa; --muted:#91a3b8; --accent:#36d6a0; --red:#ff7d83; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:radial-gradient(ellipse at top left,#172b3a 0%,var(--bg) 42%); color:var(--text); font:15px/1.5 "Segoe UI",Arial,sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:38px 24px 56px; }}
header {{ display:flex; align-items:center; justify-content:space-between; gap:18px; margin-bottom:30px; }}
.eyebrow {{ color:var(--accent); text-transform:uppercase; letter-spacing:.16em; font-size:11px; font-weight:700; }}
h1 {{ margin:5px 0 4px; font-size:clamp(27px,4vw,38px); letter-spacing:-.04em; }}
.subtitle,.muted {{ color:var(--muted); }}
button {{ border:1px solid var(--line); border-radius:10px; padding:10px 14px; color:var(--text); background:var(--panel2); cursor:pointer; font-weight:600; }}
button:hover {{ border-color:var(--accent); }}
.grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:24px 0 30px; }}
.metric,.section {{ background:rgba(18,29,45,.92); border:1px solid var(--line); border-radius:16px; }}
.metric {{ padding:18px 20px; }}
.metric-label {{ color:var(--muted); font-size:13px; }}
.metric-value {{ margin-top:5px; font-size:30px; font-weight:700; letter-spacing:-.04em; }}
.metric-value.green {{ color:var(--accent); }}
.metric-value.red {{ color:var(--red); }}
.section {{ padding:22px; margin-top:18px; }}
.section-head {{ display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:16px; }}
h2 {{ margin:0; font-size:18px; }}
.ticker-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
.ticker-card {{ background:var(--panel2); border:1px solid var(--line); border-radius:13px; padding:17px; min-width:0; }}
.ticker-top,.ticker-foot {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
.ticker {{ font-weight:800; font-size:17px; letter-spacing:.06em; }}
.status {{ display:inline-block; padding:3px 8px; border-radius:99px; font-size:10px; font-weight:800; letter-spacing:.06em; }}
.status.success {{ color:var(--accent); background:rgba(54,214,160,.12); }}
.status.error {{ color:var(--red); background:rgba(255,125,131,.12); }}
.decision {{ font-size:23px; font-weight:700; margin:18px 0; }}
.ticker-foot {{ color:var(--muted); font-size:12px; flex-wrap:wrap; }}
a {{ color:var(--accent); text-decoration:none; font-weight:650; }}
a:hover {{ text-decoration:underline; }}
.table-wrap {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; min-width:650px; }}
th {{ color:var(--muted); text-transform:uppercase; letter-spacing:.1em; font-size:10px; text-align:left; padding:11px 12px; }}
td {{ padding:13px 12px; border-top:1px solid var(--line); font-size:13px; }}
.table-ticker {{ font-weight:800; }}
.empty,.empty-row {{ color:var(--muted); text-align:center; padding:26px 12px; }}
.notice {{ margin-top:22px; padding:13px 16px; border-left:3px solid var(--accent); background:rgba(54,214,160,.07); border-radius:7px; color:var(--muted); font-size:12px; }}
footer {{ color:var(--muted); text-align:center; font-size:11px; margin-top:24px; }}
@media(max-width:850px) {{ .grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .ticker-grid {{ grid-template-columns:1fr; }} }}
@media(max-width:520px) {{ main {{ padding:25px 14px 40px; }} header {{ align-items:flex-start; }} .grid {{ gap:9px; }} .metric {{ padding:14px; }} .metric-value {{ font-size:25px; }} .section {{ padding:16px; }} }}
</style>
</head>
<body>
<main>
<header>
<div><div class="eyebrow">Research workspace · Local dashboard</div><h1>TradingAgents</h1><div class="subtitle">Daily stock-analysis activity and generated reports</div></div>
<button onclick="window.location.reload()">Refresh view ↻</button>
</header>
<section class="grid" aria-label="Run metrics">
<div class="metric"><div class="metric-label">Total analyses</div><div class="metric-value">{total}</div></div>
<div class="metric"><div class="metric-label">Successful</div><div class="metric-value green">{successes}</div></div>
<div class="metric"><div class="metric-label">Failed</div><div class="metric-value red">{failures}</div></div>
<div class="metric"><div class="metric-label">Success rate</div><div class="metric-value">{rate:.0f}%</div></div>
</section>
<section class="section"><div class="section-head"><h2>Latest stock decisions</h2><span class="muted">Most recent result per ticker</span></div>{ticker_content}</section>
<section class="section"><div class="section-head"><h2>Recent activity</h2><span class="muted">Latest 15 runs</span></div><div class="table-wrap"><table><thead><tr><th>Run time</th><th>Stock</th><th>Decision</th><th>Status</th><th>Report</th></tr></thead><tbody>{activity_content}</tbody></table></div></section>
<div class="notice"><strong>Research / paper mode:</strong> this project generates AI-assisted stock analysis and reports. It does not connect to a live broker or place real-money trades. Results are not financial advice.</div>
<footer>Generated locally from daily_summary.csv · No external dashboard service or tracking</footer>
</main>
</body>
</html>
"""


def generate_dashboard() -> Path:
    """Build dashboard.html next to the project files and return its path."""
    OUTPUT_FILE.write_text(build_dashboard(load_rows()), encoding="utf-8")
    return OUTPUT_FILE


if __name__ == "__main__":
    print(f"Dashboard generated: {generate_dashboard()}")
