import base64
import datetime
import os
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ── global Plotly theme ───────────────────────────────────────────────────────
_ORANGE  = "#CF7650"
_CREAM   = "#F7F2EE"
_BG      = "rgba(0,0,0,0)"   # transparent so Streamlit bg shows through
_GRID    = "rgba(207,118,80,0.12)"

pio.templates["claude"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        font=dict(color=_CREAM, family="Inter, sans-serif", size=13),
        title=dict(
            font=dict(color=_ORANGE, family="Cinzel, serif", size=16),
            x=0.01,
        ),
        xaxis=dict(
            gridcolor=_GRID, zerolinecolor=_GRID,
            tickfont=dict(color=_CREAM),
            title_font=dict(color=_CREAM),
        ),
        yaxis=dict(
            gridcolor=_GRID, zerolinecolor=_GRID,
            tickfont=dict(color=_CREAM),
            title_font=dict(color=_CREAM),
        ),
        colorway=[_ORANGE, "#B96443", "#8B4513", "#E8956D", "#A0522D", "#D2691E"],
    )
)
pio.templates.default = "plotly_dark+claude"

# ── page config ──────────────────────────────────────────────────────────────
ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "claude-ai_2.png")

st.set_page_config(
    page_title="Claude Code Usage Analytics Platform",
    layout="wide",
    page_icon="✳️",
)

# ── header ────────────────────────────────────────────────────────────────────
icon_html = ""
if os.path.exists(ICON_PATH):
    with open(ICON_PATH, "rb") as f:
        icon_b64 = base64.b64encode(f.read()).decode("utf-8")
    icon_html = f'<img src="data:image/png;base64,{icon_b64}" class="title-icon" alt="Claude icon"/>'

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&display=swap');
        .title-container {{
            background: linear-gradient(135deg, #CF7650 0%, #B96443 100%);
            padding: 24px 30px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 14px;
            box-shadow: 0 6px 14px rgba(0,0,0,0.18);
            border: 1px solid rgba(255,255,255,0.18);
            margin-bottom: 8px;
        }}
        .title-icon {{ width:54px; height:54px; border-radius:12px; flex-shrink:0; }}
        .title-text {{
            color:#F7F2EE; margin:0; font-size:2.2em; font-weight:700;
            font-family:'Cinzel',serif; letter-spacing:0.6px; line-height:1.1;
            text-shadow:1px 2px 6px rgba(0,0,0,0.25);
        }}
        .kpi-card {{ background:#1e1e1e; border-radius:10px; padding:16px 20px;
                     border-left:4px solid #CF7650; }}
        /* ── KPI grid cards ─────────────────────────────────────── */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 4px;
        }}
        .kpi-grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-bottom: 4px;
        }}
        .kpi-tile {{
            background: linear-gradient(145deg, #4d3526 0%, #3a2518 100%);
            border: 1px solid rgba(207,118,80,0.50);
            border-top: 3px solid #CF7650;
            border-radius: 12px;
            padding: 18px 22px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.28);
            transition: transform .15s;
        }}
        .kpi-tile:hover {{ transform: translateY(-3px); }}
        .kpi-label {{
            font-size: 0.72em;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #CF7650;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 1.65em;
            font-weight: 700;
            color: #F7F2EE;
            line-height: 1.1;
        }}
        .kpi-icon {{
            font-size: 1.4em;
            float: right;
            opacity: 0.55;
            margin-top: -4px;
        }}
        /* ── styled table ───────────────────────────────────────── */
        .styled-table {{
            width: 100%;
            border-collapse: collapse;
            border-radius: 10px;
            overflow: hidden;
            font-size: 0.88em;
            font-family: Inter, sans-serif;
        }}
        .styled-table thead tr {{
            background: #CF7650;
        }}
        .styled-table th {{
            color: #1a0f0a;
            font-family: 'Cinzel', serif;
            font-size: 0.76em;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            padding: 10px 14px;
            text-align: left;
            border: 1px solid rgba(207,118,80,0.4);
        }}
        .styled-table td {{
            padding: 7px 14px;
            color: #F7F2EE;
            border: 1px solid rgba(207,118,80,0.12);
            background: #3a2518;
        }}
        .styled-table tbody tr:nth-child(even) td {{
            background: #4d3526;
        }}
        .styled-table tbody tr:hover td {{
            background: #CF7650;
            color: #1a0f0a;
        }}
        /* ── tabs ──────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 6px;
            background: transparent;
            border-bottom: 2px solid rgba(207,118,80,0.25);
            padding-bottom: 0;
        }}
        .stTabs [data-baseweb="tab"] {{
            background: linear-gradient(145deg, #3a2518, #2a1a10);
            border: 1px solid rgba(207,118,80,0.30);
            border-bottom: none;
            border-radius: 10px 10px 0 0;
            color: #b08060;
            font-family: 'Cinzel', serif;
            font-size: 0.78em;
            font-weight: 600;
            letter-spacing: 0.06em;
            padding: 10px 20px;
            transition: all .2s;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            background: linear-gradient(145deg, #4d3526, #3a2518);
            color: #F7F2EE;
            border-color: rgba(207,118,80,0.55);
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(145deg, #CF7650, #B96443) !important;
            color: #1a0f0a !important;
            border-color: #CF7650 !important;
            font-weight: 700;
            box-shadow: 0 -2px 10px rgba(207,118,80,0.35);
        }}
        .stTabs [data-baseweb="tab-highlight"] {{
            background: transparent !important;
        }}
        .stTabs [data-baseweb="tab-border"] {{
            display: none;
        }}
        /* ── subheaders ─────────────────────────────────────────── */
        h2, [data-testid="stHeadingWithActionElements"] h2 {{
            font-family: 'Cinzel', serif !important;
            font-size: 1.15em !important;
            font-weight: 700 !important;
            letter-spacing: 0.07em !important;
            color: #CF7650 !important;
            border-bottom: 1px solid rgba(207,118,80,0.30);
            padding-bottom: 6px;
            margin-bottom: 16px;
        }}
        h3, h4 {{
            font-family: 'Cinzel', serif !important;
            color: #E8956D !important;
            letter-spacing: 0.05em !important;
        }}
        /* ── sidebar ────────────────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #4a2e1a 0%, #3a2210 100%);
            border-right: 1px solid rgba(207,118,80,0.25);
        }}
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            font-family: 'Cinzel', serif !important;
            color: #CF7650 !important;
            letter-spacing: 0.07em !important;
            border-bottom: 1px solid rgba(207,118,80,0.25);
            padding-bottom: 6px;
        }}
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown p {{
            color: #F7F2EE !important;
            font-size: 0.85em;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] > div {{
            background: #3a2518 !important;
            border-color: rgba(207,118,80,0.40) !important;
            color: #F7F2EE !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="tag"] {{
            background: #CF7650 !important;
            color: #1a0f0a !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: rgba(207,118,80,0.25);
        }}
        [data-testid="stSidebar"] [data-testid="stDateInput"] input {{
            background: #3a2518 !important;
            color: #F7F2EE !important;
            border-color: rgba(207,118,80,0.40) !important;
        }}
    </style>
    <div class="title-container">
        {icon_html}
        <h1 class="title-text">Claude Code Usage Analytics Platform</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── DB connection ─────────────────────────────────────────────────────────────
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.db")
DEFAULT_DB = os.path.normpath(DEFAULT_DB)

with st.sidebar:
    st.header("⚙️ Settings")
    # db_path = st.text_input("Database path", value=DEFAULT_DB)
    db_path = DEFAULT_DB
    if not os.path.exists(db_path):
        st.error("DB file not found.")
        st.stop()

    # Date filter (driven by events table)
    @st.cache_data(show_spinner=False)
    def get_date_range(path):
        try:
            conn = sqlite3.connect(path)
            df = pd.read_sql_query(
                "SELECT date(MIN(`attributes.event.timestamp`)) AS mn, "
                "date(MAX(`attributes.event.timestamp`)) AS mx FROM events",
                conn,
            )
            conn.close()
            if df.empty or df.iloc[0]["mn"] is None:
                today = datetime.date.today().isoformat()
                return today, today
            return df.iloc[0]["mn"], df.iloc[0]["mx"]
        except sqlite3.OperationalError:
            today = datetime.date.today().isoformat()
            return today, today

    mn, mx = get_date_range(db_path)
    d_from = st.date_input("From", value=datetime.date.fromisoformat(mn))
    d_to   = st.date_input("To",   value=datetime.date.fromisoformat(mx))

    st.divider()
    # Model filter
    @st.cache_data(show_spinner=False)
    def get_models(path):
        conn = sqlite3.connect(path)
        df = pd.read_sql_query(
            "SELECT DISTINCT `attributes.model` AS model FROM api_requests ORDER BY model",
            conn,
        )
        conn.close()
        return df["model"].tolist()

    all_models = get_models(db_path)
    sel_models = st.multiselect("Models", all_models, default=all_models)

    # Practice filter
    @st.cache_data(show_spinner=False)
    def get_practices(path):
        conn = sqlite3.connect(path)
        df = pd.read_sql_query("SELECT DISTINCT user_practice FROM users ORDER BY 1", conn)
        conn.close()
        return df["user_practice"].tolist()

    all_practices = get_practices(db_path)
    sel_practices = st.multiselect("Practices", all_practices, default=all_practices)

# ── shared query helper ───────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def qry(path, sql, params=None):
    try:
        conn = sqlite3.connect(path)
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except sqlite3.OperationalError as e:
        st.warning(f"Query failed: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame()

# ── safe single-row extractor ───────────────────────────────────────────────
def safe_row(df, defaults=None):
    """Return first row of df as a Series; fall back to defaults if empty."""
    if df is not None and not df.empty:
        return df.iloc[0]
    if defaults:
        return pd.Series(defaults)
    return pd.Series(dtype=object)

# ── styled HTML table renderer ────────────────────────────────────────────────
def _fmt(v):
    """Format a cell value: integers and floats get comma separators."""
    if pd.isna(v):
        return ""
    if isinstance(v, float):
        return f"{v:,.2f}" if v != int(v) else f"{int(v):,}"
    if isinstance(v, int):
        return f"{v:,}"
    return v

def show_table(df, rename=None):
    display = df.rename(columns=rename) if rename else df.copy()
    header = "".join(f"<th>{c}</th>" for c in display.columns)
    rows = ""
    for _, row in display.iterrows():
        cells = "".join(f"<td>{_fmt(v)}</td>" for v in row)
        rows += f"<tr>{cells}</tr>"
    st.markdown(
        f'<div style="overflow-x:auto;margin-bottom:12px;">'
        f'<table class="styled-table"><thead><tr>{header}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>',
        unsafe_allow_html=True,
    )

d_from_s = str(d_from)
d_to_s   = str(d_to)

# ── filter validation ─────────────────────────────────────────────────────────
_filters_ok = True
if d_from > d_to:
    st.error("⚠️ 'From' date must not be after 'To' date — please fix the date range in the sidebar.")
    _filters_ok = False
if not sel_models:
    st.warning("⚠️ No models selected — please select at least one model in the sidebar.")
    _filters_ok = False
if not sel_practices:
    st.warning("⚠️ No practices selected — please select at least one practice in the sidebar.")
    _filters_ok = False
if not _filters_ok:
    st.stop()

models_ph    = ",".join(f'"{m}"' for m in sel_models)
practices_ph = ",".join(f'"{p}"' for p in sel_practices)

# ── tabs ──────────────────────────────────────────────────────────────────────
tab_overview, tab_trends, tab_models, tab_tools, tab_users, tab_errors = st.tabs(
    ["📊 Overview", "📈 Trends", "🤖 Models", "🔧 Tools", "👥 Users", "🚨 Errors"]
)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 – OVERVIEW
# ═════════════════════════════════════════════════════════════════════════════
with tab_overview:
    st.subheader("Executive Overview")

    _kpi_defaults = {"total_requests": 0, "total_cost": 0.0, "input_M": 0.0,
                     "output_M": 0.0, "cache_read_B": 0.0, "avg_latency_s": 0.0}
    kpi = safe_row(qry(db_path, f"""
        SELECT
            COUNT(*) AS total_requests,
            ROUND(SUM(CAST(`attributes.cost_usd` AS REAL)),2) AS total_cost,
            ROUND(SUM(CAST(`attributes.input_tokens` AS REAL))/1e6,2) AS input_M,
            ROUND(SUM(CAST(`attributes.output_tokens` AS REAL))/1e6,2) AS output_M,
            ROUND(SUM(CAST(`attributes.cache_read_tokens` AS REAL))/1e9,2) AS cache_read_B,
            ROUND(AVG(CAST(`attributes.duration_ms` AS REAL))/1000,2) AS avg_latency_s
        FROM api_requests
        WHERE `attributes.model` IN ({models_ph})
    """), _kpi_defaults)

    err = safe_row(qry(db_path, f"""
        SELECT COUNT(*) AS errors FROM api_errors
        WHERE `attributes.model` IN ({models_ph})
    """), {"errors": 0}).get("errors", 0)

    error_rate = round(100 * int(err) / max(int(kpi["total_requests"]), 1), 2)

    active = safe_row(qry(db_path, f"""
        SELECT COUNT(DISTINCT `attributes.user.id`) AS users,
               COUNT(DISTINCT `attributes.session.id`) AS sessions
        FROM events
        WHERE date(`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
    """), {"users": 0, "sessions": 0})

    st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-tile">
                <div class="kpi-icon">📨</div>
                <div class="kpi-label">Total Requests</div>
                <div class="kpi-value">{int(kpi['total_requests']):,}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">💰</div>
                <div class="kpi-label">Total Cost (USD)</div>
                <div class="kpi-value">${kpi['total_cost']:,.2f}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">⚠️</div>
                <div class="kpi-label">Error Rate</div>
                <div class="kpi-value">{error_rate}%</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">⏱️</div>
                <div class="kpi-label">Avg Latency</div>
                <div class="kpi-value">{kpi['avg_latency_s']} s</div>
            </div>
        </div>
        <div class="kpi-grid">
            <div class="kpi-tile">
                <div class="kpi-icon">📥</div>
                <div class="kpi-label">Input Tokens (M)</div>
                <div class="kpi-value">{kpi['input_M']:,.2f}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">📤</div>
                <div class="kpi-label">Output Tokens (M)</div>
                <div class="kpi-value">{kpi['output_M']:,.2f}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">👥</div>
                <div class="kpi-label">Active Users</div>
                <div class="kpi-value">{int(active['users'])}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">🔗</div>
                <div class="kpi-label">Active Sessions</div>
                <div class="kpi-value">{int(active['sessions']):,}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### Cost share by model")
        cost_m = qry(db_path, f"""
            SELECT `attributes.model` AS model,
                   ROUND(SUM(CAST(`attributes.cost_usd` AS REAL)),2) AS cost_usd
            FROM api_requests
            WHERE `attributes.model` IN ({models_ph})
            GROUP BY 1 ORDER BY cost_usd DESC
        """)
        fig = px.pie(cost_m, names="model", values="cost_usd",
                     color_discrete_sequence=px.colors.sequential.Oranges_r, hole=0.45)
        fig.update_traces(textposition="inside", textinfo="percent+label",
                          hovertemplate="<b>%{label}</b><br>Cost: $%{value:,.2f}<br>Share: %{percent}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("#### Token breakdown")
        tok = {
            "Input": float(kpi["input_M"]),
            "Output": float(kpi["output_M"]),
            "Cache read (B)": float(kpi["cache_read_B"]),
        }
        fig2 = px.bar(
            x=list(tok.keys()), y=list(tok.values()),
            labels={"x": "Token type", "y": "Volume"},
            color=list(tok.keys()),
            color_discrete_sequence=["#CF7650","#B96443","#8B4513"],
        )
        fig2.update_layout(showlegend=False)
        fig2.update_traces(hovertemplate="<b>%{x}</b><br>Volume: %{y:,.2f}<extra></extra>")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Tool decision summary")
    td = qry(db_path, """
        SELECT `attributes.tool_name` AS tool,
               SUM(CASE WHEN lower(`attributes.decision`)='accept' THEN 1 ELSE 0 END) AS accepted,
               SUM(CASE WHEN lower(`attributes.decision`)='reject' THEN 1 ELSE 0 END) AS rejected
        FROM tool_decisions
        GROUP BY 1 ORDER BY accepted DESC LIMIT 15
    """)
    fig3 = px.bar(td, x="tool", y=["accepted","rejected"], barmode="stack",
                  color_discrete_map={"accepted":"#CF7650","rejected":"#888"},
                  labels={"value":"Count","variable":"Decision","tool":"Tool",
                          "accepted":"Accepted","rejected":"Rejected"})
    fig3.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:,}<extra></extra>")
    st.plotly_chart(fig3, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 – TRENDS
# ═════════════════════════════════════════════════════════════════════════════
with tab_trends:
    st.subheader("Time Trends")

    daily_events = qry(db_path, f"""
        SELECT date(`attributes.event.timestamp`) AS day,
               COUNT(*) AS events,
               COUNT(DISTINCT `attributes.user.id`) AS active_users,
               COUNT(DISTINCT `attributes.session.id`) AS active_sessions
        FROM events
        WHERE date(`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
        GROUP BY 1 ORDER BY 1
    """)

    # ── forecast helper ───────────────────────────────────────────────────────
    def build_forecast(df, date_col, value_col, horizon=7):
        """Linear regression forecast for the next `horizon` days.
        Returns (forecast_dates, forecast_values) as lists, or ([], []) if
        there is insufficient data.
        """
        if df is None or len(df) < 4:
            return [], []
        import numpy as np
        dates = pd.to_datetime(df[date_col])
        x = (dates - dates.min()).dt.days.values.astype(float)
        y = df[value_col].values.astype(float)
        coeffs = np.polyfit(x, y, 1)          # degree-1 linear fit
        last_x = x[-1]
        future_x = np.arange(last_x + 1, last_x + horizon + 1)
        future_vals = np.polyval(coeffs, future_x)
        future_vals = np.maximum(future_vals, 0)   # no negative predictions
        last_date = dates.max()
        future_dates = [
            (last_date + datetime.timedelta(days=int(i))).strftime("%Y-%m-%d")
            for i in range(1, horizon + 1)
        ]
        return future_dates, future_vals.tolist()

    # ── Daily Events + 7-day forecast ─────────────────────────────────────────
    fc_dates, fc_vals = build_forecast(daily_events, "day", "events")

    fig = px.line(daily_events, x="day", y="events",
                  title="Daily Events — with 7-Day Forecast",
                  markers=True, color_discrete_sequence=["#CF7650"],
                  labels={"day": "Date", "events": "Total Events"})
    fig.update_traces(
        name="Actual",
        hovertemplate="<b>%{x}</b><br>Events: %{y:,}<extra>Actual</extra>"
    )
    if fc_dates:
        # connect the last actual point to the first forecast point for continuity
        join_dates = [daily_events["day"].iloc[-1]] + fc_dates
        join_vals  = [float(daily_events["events"].iloc[-1])] + fc_vals
        fig.add_trace(go.Scatter(
            x=join_dates, y=join_vals,
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#E8956D", dash="dash", width=2),
            marker=dict(symbol="circle-open", size=7),
            hovertemplate="<b>%{x}</b><br>Forecast: %{y:,.0f}<extra>Forecast</extra>",
        ))
        fig.add_vrect(
            x0=fc_dates[0], x1=fc_dates[-1],
            fillcolor="rgba(207,118,80,0.07)", line_width=0,
            annotation_text="Forecast zone", annotation_position="top left",
            annotation_font_color="#CF7650",
        )
    st.plotly_chart(fig, use_container_width=True)

    # ── Forecast KPI tiles ────────────────────────────────────────────────────
    if fc_dates:
        avg_fc   = sum(fc_vals) / len(fc_vals)
        total_fc = sum(fc_vals)
        trend    = fc_vals[-1] - fc_vals[0]
        trend_arrow = "▲" if trend >= 0 else "▼"
        trend_color = "#4CAF50" if trend >= 0 else "#D9534F"
        st.markdown(f"""
            <div class="kpi-grid-3" style="margin-top:4px;margin-bottom:16px;">
                <div class="kpi-tile">
                    <div class="kpi-icon">🔮</div>
                    <div class="kpi-label">Forecast Total (7d)</div>
                    <div class="kpi-value">{int(total_fc):,}</div>
                </div>
                <div class="kpi-tile">
                    <div class="kpi-icon">📅</div>
                    <div class="kpi-label">Forecast Daily Avg</div>
                    <div class="kpi-value">{avg_fc:,.0f}</div>
                </div>
                <div class="kpi-tile">
                    <div class="kpi-icon">{trend_arrow}</div>
                    <div class="kpi-label">Trend (day 1 → 7)</div>
                    <div class="kpi-value" style="color:{trend_color};">{trend_arrow} {abs(trend):,.0f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col_l, col_r = st.columns(2)

    # ── Daily Active Users + forecast ─────────────────────────────────────────
    with col_l:
        fc_u_dates, fc_u_vals = build_forecast(daily_events, "day", "active_users")
        fig2 = px.line(daily_events, x="day", y="active_users",
                       title="Daily Active Users — 7-Day Forecast", markers=True,
                       color_discrete_sequence=["#B96443"],
                       labels={"day": "Date", "active_users": "Active Users"})
        fig2.update_traces(
            name="Actual",
            hovertemplate="<b>%{x}</b><br>Active Users: %{y:,}<extra>Actual</extra>"
        )
        if fc_u_dates:
            join_u = [daily_events["day"].iloc[-1]] + fc_u_dates
            join_uv = [float(daily_events["active_users"].iloc[-1])] + fc_u_vals
            fig2.add_trace(go.Scatter(
                x=join_u, y=join_uv, mode="lines+markers", name="Forecast",
                line=dict(color="#E8956D", dash="dash", width=2),
                marker=dict(symbol="circle-open", size=7),
                hovertemplate="<b>%{x}</b><br>Forecast: %{y:,.0f}<extra>Forecast</extra>",
            ))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Daily Active Sessions + forecast ──────────────────────────────────────
    with col_r:
        fc_s_dates, fc_s_vals = build_forecast(daily_events, "day", "active_sessions")
        fig3 = px.line(daily_events, x="day", y="active_sessions",
                       title="Daily Active Sessions — 7-Day Forecast", markers=True,
                       color_discrete_sequence=["#8B4513"],
                       labels={"day": "Date", "active_sessions": "Active Sessions"})
        fig3.update_traces(
            name="Actual",
            hovertemplate="<b>%{x}</b><br>Active Sessions: %{y:,}<extra>Actual</extra>"
        )
        if fc_s_dates:
            join_s = [daily_events["day"].iloc[-1]] + fc_s_dates
            join_sv = [float(daily_events["active_sessions"].iloc[-1])] + fc_s_vals
            fig3.add_trace(go.Scatter(
                x=join_s, y=join_sv, mode="lines+markers", name="Forecast",
                line=dict(color="#E8956D", dash="dash", width=2),
                marker=dict(symbol="circle-open", size=7),
                hovertemplate="<b>%{x}</b><br>Forecast: %{y:,.0f}<extra>Forecast</extra>",
            ))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Daily API requests")
    daily_req = qry(db_path, f"""
        SELECT date(e.`attributes.event.timestamp`) AS day,
               COUNT(DISTINCT e.log_id) AS events
        FROM events e
        WHERE e.`attributes.event.name`='api_request'
          AND date(e.`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
        GROUP BY 1 ORDER BY 1
    """)
    fig4 = px.bar(daily_req, x="day", y="events",
                  color_discrete_sequence=["#CF7650"],
                  labels={"events":"Requests","day":"Date"})
    fig4.update_traces(hovertemplate="<b>%{x}</b><br>Requests: %{y:,}<extra></extra>")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Daily error count")
    daily_err = qry(db_path, f"""
        SELECT date(e.`attributes.event.timestamp`) AS day, COUNT(*) AS errors
        FROM events e
        WHERE e.`attributes.event.name`='api_error'
          AND date(e.`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
        GROUP BY 1 ORDER BY 1
    """)
    fig5 = px.bar(daily_err, x="day", y="errors",
                  color_discrete_sequence=["#D9534F"],
                  labels={"errors":"Errors","day":"Date"})
    fig5.update_traces(hovertemplate="<b>%{x}</b><br>Errors: %{y:,}<extra></extra>")
    st.plotly_chart(fig5, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 – MODELS
# ═════════════════════════════════════════════════════════════════════════════
with tab_models:
    st.subheader("Model Performance & Cost")

    model_stats = qry(db_path, f"""
        SELECT `attributes.model` AS model,
               COUNT(*) AS requests,
               ROUND(SUM(CAST(`attributes.cost_usd` AS REAL)),2) AS cost_usd,
               ROUND(AVG(CAST(`attributes.duration_ms` AS REAL))/1000,2) AS avg_latency_s,
               ROUND(AVG(CAST(`attributes.input_tokens` AS REAL)),0) AS avg_input_tok,
               ROUND(AVG(CAST(`attributes.output_tokens` AS REAL)),0) AS avg_output_tok
        FROM api_requests
        WHERE `attributes.model` IN ({models_ph})
        GROUP BY 1 ORDER BY requests DESC
    """)

    model_err = qry(db_path, f"""
        SELECT `attributes.model` AS model, COUNT(*) AS errors
        FROM api_errors
        WHERE `attributes.model` IN ({models_ph})
        GROUP BY 1
    """)

    model_df = model_stats.merge(model_err, on="model", how="left").fillna(0)
    model_df["error_rate_pct"] = (model_df["errors"] / model_df["requests"] * 100).round(2)

    show_table(model_df, rename={
        "model": "Model",
        "requests": "Requests",
        "cost_usd": "Cost (USD)",
        "avg_latency_s": "Avg Latency (s)",
        "avg_input_tok": "Avg Input Tokens",
        "avg_output_tok": "Avg Output Tokens",
        "errors": "Errors",
        "error_rate_pct": "Error Rate (%)",
    })
    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        fig = px.bar(model_df.sort_values("cost_usd", ascending=True),
                     x="cost_usd", y="model", orientation="h",
                     title="Total Cost by Model (USD)",
                     color="cost_usd", color_continuous_scale="Oranges",
                     labels={"cost_usd":"Cost (USD)","model":"Model"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Cost: $%{x:,.2f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = px.bar(model_df.sort_values("avg_latency_s", ascending=True),
                      x="avg_latency_s", y="model", orientation="h",
                      title="Avg Latency by Model (s)",
                      color="avg_latency_s", color_continuous_scale="Reds",
                      labels={"avg_latency_s":"Avg Latency (s)","model":"Model"})
        fig2.update_traces(hovertemplate="<b>%{y}</b><br>Avg Latency: %{x:.2f}s<extra></extra>")
        st.plotly_chart(fig2, use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        fig3 = px.bar(model_df, x="model", y=["avg_input_tok","avg_output_tok"],
                      barmode="group", title="Avg Tokens per Request",
                      color_discrete_map={"avg_input_tok":"#CF7650","avg_output_tok":"#B96443"},
                      labels={"value":"Tokens","variable":"Token Type","model":"Model",
                              "avg_input_tok":"Input Tokens","avg_output_tok":"Output Tokens"})
        fig3.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:,.0f}<extra></extra>")
        st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        fig4 = px.bar(model_df.sort_values("error_rate_pct", ascending=False),
                      x="model", y="error_rate_pct",
                      title="Error Rate by Model (%)",
                      color_discrete_sequence=["#D9534F"],
                      labels={"error_rate_pct":"Error Rate (%)","model":"Model"})
        fig4.update_traces(hovertemplate="<b>%{x}</b><br>Error Rate: %{y:.2f}%<extra></extra>")
        st.plotly_chart(fig4, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 – TOOLS
# ═════════════════════════════════════════════════════════════════════════════
with tab_tools:
    st.subheader("Tool Usage & Effectiveness")

    tool_stats = qry(db_path, """
        SELECT `attributes.tool_name` AS tool,
               COUNT(*) AS runs,
               SUM(CASE WHEN lower(`attributes.success`)='true' THEN 1 ELSE 0 END) AS success,
               ROUND(100.0*SUM(CASE WHEN lower(`attributes.success`)='true' THEN 1 ELSE 0 END)/COUNT(*),2) AS success_rate,
               ROUND(AVG(CAST(`attributes.duration_ms` AS REAL))/1000,2) AS avg_latency_s,
               ROUND(MAX(CAST(`attributes.duration_ms` AS REAL))/1000,2) AS max_latency_s,
               ROUND(AVG(CAST(`attributes.tool_result_size_bytes` AS REAL))/1024,2) AS avg_size_kb
        FROM tool_results
        GROUP BY 1 ORDER BY runs DESC
    """)

    show_table(tool_stats, rename={
        "tool": "Tool",
        "runs": "Runs",
        "success": "Successes",
        "success_rate": "Success Rate (%)",
        "avg_latency_s": "Avg Latency (s)",
        "max_latency_s": "Max Latency (s)",
        "avg_size_kb": "Avg Result Size (KB)",
    })
    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        fig = px.bar(tool_stats.sort_values("runs", ascending=True).tail(15),
                     x="runs", y="tool", orientation="h",
                     title="Tool Runs (Top 15)",
                     color="runs", color_continuous_scale="Oranges",
                     labels={"runs":"Runs","tool":"Tool"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Runs: %{x:,}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = px.bar(tool_stats.sort_values("success_rate"),
                      x="success_rate", y="tool", orientation="h",
                      title="Tool Success Rate (%)",
                      color="success_rate", color_continuous_scale="RdYlGn",
                      range_color=[80, 100],
                      labels={"success_rate":"Success Rate (%)","tool":"Tool"})
        fig2.update_traces(hovertemplate="<b>%{y}</b><br>Success Rate: %{x:.1f}%<extra></extra>")
        st.plotly_chart(fig2, use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        lat = tool_stats[tool_stats["avg_latency_s"] > 0].sort_values("avg_latency_s", ascending=False)
        fig3 = px.bar(lat, x="tool", y="avg_latency_s",
                      title="Avg Latency by Tool (s)",
                      color="avg_latency_s", color_continuous_scale="Reds",
                      labels={"avg_latency_s":"Avg Latency (s)","tool":"Tool"})
        fig3.update_traces(hovertemplate="<b>%{x}</b><br>Avg Latency: %{y:.2f}s<extra></extra>")
        st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        sz = tool_stats[tool_stats["avg_size_kb"] > 0].sort_values("avg_size_kb", ascending=False)
        fig4 = px.bar(sz, x="tool", y="avg_size_kb",
                      title="Avg Result Size by Tool (KB)",
                      color_discrete_sequence=["#CF7650"],
                      labels={"avg_size_kb":"Avg Size (KB)","tool":"Tool"})
        fig4.update_traces(hovertemplate="<b>%{x}</b><br>Avg Size: %{y:,.2f} KB<extra></extra>")
        st.plotly_chart(fig4, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 5 – USERS
# ═════════════════════════════════════════════════════════════════════════════
with tab_users:
    st.subheader("User Analytics")

    practice_act = qry(db_path, f"""
        SELECT u.user_practice AS practice,
               COUNT(*) AS events,
               COUNT(DISTINCT e.`attributes.user.id`) AS active_users,
               ROUND(1.0*COUNT(*)/COUNT(DISTINCT e.`attributes.user.id`),1) AS events_per_user
        FROM events e
        JOIN users u ON e.`attributes.user.id` = u.user_id
        WHERE date(e.`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
          AND u.user_practice IN ({practices_ph})
        GROUP BY 1 ORDER BY events DESC
    """)

    level_act = qry(db_path, f"""
        SELECT u.user_level AS level,
               COUNT(*) AS events,
               COUNT(DISTINCT e.`attributes.user.id`) AS active_users,
               ROUND(1.0*COUNT(*)/COUNT(DISTINCT e.`attributes.user.id`),1) AS events_per_user
        FROM events e
        JOIN users u ON e.`attributes.user.id` = u.user_id
        WHERE date(e.`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
          AND u.user_practice IN ({practices_ph})
        GROUP BY 1 ORDER BY events DESC
    """)

    top_users = qry(db_path, f"""
        SELECT u.user_email AS user,
               u.user_practice AS practice,
               u.user_level AS level,
               u.user_location AS location,
               COUNT(*) AS events
        FROM events e
        JOIN users u ON e.`attributes.user.id` = u.user_id
        WHERE date(e.`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
          AND u.user_practice IN ({practices_ph})
        GROUP BY 1,2,3,4
        ORDER BY events DESC
        LIMIT 20
    """)

    col_l, col_r = st.columns(2)
    with col_l:
        fig = px.bar(practice_act, x="practice", y="events",
                     title="Events by Practice",
                     color="events", color_continuous_scale="Oranges",
                     labels={"events":"Total Events","practice":"Practice"})
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Events: %{y:,}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = px.bar(practice_act, x="practice", y="events_per_user",
                      title="Events per User by Practice",
                      color_discrete_sequence=["#CF7650"],
                      labels={"events_per_user":"Events / User","practice":"Practice"})
        fig2.update_traces(hovertemplate="<b>%{x}</b><br>Events/User: %{y:.1f}<extra></extra>")
        st.plotly_chart(fig2, use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        fig3 = px.bar(level_act.sort_values("level"), x="level", y="events",
                      title="Events by Level",
                      color="events", color_continuous_scale="Oranges",
                      labels={"events":"Total Events","level":"Level"})
        fig3.update_traces(hovertemplate="<b>%{x}</b><br>Events: %{y:,}<extra></extra>")
        st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        fig4 = px.pie(practice_act, names="practice", values="active_users",
                      title="Active Users by Practice",
                      color_discrete_sequence=px.colors.sequential.Oranges_r, hole=0.4)
        fig4.update_traces(hovertemplate="<b>%{label}</b><br>Users: %{value:,}<br>Share: %{percent}<extra></extra>")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Top 20 most active users")
    show_table(top_users, rename={
        "user": "User",
        "practice": "Practice",
        "level": "Level",
        "location": "Location",
        "events": "Total Events",
    })

    st.markdown("#### Prompt length distribution")
    prompts = qry(db_path, """
        SELECT CAST(`attributes.prompt_length` AS INTEGER) AS prompt_length
        FROM user_prompts
        WHERE CAST(`attributes.prompt_length` AS INTEGER) < 5000
    """)
    fig5 = px.histogram(prompts, x="prompt_length", nbins=60,
                        title="Prompt Length Distribution (< 5000 chars)",
                        color_discrete_sequence=["#CF7650"],
                        labels={"prompt_length":"Prompt Length (chars)"})
    fig5.update_traces(hovertemplate="Length: %{x}<br>Count: %{y:,}<extra></extra>")
    st.plotly_chart(fig5, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 6 – ERRORS
# ═════════════════════════════════════════════════════════════════════════════
with tab_errors:
    st.subheader("Error Analytics")

    err_kpi = safe_row(qry(db_path, f"""
        SELECT COUNT(*) AS total_errors,
               COUNT(DISTINCT `attributes.model`) AS affected_models
        FROM api_errors
        WHERE `attributes.model` IN ({models_ph})
    """), {"total_errors": 0, "affected_models": 0})

    total_req_for_rate = safe_row(qry(db_path, f"""
        SELECT COUNT(*) AS n FROM api_requests
        WHERE `attributes.model` IN ({models_ph})
    """), {"n": 0}).get("n", 0)

    st.markdown(f"""
        <div class="kpi-grid-3">
            <div class="kpi-tile">
                <div class="kpi-icon">🚨</div>
                <div class="kpi-label">Total Errors</div>
                <div class="kpi-value">{int(err_kpi['total_errors']):,}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">🤖</div>
                <div class="kpi-label">Affected Models</div>
                <div class="kpi-value">{int(err_kpi['affected_models'])}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-icon">📉</div>
                <div class="kpi-label">Error Rate</div>
                <div class="kpi-value">{round(100*int(err_kpi['total_errors'])/max(total_req_for_rate,1),2)}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        err_status = qry(db_path, f"""
            SELECT `attributes.status_code` AS status_code, COUNT(*) AS n
            FROM api_errors
            WHERE `attributes.model` IN ({models_ph})
            GROUP BY 1 ORDER BY n DESC
        """)
        fig = px.bar(err_status, x="status_code", y="n",
                     title="Errors by Status Code",
                     color="n", color_continuous_scale="Reds",
                     labels={"n":"Count","status_code":"HTTP Status"})
        fig.update_traces(hovertemplate="<b>HTTP %{x}</b><br>Count: %{y:,}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        err_model = qry(db_path, f"""
            SELECT `attributes.model` AS model, COUNT(*) AS errors
            FROM api_errors
            WHERE `attributes.model` IN ({models_ph})
            GROUP BY 1 ORDER BY errors DESC
        """)
        fig2 = px.bar(err_model, x="model", y="errors",
                      title="Errors by Model",
                      color_discrete_sequence=["#D9534F"],
                      labels={"errors":"Error Count","model":"Model"})
        fig2.update_traces(hovertemplate="<b>%{x}</b><br>Errors: %{y:,}<extra></extra>")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Daily error trend")
    daily_err2 = qry(db_path, f"""
        SELECT date(e.`attributes.event.timestamp`) AS day, COUNT(*) AS errors
        FROM events e
        WHERE e.`attributes.event.name`='api_error'
          AND date(e.`attributes.event.timestamp`) BETWEEN '{d_from_s}' AND '{d_to_s}'
        GROUP BY 1 ORDER BY 1
    """)
    fig3 = px.area(daily_err2, x="day", y="errors",
                   title="Daily Error Count",
                   color_discrete_sequence=["#D9534F"],
                   labels={"errors":"Errors","day":"Date"})
    fig3.update_traces(hovertemplate="<b>%{x}</b><br>Errors: %{y:,}<extra></extra>")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Error attempt distribution")
    err_attempt = qry(db_path, f"""
        SELECT `attributes.attempt` AS attempt, COUNT(*) AS n
        FROM api_errors
        WHERE `attributes.model` IN ({models_ph})
        GROUP BY 1 ORDER BY attempt
    """)
    fig4 = px.bar(err_attempt, x="attempt", y="n",
                  title="Errors by Attempt Number",
                  color_discrete_sequence=["#CF7650"],
                  labels={"n":"Count","attempt":"Attempt #"})
    fig4.update_traces(hovertemplate="<b>Attempt %{x}</b><br>Count: %{y:,}<extra></extra>")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Top error messages")
    err_msg = qry(db_path, f"""
        SELECT `attributes.error` AS error_msg, COUNT(*) AS n
        FROM api_errors
        WHERE `attributes.model` IN ({models_ph})
        GROUP BY 1 ORDER BY n DESC LIMIT 15
    """)
    show_table(err_msg, rename={"error_msg": "Error Message", "n": "Count"})
