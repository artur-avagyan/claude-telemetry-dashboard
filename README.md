# Claude Telemetry Dashboard

> Interactive analytics platform built on Claude Code telemetry data.  
> Features 6 dashboard tabs, ML-based 7-day usage forecasting, and a fully styled dark-warm UI built with Streamlit + Plotly.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Data Schema](#data-schema)
4. [Setup & Installation](#setup--installation)
5. [Step 1 — Generate Fake Data](#step-1--generate-fake-data)
6. [Step 2 — Run the ETL Pipeline](#step-2--run-the-etl-pipeline)
7. [Step 3 — Launch the Dashboard](#step-3--launch-the-dashboard)
8. [Dashboard Features](#dashboard-features)
9. [Technical Design Decisions](#technical-design-decisions)
10. [Dependencies](#dependencies)
11. [LLM Usage Log](#llm-usage-log)

---

## Project Overview

This project was built as part of the **Provectus Internship Technical Assignment**.  
The goal is to process raw Claude Code telemetry logs, store them in a normalized SQLite database, and surface actionable analytics through an interactive Streamlit dashboard.

**Data scope:** ~60-day window (Dec 2025 – Jan 2026) with ~118,000 telemetry events across 5 Claude models and ~100 users.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Raw Data Sources                         │
│   data/output/telemetry_logs.jsonl   data/output/employees.csv  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ETL Pipeline  (data/etl.py)                 │
│  parse_events() → build_users/sessions/events/api_requests/...  │
│  save_to_db() → writes 9 normalized tables                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SQLite Database  (data/telemetry.db)           │
│  users · sessions · resources · events · user_prompts           │
│  api_requests · tool_decisions · tool_results · api_errors      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                Streamlit Dashboard  (dashboard/app.py)          │
│  6 tabs: Overview · Trends · Models · Tools · Users · Errors    │
│  Sidebar filters: date range · model · practice                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Schema

The ETL pipeline normalizes raw JSONL logs into 9 SQLite tables:

| Table | Description | Key Columns |
|---|---|---|
| `users` | One row per unique user, enriched with employee metadata | `user_id`, `user_email`, `user_practice`, `user_level`, `user_location` |
| `sessions` | One row per unique session | `attributes.session.id`, `attributes.user.id`, `attributes.terminal.type` |
| `resources` | Machine/OS environment per session | host, OS, architecture |
| `events` | Base table — one row per log event | `log_id`, `attributes.event.name`, `attributes.event.timestamp` |
| `user_prompts` | User prompt events with length metadata | `log_id`, `attributes.prompt_length` |
| `api_requests` | API call events with model/token/cost data | `attributes.model`, `attributes.cost_usd`, `attributes.input_tokens` |
| `tool_decisions` | Tool accept/reject decisions | `attributes.tool_name`, `attributes.decision` |
| `tool_results` | Tool execution outcomes | `attributes.tool_name`, `attributes.success`, `attributes.duration_ms` |
| `api_errors` | Failed API calls with error details | `attributes.model`, `attributes.error`, `attributes.status_code` |

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- `pip`

### 1. Clone the repository

```bash
git clone https://github.com/artur-avagyan/claude-telemetry-dashboard.git
cd claude-telemetry-dashboard
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 1 — Generate Fake Data

If you don't have real telemetry logs, generate synthetic data:

```bash
python data/generate_fake_data.py
```

This creates two files:
- `data/output/telemetry_logs.jsonl` — simulated Claude Code telemetry events (~60 days)
- `data/output/employees.csv` — employee metadata (name, practice, level, location)

---

## Step 2 — Run the ETL Pipeline

```bash
python -m data.etl
```

This pipeline:
1. Loads and parses raw JSONL log batches
2. Flattens nested JSON into a wide DataFrame using `pd.json_normalize`
3. Builds 9 normalized tables (users, sessions, events, api_requests, etc.)
4. Writes all tables to `data/telemetry.db` (SQLite)

Expected output:
```
Loading raw data...
Parsing events...
Building tables...
Saving to SQLite...
  Saved 101 rows → users
  Saved 4,821 rows → sessions
  ...
Done!
```

---

## Step 3 — Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Then open your browser at `http://localhost:8501`.

Use the **sidebar** to filter by:
- Date range
- Model(s)
- Practice(s)

---

## Dashboard Features

### 📊 Overview
- 8 KPI tiles: total requests, cost, error rate, avg latency, token volumes, active users/sessions
- Cost share pie chart by model
- Token breakdown bar chart (input / output / cache)
- Tool decision summary (accept vs. reject stacked bar)

### 📈 Trends
- Daily events line chart with **7-day linear regression forecast** + shaded forecast zone
- Forecast KPI tiles: predicted total, daily average, trend direction (▲/▼)
- Daily active users & sessions with individual forecasts
- Daily API requests and error count bar charts

### 🤖 Models
- Full model performance table: requests, cost, latency, token averages, error rate
- Cost by model (horizontal bar), avg latency, token comparison, error rate charts

### 🔧 Tools
- Tool usage table: runs, success rate, latency, result size
- Top 15 tools by runs, success rate ranking, latency and result size charts

### 👥 Users
- Events and engagement by practice and seniority level
- Top 20 most active users table
- Prompt length distribution histogram

### 🚨 Errors
- 3 KPI tiles: total errors, affected models, error rate
- Errors by HTTP status code, by model, daily error trend area chart
- Retry attempt distribution, top error messages table

---

## Technical Design Decisions

### Error Handling & Validation
- `qry()` wraps all SQLite queries in `try/except` — returns an empty DataFrame on failure instead of crashing
- `safe_row()` helper replaces all raw `.iloc[0]` calls — returns zero-default values if a query returns no rows
- Empty model/practice filter selections trigger `st.warning` + `st.stop()` before any query runs
- Invalid date range (`From > To`) triggers `st.error` + `st.stop()`
- `get_date_range()` handles missing/null timestamps with a fallback to today's date

### Forecasting
- `build_forecast()` uses `numpy.polyfit` (degree-1 linear regression) on daily event counts
- Projects 7 days forward, clamps negative values to 0
- Requires minimum 4 data points — silently skips if insufficient data

### UI/Styling
- All charts use a custom Plotly template (`"plotly_dark+claude"`) with transparent backgrounds and orange Cinzel titles
- All `st.dataframe` calls replaced with a custom `show_table()` HTML renderer for consistent dark-warm styling
- Professional hovertemplates on every chart — no raw column names exposed to users

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | 1.55.0 | Web dashboard framework |
| `plotly` | 6.6.0 | Interactive charts |
| `pandas` | 2.3.3 | Data manipulation |
| `numpy` | 2.4.3 | Forecasting (linear regression) |

Full list with transitive dependencies in [requirements.txt](requirements.txt).

---

## LLM Usage Log

This project was developed with assistance from **GitHub Copilot (Claude Sonnet 4.6)**.

### AI Tools Used
- **GitHub Copilot** (VS Code) — code generation, debugging, refactoring

### Key Prompts & Usage Examples

| Prompt | Purpose | Validation Method |
|---|---|---|
| *"Analyze the schema of telemetry.db and suggest what analytics pages to build in a Streamlit dashboard"* | Dashboard planning | Manually reviewed table schemas and row counts in SQLite |
| *"Create all 6 dashboard tabs with charts for the telemetry data"* | Full dashboard generation | Ran `py_compile`, tested in browser, verified chart data against direct SQL queries |
| *"Add error handling, data validation, and filter guards — step by step"* | Robustness improvements | Tested each guard: empty filters, flipped date range, missing DB file |
| *"Implement 7-day linear regression forecast on the Trends tab using only numpy"* | Predictive analytics feature | Visually verified forecast direction matched observed trend; checked edge case with <4 data points |
| *"Style the entire dashboard — sidebar, tabs, tables, charts, KPI cards — in a dark warm orange/cream palette with Cinzel font"* | UI/UX design | Iterative browser testing across all 6 tabs |

### How AI Output Was Validated
- All generated Python was compiled with `python -m py_compile dashboard/app.py` before use
- SQL queries were verified against direct SQLite queries in a notebook
- Chart hovertemplates were tested interactively in the running Streamlit app
- Edge cases (empty DB, no filter selection, date inversion) were manually triggered and confirmed handled

---

*Built for Provectus Internship Program — March 2026*
