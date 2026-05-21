"""
theme_css.py
Centralised CSS for app.py.
Exports one function: inject_theme_css()
All colours use CSS custom-properties that adapt to Streamlit's light / dark mode
automatically — no hardcoded hex in HTML strings needed.
"""

THEME_CSS = """
<style>
/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   DESIGN TOKENS  —  Streamlit sets [data-theme] on <html>.
   Light is the default; dark overrides follow.
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

:root,
[data-theme="light"] {
  /* surfaces */
  --surface-base:     #F7F8FC;
  --surface-card:     #FFFFFF;
  --surface-muted:    #F8FAFC;
  --surface-subtle:   #F1F5F9;
  --surface-input:    #FFFFFF;
  --surface-filter:   #F8FAFC;
  --surface-totals:   #F1F5F9;
  --surface-grandtot: #0F172A;

  /* borders */
  --border-default:   #E2E8F0;
  --border-muted:     #CBD5E1;

  /* text */
  --text-primary:     #0F172A;
  --text-secondary:   #1E293B;
  --text-muted:       #475569;
  --text-faint:       #94A3B8;
  --text-grandtot:    #94A3B8;

  /* row striping in dataframe */
  --row-even:         #F8FAFC;
  --row-odd:          #FFFFFF;
}

[data-theme="dark"] {
  --surface-base:     #0E1117;
  --surface-card:     #1E2130;
  --surface-muted:    #262B3D;
  --surface-subtle:   #1A1F2E;
  --surface-input:    #1E2130;
  --surface-filter:   #1A1F2E;
  --surface-totals:   #262B3D;
  --surface-grandtot: #0B0F1A;

  --border-default:   #2D3148;
  --border-muted:     #3D4460;

  --text-primary:     #F1F5F9;
  --text-secondary:   #CBD5E1;
  --text-muted:       #94A3B8;
  --text-faint:       #64748B;
  --text-grandtot:    #64748B;

  --row-even:         #1A1F2E;
  --row-odd:          #1E2130;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   GLOBAL RESETS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
}

.stApp { background: var(--surface-base) !important; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   SIDEBAR  (always dark — intentional brand choice, unchanged)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
section[data-testid="stSidebar"] {
  background: #0F172A !important;
  border-right: 1px solid #1E293B !important;
  min-width: 220px !important;
  max-width: 260px !important;
}
section[data-testid="stSidebar"] * { color: #94A3B8 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #F1F5F9 !important; }

section[data-testid="stSidebar"] div[role="radiogroup"] > label {
  background: transparent !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  margin-bottom: 2px !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  transition: all 0.15s ease !important;
  cursor: pointer !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
  background: #1E293B !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: #2563EB !important;
  border-radius: 10px !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) * {
  color: #FFFFFF !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
  font-size: 13px !important;
  font-weight: 500 !important;
  white-space: nowrap !important;
  overflow: hidden;
  text-overflow: ellipsis;
}
section[data-testid="stSidebar"] .stButton button {
  background: #2563EB !important;
  color: white !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  border: none !important;
  width: 100% !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
  background: #1D4ED8 !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   METRIC CARDS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
[data-testid="stMetricValue"] {
  font-size: 24px !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted) !important;
}
[data-testid="metric-container"] {
  background: var(--surface-card) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 14px;
  padding: 18px 20px !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
  transition: box-shadow 0.2s;
}
[data-testid="metric-container"]:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,.08);
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   TABS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
button[data-baseweb="tab"] {
  font-weight: 600 !important;
  font-size: 13px !important;
  color: var(--text-muted) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: #2563EB !important;
  border-bottom-color: #2563EB !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   EXPANDER
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
[data-testid="stExpander"] {
  background: var(--surface-card) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 12px !important;
  margin-bottom: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
[data-testid="stExpander"] summary {
  font-weight: 600;
  font-size: 13px;
  padding: 14px 18px !important;
  color: var(--text-secondary) !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   DATAFRAME
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border-default) !important;
  border-radius: 12px;
  overflow: hidden;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   BUTTONS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.stButton button {
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  transition: all 0.15s !important;
}
.stButton button[kind="primary"] {
  background: #2563EB !important;
  border: none !important;
  color: white !important;
}
.stButton button[kind="primary"]:hover {
  background: #1D4ED8 !important;
  box-shadow: 0 4px 12px rgba(37,99,235,.35) !important;
  transform: translateY(-1px) !important;
}
.stButton button[kind="primary"],
.stButton button[kind="primary"] *,
.stDownloadButton > button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
}

.stDownloadButton > button span,
.stDownloadButton > button div,
.stDownloadButton > button p {
    color: #FFFFFF !important;
}

.stDownloadButton > button:hover {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   INPUTS  — use token so they flip automatically
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
[data-testid="stFileUploader"] {
  background: var(--surface-muted);
  border: 1.5px dashed var(--border-muted);
  border-radius: 10px;
  padding: 6px;
  transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #2563EB; }

input[type="number"],
input[type="text"],
textarea {
  background: var(--surface-input) !important;
  border: 1.5px solid var(--border-default) !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  color: var(--text-primary) !important;
}
input:focus, textarea:focus {
  border-color: #2563EB !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,.12) !important;
}

/* Streamlit native text inputs */
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
  background: var(--surface-input) !important;
  border-color: var(--border-default) !important;
}
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
  background: var(--surface-input) !important;
  color: var(--text-primary) !important;
}
[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder {
  color: var(--text-faint) !important;
}

[data-testid="stSelectbox"] > div > div {
  background: var(--surface-input) !important;
  border: 1.5px solid var(--border-default) !important;
  border-radius: 8px !important;
  color: var(--text-primary) !important;
}
[data-testid="stMultiSelect"] > div {
  border-radius: 8px !important;
  border: 1.5px solid var(--border-default) !important;
  background: var(--surface-input) !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   SCROLLBAR
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-muted); border-radius: 4px; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   TYPOGRAPHY
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
h1 {
  font-weight: 800 !important;
  letter-spacing: -0.5px !important;
  font-size: 26px !important;
  color: var(--text-primary) !important;
}
h2, h3 {
  font-weight: 700 !important;
  color: var(--text-secondary) !important;
}
p { color: var(--text-muted) !important; }
.stCaption {
    font-size: 12px !important;
    color: white !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ALERT / INFO
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   SLIDER
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
[data-testid="stSlider"] > div > div > div { background: #2563EB !important; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   THEME-AWARE UTILITY CLASSES
   Used by the inline HTML blocks in app.py via class= on divs/spans.
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/* Card containers */
.th-card {
  background: var(--surface-card);
  border: 1px solid var(--border-default);
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.th-card-muted {
  background: var(--surface-muted);
  border: 1px solid var(--border-default);
  border-radius: 12px;
}
.th-filter-panel {
  background: var(--surface-card);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.th-filter-cell {
  background: var(--surface-filter);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
}
.th-totals-bar {
  background: var(--surface-totals);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 10px;
}
.th-grand-bar {
  background: var(--surface-grandtot);
  border-radius: 10px;
  padding: 14px 18px;
  margin-top: 4px;
  margin-bottom: 16px;
}

/* Text utilities */
.th-text-primary   { color: var(--text-primary)   !important; }
.th-text-secondary { color: var(--text-secondary) !important; }
.th-text-muted     { color: var(--text-muted)     !important; }
.th-text-faint     { color: var(--text-faint)     !important; }
.th-text-grandtot  { color: var(--text-grandtot)  !important; }

/* Divider */
.th-divider {
  height: 1px;
  background: var(--border-default);
  margin: 20px 0;
}

/* KPI card */
.th-kpi {
  background: var(--surface-card);
  border-radius: 14px;
  padding: 16px 18px;
  border: 1px solid var(--border-default);
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
  transition: box-shadow 0.2s;
}
.th-kpi-label {
  font-size: 10px;
  color: var(--text-faint);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: 6px;
}
.th-kpi-bar {
  width: 28px;
  height: 3px;
  border-radius: 2px;
  margin-top: 8px;
  opacity: 0.4;
}

/* Section header accent bar */
.th-section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 20px 0 14px;
}
.th-section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.th-section-sub {
  font-size: 11px;
  color: var(--text-faint);
  margin-top: 2px;
}

/* Upload source card */
.th-source-card {
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 8px;

  /* Fix inconsistent upload card height */
  min-height: 90px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}
.th-source-title {
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.th-source-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 3px;
  line-height: 1.4;

  min-height: 36px;   /* reserve equal text area */
}
/* Operator/value filter cell label */
.th-filter-label {
  font-size: 10px;
  color: var(--text-faint);
  margin-bottom: 2px;
}
.th-filter-metric-title {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .07em;
  margin-bottom: 8px;
}

/* Empty state */
.th-empty {
  background: var(--surface-card);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
}

/* Badge / pill */
.th-badge-ready {
  background: #ECFDF5;
  border: 1.5px solid #059669;
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 700;
  color: #059669;
  margin: 2px;
}

/* Page header */
.th-page-header {
  padding: 4px 0 20px;
}
.th-page-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}
.th-page-sub {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}
.metric-help {
    color: #0F172A !important;
    font-size: 11px !important;
    font-weight: 500 !important;
}
</style>
"""


def inject_theme_css():
    import streamlit as st # type: ignore
    st.markdown(THEME_CSS, unsafe_allow_html=True)
