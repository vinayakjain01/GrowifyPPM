# ╔══════════════════════════════════════════════════════════════════════╗
# ║  app.py  —  Brand Analysis Tool  (modular, v9)                     ║
# ║  Sections:                                                          ║
# ║    0 · Overall View    (Meta + Shopify + Google merged)            ║
# ║    1 · Discount Analysis                                            ║
# ║    2 · Quadrant View   (4-Quadrant + AI Insights)                  ║
# ║                                                                     ║
# ║  Modules:                                                           ║
# ║    data_cleaner.py  — raw → clean transformation                   ║
# ║    cleaning_ui.py   — upload + diff UI component                   ║
# ║    analytics.py     — merge & analysis engines                     ║
# ║    charts.py        — Plotly chart builders                        ║
# ║    ai_insights.py   — Gemini AI + insight renderer                 ║
# ║    excel_export.py  — Excel workbook builders                      ║
# ╚══════════════════════════════════════════════════════════════════════╝

import streamlit as st
import pandas as pd
import numpy as np

# ── Module imports ────────────────────────────────────────────────────
from cleaning_ui  import render_upload_panel, render_clean_preview
from analytics    import (
    run_overall_view, run_discount_analysis, run_product_analysis,
    compact_currency, fmt_inr, fmt_roi, fmt_pct, make_month_label,
    parse_month_start,
)
from charts       import make_combo_chart, make_share_chart
from ai_insights  import (
    prepare_full_ai_data, generate_overall_ai_insights, render_ai_insights,
)
from excel_export import build_s1_excel


# ══════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Product Performance Marketing",
    layout="wide",
    page_icon="📊",
)

# ── Global Styles ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

.stApp { background: #F4F6FB; }
section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
section[data-testid="stSidebar"] * { color: #1E293B !important; }
section[data-testid="stSidebar"] .stButton button {
    background: #2563EB !important; color: white !important;
    border-radius: 8px !important; font-weight: 600 !important;
}

div[data-testid="stRadio"] label {
    background: #F1F5F9; border: 1.5px solid #E2E8F0; border-radius: 999px;
    padding: 5px 18px; font-size: 13px; font-weight: 600; color: #475569;
    cursor: pointer; transition: all .18s;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #2563EB; border-color: #2563EB; color: white !important;
}

[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; color: #1E293B !important; }
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #64748B !important; font-weight: 500 !important; }
[data-testid="metric-container"] {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 16px 20px !important; box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

button[data-baseweb="tab"] { font-weight: 600 !important; font-size: 13px !important; color: #64748B !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: #2563EB !important; border-bottom-color: #2563EB !important; }

[data-testid="stExpander"] {
    background: #FFFFFF; border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important; margin-bottom: 8px;
}
[data-testid="stExpander"] summary { font-weight: 600; color: #1E293B; font-size: 13px; }

[data-testid="stDataFrame"] { border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; }

.stButton button { border-radius: 8px !important; font-weight: 600 !important; font-size: 13px !important; }
.stButton button[kind="primary"] { background: #2563EB !important; border: none !important; }
.stButton button[kind="primary"]:hover { background: #1D4ED8 !important; }

[data-testid="stFileUploader"] {
    background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 10px; padding: 8px;
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }

h1 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.5px !important; }
h2, h3 { color: #1E293B !important; font-weight: 600 !important; }
p { color: #475569 !important; }
.stCaption { color: #94A3B8 !important; font-size: 12px !important; }

input[type="number"] { background: #FFFFFF; border: 1px solid #E2E8F0 !important; border-radius: 6px !important; }
[data-testid="stSelectbox"] > div > div { background: #FFFFFF; border: 1px solid #E2E8F0 !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  UI COMPONENT HELPERS
# ══════════════════════════════════════════════════════════════════════

def section_header(title, subtitle="", accent="#2563EB"):
    st.markdown(f"""
    <div style="background:#FFFFFF;border-radius:12px;padding:18px 22px;
                border-left:4px solid {accent};margin-bottom:20px;
                box-shadow:0 1px 4px rgba(0,0,0,.06)">
      <div style="font-size:16px;font-weight:700;color:#0F172A">{title}</div>
      {'<div style="font-size:12px;color:#64748B;margin-top:3px">'+subtitle+'</div>' if subtitle else ''}
    </div>""", unsafe_allow_html=True)


def kpi_row(items):
    cols = st.columns(len(items))
    for col, (label, value, color, bg) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div style="background:{bg};border-radius:10px;padding:14px 16px;
                        border:1px solid {color}33;text-align:center">
              <div style="font-size:11px;color:#64748B;font-weight:500;text-transform:uppercase;
                          letter-spacing:.06em;margin-bottom:4px">{label}</div>
              <div style="font-size:22px;font-weight:700;color:{color}">{value}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  OVERALL VIEW COLUMN DEFINITIONS  (extended with CTR, CPM, Variant)
# ══════════════════════════════════════════════════════════════════════

_OV_COLS = {
    "Meta Spend":         {"label": "Meta Spend (₹)",    "fmt": "currency", "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "Google Cost":        {"label": "Google Cost (₹)",   "fmt": "currency", "source": "Google",  "color": "#D97706", "bg": "#FFF7ED"},
    "Total Spend":        {"label": "Total Spend (₹)",   "fmt": "currency", "source": "Derived", "color": "#7C3AED", "bg": "#F5F3FF"},
    "Shopify Revenue":    {"label": "Revenue (₹)",       "fmt": "currency", "source": "Shopify", "color": "#059669", "bg": "#ECFDF5"},
    "ROI":                {"label": "ROI",               "fmt": "roi",      "source": "Derived", "color": "#059669", "bg": "#ECFDF5"},
    "Net Items Sold":     {"label": "Items Sold",        "fmt": "int",      "source": "Shopify", "color": "#0F172A", "bg": "#F8FAFC"},
    "Landing Page Views": {"label": "LPV",               "fmt": "int",      "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "Conversions":        {"label": "Conversions",       "fmt": "int",      "source": "Google",  "color": "#D97706", "bg": "#FFF7ED"},
    "CTR":                {"label": "CTR",               "fmt": "pct",      "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "CPM":                {"label": "CPM (₹)",           "fmt": "currency", "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "Variant Title":      {"label": "Variant Title",     "fmt": "text",     "source": "Shopify", "color": "#059669", "bg": "#ECFDF5"},
    "Month":              {"label": "Month",             "fmt": "text",     "source": "All",     "color": "#64748B", "bg": "#F8FAFC"},
}


def _fmt_val(v, fmt):
    if fmt == "currency": return f"₹{v:,.0f}"
    if fmt == "roi":      return f"{v:.2f}x"
    if fmt == "int":      return f"{int(v):,}"
    if fmt == "pct":      return f"{float(v)*100:.2f}%"
    return str(v)


# ════════════════════════════════════════════════════════════════════
#  SECTION 0 — OVERALL VIEW
# ══════════════════════════════════════════════════════════════════════

def render_overall_view():
    st.title("🌐 Overall View")
    # st.caption("Upload raw exports — the tool auto-cleans and merges Meta, Shopify, and Google data.")

    # ── Upload + auto-clean panel ─────────────────────────────────
    section_header(
        "📤 Upload Raw Exports",
        "Drop your unmodified platform exports",
        "#2563EB",
    )

    cleaned = render_upload_panel("ov", show_google=True, google_optional=True)

    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    run_ov = st.button("▶ Merge & Analyse", type="primary", key="btn_run_ov")

    if run_ov:
        if not cleaned["ready"]:
            st.error("Please upload at least Meta and Shopify files before running.")
            return
        with st.spinner("Merging data sources…"):
            try:
                merged_df, has_month = run_overall_view(
                    cleaned["meta_df"],
                    cleaned["shopify_df"],
                    cleaned["google_df"],   # None if not uploaded
                )
                st.session_state["ov_data"]      = merged_df
                st.session_state["ov_has_month"] = has_month
                st.session_state["ov_has_google"] = cleaned["google_df"] is not None
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
                return

    if "ov_data" not in st.session_state:
        # Show clean preview if files are loaded but not yet merged
        if cleaned["ready"]:
            render_clean_preview(cleaned)
        else:
            st.info("👆 Upload Meta + Shopify files (Google is optional) then click **Merge & Analyse**.")
        return

    # Show clean preview in an expander
    render_clean_preview(cleaned)

    df        = st.session_state["ov_data"].copy()
    has_month = st.session_state["ov_has_month"]
    has_google = st.session_state.get("ov_has_google", False)

    # ── Top KPIs ──────────────────────────────────────────────────
    total_meta   = df["Meta Spend"].sum()    if "Meta Spend"      in df.columns else 0
    total_google = df["Google Cost"].sum()   if "Google Cost"     in df.columns else 0
    total_spend  = df["Total Spend"].sum()   if "Total Spend"     in df.columns else 0
    total_rev    = df["Shopify Revenue"].sum() if "Shopify Revenue" in df.columns else 0
    overall_roi  = total_rev / total_spend if total_spend else 0

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    kpi_row([
        ("Total Products",  df["Product ID"].nunique(),           "#0F172A", "#F8FAFC"),
        ("Meta Spend",      compact_currency(total_meta),         "#2563EB", "#EFF6FF"),
        ("Google Cost",     compact_currency(total_google),       "#D97706", "#FFF7ED"),
        ("Total Spend",     compact_currency(total_spend),        "#7C3AED", "#F5F3FF"),
        ("Shopify Revenue", compact_currency(total_rev),          "#059669", "#ECFDF5"),
        ("Overall ROI",     f"{overall_roi:.2f}x",
         "#059669" if overall_roi >= 1 else "#DC2626",
         "#ECFDF5" if overall_roi >= 1 else "#FEF2F2"),
    ])
    st.markdown("<div style='margin:16px 0'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Column selector ───────────────────────────────────────────
    section_header("📋 Select Columns & Filters",
                   "Choose which columns to display → filters appear automatically", "#2563EB")

    # Build available columns
    available_cols = [c for c in _OV_COLS.keys() if c in df.columns]
    if not has_month and "Month" in available_cols:
        available_cols.remove("Month")
    if not has_google:
        available_cols = [c for c in available_cols if c not in ("Google Cost", "Conversions")]

    # default_selected = [
    #     c for c in ["Meta Spend", "Google Cost", "Total Spend",
    #                  "Shopify Revenue", "ROI", "Net Items Sold", "CTR", "CPM"]
    #     if c in available_cols
    # ]
    default_selected = [
        c for c in ["Meta Spend", "Google Cost", "Total Spend",
                     "Shopify Revenue", "ROI", "Net Items Sold", "CTR", "CPM", "Variant Title"]
        if c in available_cols
    ]

    # Source legend
    # source_pills = ""
    # for src, col_hex in [("Meta","#2563EB"),("Shopify","#059669"),("Google","#D97706"),("Derived","#7C3AED")]:
    #     source_pills += f"""<span style="display:inline-flex;align-items:center;gap:4px;
    #         background:{col_hex}11;border:1px solid {col_hex}44;border-radius:999px;
    #         padding:2px 10px;font-size:11px;color:{col_hex};font-weight:600;margin:2px">
    #         {src}</span>"""
    # st.markdown(f"""
    # <div style="background:#FFFFFF;border-radius:12px;padding:14px 18px;
    #             border:1px solid #E2E8F0;margin-bottom:12px">
    #   <div style="font-size:13px;font-weight:700;color:#1E293B;margin-bottom:8px">
    #     📌 Choose columns to display and filter
    #   </div>
    #   <div style="margin-bottom:10px">{source_pills}</div>
    # </div>""", unsafe_allow_html=True)

    col_options = list(available_cols)
    col_labels  = [f"{_OV_COLS.get(c,{}).get('label',c)}  [{_OV_COLS.get(c,{}).get('source','?')}]"
                   for c in col_options]
    label_to_key = {lbl: key for key, lbl in zip(col_options, col_labels)}

    selected_labels = st.multiselect(
        "Select columns",
        options=col_labels,
        default=[col_labels[col_options.index(c)] for c in default_selected if c in col_options],
        label_visibility="collapsed",
        key="ov_col_sel",
        placeholder="Choose columns to display and filter…",
    )
    selected_cols = [label_to_key[lbl] for lbl in selected_labels]

    if not selected_cols:
        st.info("👆 Select at least one column above to begin filtering.")
        return

    # ── Dynamic per-column filters ────────────────────────────────
    st.markdown("""
    <div style="background:#FFFFFF;border-radius:12px;padding:18px 20px;
                border:1px solid #E2E8F0;margin-bottom:16px">
      <div style="font-size:13px;font-weight:700;color:#1E293B;margin-bottom:14px">
        🔍 Filters — one per selected column
      </div>""", unsafe_allow_html=True)

    s1, s2 = st.columns([3, 2])
    with s1:
        st.markdown("<div style='font-size:12px;font-weight:600;color:#475569;margin-bottom:3px'>Product Title / ID Search</div>", unsafe_allow_html=True)
        search_text = st.text_input("Search", placeholder="e.g. T-Shirt, 12345…",
                                    label_visibility="collapsed", key="ov_search")
    with s2:
        if has_month and "Month" in df.columns:
            months_avail = sorted(df["Month"].dropna().unique().tolist())
            st.markdown("<div style='font-size:12px;font-weight:600;color:#475569;margin-bottom:3px'>Month</div>", unsafe_allow_html=True)
            sel_months = st.multiselect("Month", months_avail, default=months_avail,
                                        label_visibility="collapsed", key="ov_months")
        else:
            sel_months = None

    st.markdown("<div style='margin:10px 0 4px'></div>", unsafe_allow_html=True)

    filter_specs = {}
    num_fmts = ("currency", "int", "roi", "pct")
    num_cols  = [c for c in selected_cols if _OV_COLS.get(c, {}).get("fmt") in num_fmts]
    text_cols = [c for c in selected_cols
                 if _OV_COLS.get(c, {}).get("fmt") == "text"
                 and c not in ("Month", "Variant Title")]

    if num_cols:
        for i in range(0, len(num_cols), 3):
            chunk = num_cols[i:i+3]
            row_cols = st.columns(len(chunk))
            for rc, col_key in zip(row_cols, chunk):
                meta_info = _OV_COLS[col_key]
                col_min   = float(df[col_key].min()) if col_key in df.columns else 0.0
                col_max   = float(df[col_key].max()) if col_key in df.columns else 100.0
                fmt_str   = "%.4f" if meta_info["fmt"] == "pct" else "%.2f" if meta_info["fmt"] == "roi" else "%.0f"
                step      = 0.0001 if meta_info["fmt"] == "pct" else 0.01 if meta_info["fmt"] == "roi" else 1.0
                with rc:
                    st.markdown(f"""<div style="background:{meta_info['bg']};border-radius:8px;
                        padding:10px 12px;border:1px solid {meta_info['color']}33;margin-bottom:4px">
                        <div style="font-size:11px;font-weight:700;color:{meta_info['color']};
                                    text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px">
                        {meta_info['label']}</div>""", unsafe_allow_html=True)
                    st.markdown("<div style='font-size:11px;color:#64748B;margin-bottom:2px'>Min</div>", unsafe_allow_html=True)
                    mn_val = st.number_input(f"min_{col_key}", min_value=col_min, max_value=col_max,
                                             value=col_min, step=step, format=fmt_str,
                                             label_visibility="collapsed", key=f"ov_min_{col_key}")
                    st.markdown("<div style='font-size:11px;color:#64748B;margin-bottom:2px'>Max</div>", unsafe_allow_html=True)
                    mx_val = st.number_input(f"max_{col_key}", min_value=col_min, max_value=col_max,
                                             value=col_max, step=step, format=fmt_str,
                                             label_visibility="collapsed", key=f"ov_max_{col_key}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    filter_specs[col_key] = (mn_val, mx_val)

    if text_cols:
        for col_key in text_cols:
            meta_info = _OV_COLS[col_key]
            uniq = sorted(df[col_key].dropna().unique().tolist()) if col_key in df.columns else []
            if uniq:
                st.markdown(f"<div style='font-size:12px;font-weight:600;color:{meta_info['color']};margin-bottom:3px'>{meta_info['label']}</div>", unsafe_allow_html=True)
                sel_vals = st.multiselect(f"filter_{col_key}", uniq, default=uniq,
                                          label_visibility="collapsed", key=f"ov_txt_{col_key}")
                filter_specs[col_key] = ("text", sel_vals)

    # Variant title filter (special — text search not multiselect)
    if "Variant Title" in selected_cols and "Variant Title" in df.columns:
        st.markdown("<div style='font-size:12px;font-weight:600;color:#059669;margin-bottom:3px'>Variant Title search</div>", unsafe_allow_html=True)
        variant_search = st.text_input("Variant search", placeholder="e.g. XL, M, Blue…",
                                        label_visibility="collapsed", key="ov_variant_search")
    else:
        variant_search = ""

    rst_col1, rst_col2 = st.columns([5, 1])
    with rst_col2:
        if st.button("↺ Reset", key="ov_reset"):
            keys_to_del = ["ov_search", "ov_months", "ov_col_sel", "ov_variant_search"]
            for c in available_cols:
                keys_to_del += [f"ov_min_{c}", f"ov_max_{c}", f"ov_txt_{c}"]
            for k in keys_to_del:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Apply filters ─────────────────────────────────────────────
    fdf = df.copy()

    if search_text.strip():
        q = search_text.strip().lower()
        fdf = fdf[
            fdf["Product Title"].str.lower().str.contains(q, na=False) |
            fdf["Product ID"].astype(str).str.lower().str.contains(q, na=False)
        ]

    if has_month and sel_months and "Month" in fdf.columns:
        fdf = fdf[fdf["Month"].isin(sel_months)]

    if variant_search.strip() and "Variant Title" in fdf.columns:
        fdf = fdf[fdf["Variant Title"].str.lower().str.contains(variant_search.strip().lower(), na=False)]

    for col_key, spec in filter_specs.items():
        if col_key not in fdf.columns:
            continue
        if spec[0] == "text":
            _, sel_vals = spec
            if sel_vals:
                fdf = fdf[fdf[col_key].isin(sel_vals)]
        else:
            mn_val, mx_val = spec
            fdf = fdf[(fdf[col_key] >= mn_val) & (fdf[col_key] <= mx_val)]

    # ── Result strip ──────────────────────────────────────────────
    n_shown    = len(fdf)
    n_total    = len(df)
    is_filtered = n_shown < n_total

    badge_color = "#2563EB" if not is_filtered else "#059669"
    badge_bg    = "#EFF6FF" if not is_filtered else "#ECFDF5"
    st.markdown(f"""
    <div style="background:{badge_bg};border:1px solid {badge_color}33;border-radius:8px;
                padding:8px 14px;display:inline-flex;align-items:center;gap:10px;margin-bottom:12px">
      <span style="font-size:13px;font-weight:700;color:{badge_color}">{n_shown:,} rows</span>
      <span style="font-size:12px;color:#64748B">
        {'showing all' if not is_filtered else f'filtered from {n_total:,} total'}
      </span>
      {'' if not is_filtered else '<span style="background:#DBEAFE;border-radius:999px;padding:2px 10px;font-size:11px;color:#1E40AF;font-weight:600">Filters active</span>'}
    </div>""", unsafe_allow_html=True)

    # Filtered KPIs
    if is_filtered and not fdf.empty:
        kpi_items = []
        for col_key in selected_cols:
            meta_info = _OV_COLS.get(col_key, {})
            if meta_info.get("fmt") in ("currency", "int") and col_key in fdf.columns:
                total_v = fdf[col_key].sum()
                kpi_items.append((
                    f"Total {meta_info['label']}", _fmt_val(total_v, meta_info["fmt"]),
                    meta_info["color"], meta_info["bg"],
                ))
            elif meta_info.get("fmt") == "roi" and col_key in fdf.columns:
                sp = fdf["Total Spend"].sum()    if "Total Spend"     in fdf.columns else 0
                rv = fdf["Shopify Revenue"].sum() if "Shopify Revenue" in fdf.columns else 0
                roi_v = rv / sp if sp else 0
                kpi_items.append(("Filtered ROI", f"{roi_v:.2f}x",
                                  "#059669" if roi_v >= 1 else "#DC2626",
                                  "#ECFDF5" if roi_v >= 1 else "#FEF2F2"))
        if kpi_items:
            kpi_row(kpi_items[:6])
            st.markdown("<div style='margin:10px 0'></div>", unsafe_allow_html=True)

    if fdf.empty:
        st.markdown("""
        <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;
                    padding:24px;text-align:center;color:#DC2626;font-weight:600;font-size:14px">
          No products match the current filters. Try adjusting the criteria above.
        </div>""", unsafe_allow_html=True)
        return

    # ── Build display table ───────────────────────────────────────
    always_cols = ["Product ID", "Product Title"]
    if "Variant Title" in fdf.columns:
        always_cols.append("Variant Title")
    if has_month and "Month" in selected_cols and "Month" in fdf.columns:
        always_cols.append("Month")

    disp = fdf[[c for c in always_cols if c in fdf.columns]].copy()
    display_col_map = {}

    for col_key in selected_cols:
        if col_key in always_cols or col_key not in fdf.columns:
            continue
        meta_info = _OV_COLS.get(col_key, {})
        disp_lbl  = meta_info.get("label", col_key)
        disp[disp_lbl] = fdf[col_key].apply(lambda v: _fmt_val(v, meta_info.get("fmt","text")))
        display_col_map[disp_lbl] = col_key

    disp_cols_data = [c for c in always_cols if c in disp.columns] + list(display_col_map.keys())

    # Totals
    totals_row = {c: ("∑ TOTAL" if c == "Product ID" else "") for c in always_cols}
    for disp_lbl, col_key in display_col_map.items():
        meta_info = _OV_COLS.get(col_key, {})
        fmt       = meta_info.get("fmt", "text")
        if fmt in ("currency", "int") and col_key in fdf.columns:
            totals_row[disp_lbl] = _fmt_val(fdf[col_key].sum(), fmt)
        elif fmt == "roi":
            sp = fdf["Total Spend"].sum()    if "Total Spend"     in fdf.columns else 0
            rv = fdf["Shopify Revenue"].sum() if "Shopify Revenue" in fdf.columns else 0
            totals_row[disp_lbl] = f"{rv/sp:.2f}x" if sp else "—"
        else:
            totals_row[disp_lbl] = ""

    # Totals banner
    totals_html = ""
    for disp_lbl, col_key in display_col_map.items():
        meta_info = _OV_COLS.get(col_key, {})
        val = totals_row.get(disp_lbl, "")
        if val and val != "":
            totals_html += f"""<span style="display:inline-flex;align-items:center;gap:4px;
                background:{meta_info['bg']};border:1px solid {meta_info['color']}33;
                border-radius:6px;padding:3px 10px;font-size:11px;margin:2px;
                color:{meta_info['color']};font-weight:700">
                {disp_lbl}: {val}</span>"""

    if totals_html:
        st.markdown(f"""
        <div style="background:#F8FAFC;border-radius:10px;padding:10px 14px;
                    border:1px solid #E2E8F0;margin-bottom:10px">
          <div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;
                      letter-spacing:.08em;margin-bottom:6px">∑ Totals for {n_shown:,} filtered rows</div>
          <div>{totals_html}</div>
        </div>""", unsafe_allow_html=True)

    st.dataframe(
        disp[disp_cols_data].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        height=520,
    )

    st.markdown(f"""
    <div style="background:#0F172A;border-radius:10px;padding:14px 18px;margin-top:4px;margin-bottom:16px">
      <div style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;
                  letter-spacing:.1em;margin-bottom:8px">∑ GRAND TOTALS — {n_shown:,} products</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">{totals_html}</div>
    </div>""", unsafe_allow_html=True)

    # ── Download ──────────────────────────────────────────────────
    dl1, dl2 = st.columns([2, 4])
    with dl1:
        export_cols = ["Product ID", "Product Title"]
        if has_month and "Month" in df.columns:
            export_cols.append("Month")
        for col_key in selected_cols:
            if col_key not in export_cols and col_key in fdf.columns:
                export_cols.append(col_key)
        export_df = fdf[export_cols].copy()
        csv_buf   = export_df.to_csv(index=False).encode("utf-8")
        col_names = ", ".join([_OV_COLS.get(c, {}).get("label", c) for c in selected_cols])
        st.download_button(
            label="⬇ Download Filtered Data (CSV)",
            data=csv_buf,
            file_name="overall_view_filtered.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    with dl2:
        st.markdown(f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                    padding:10px 14px;font-size:12px;color:#64748B">
          Exporting <strong style="color:#1E293B">{n_shown:,} rows</strong> with columns:<br>
          <strong style="color:#1E293B">{col_names}</strong>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  SECTION 1 — DISCOUNT ANALYSIS
# ══════════════════════════════════════════════════════════════════════

def insight_bucket_ui(itype, df_sec, key_prefix):
    CONF = {
        "hslr": {"icon": "🔴", "label": "High Spend · Low Revenue",
                 "tip": "Consuming budget with poor returns — review or pause",
                 "color": "#DC2626", "bg": "#FEF2F2", "border": "#FCA5A5"},
        "lshr": {"icon": "🟢", "label": "Low Spend · High Revenue",
                 "tip": "Highly efficient — consider scaling spend",
                 "color": "#059669", "bg": "#ECFDF5", "border": "#6EE7B7"},
    }
    c = CONF[itype]
    st.markdown(f"""
    <div style="background:{c['bg']};border:1.5px solid {c['border']};
                border-radius:12px;padding:14px 18px;margin-bottom:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:5px">
        <span style="font-size:18px">{c['icon']}</span>
        <span style="font-weight:700;color:{c['color']};font-size:14px">{c['label']}</span>
      </div>
      <div style="font-size:12px;color:#64748B">{c['tip']}</div>
    </div>""", unsafe_allow_html=True)

    if df_sec.empty:
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                    padding:12px 16px;color:#94A3B8;font-size:13px;text-align:center;margin-bottom:12px">
          No products match this criteria
        </div>""", unsafe_allow_html=True)
        return

    t_sp  = df_sec["Spend"].sum()
    t_rv  = df_sec["Revenue"].sum()
    t_roi = round(t_rv / t_sp, 2) if t_sp else 0

    kpi_row([
        ("Products",  len(df_sec),              c["color"], c["bg"]),
        ("Spend",     compact_currency(t_sp),   "#64748B",  "#F8FAFC"),
        ("Revenue",   compact_currency(t_rv),   "#059669",  "#ECFDF5"),
        ("ROI",       fmt_roi(t_roi),           c["color"], c["bg"]),
    ])

    with st.expander(f"📋 View {len(df_sec)} products"):
        disp = df_sec.copy()
        disp["Spend"]   = disp["Spend"].apply(fmt_inr)
        disp["Revenue"] = disp["Revenue"].apply(fmt_inr)
        disp["ROI"]     = disp["ROI"].apply(fmt_roi)
        disp = disp.rename(columns={"Product ID": "PID", "Product Title": "Title",
                                    "Spend": "Spend (INR)", "Revenue": "Revenue (INR)"})
        st.dataframe(disp, use_container_width=True, hide_index=True)


def render_discount_view():
    st.title("📋 Discount vs Non-Discount Analysis")
    st.caption("Compare discounted and non-discounted product performance across months.")

    # ── Sidebar state ─────────────────────────────────────────────
    run_s1    = st.session_state.get("_run_s1",    False)
    spend_pct = st.session_state.get("s1_sp",      100)
    rev_pct   = st.session_state.get("s1_rv",      100)
    brand_name = st.session_state.get("brand_name", "Brand")

    # ── Upload panel ──────────────────────────────────────────────
    section_header("📤 Upload Raw Exports", "Meta + Shopify are required · Discount list is the 3rd file", "#2563EB")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""...""", unsafe_allow_html=True)
        meta_file = st.file_uploader("Meta CSV", type=["csv","xlsx"], key="s1_meta",
                                      label_visibility="collapsed")
        # ✅ Save bytes immediately
        if meta_file is not None:
            st.session_state["s1_meta_bytes"] = meta_file.read()
            st.session_state["s1_meta_name"]  = meta_file.name
            meta_file.seek(0)

    with col2:
        st.markdown("""...""", unsafe_allow_html=True)
        shopify_file = st.file_uploader("Shopify CSV", type=["csv","xlsx"], key="s1_shop",
                                         label_visibility="collapsed")
        # ✅ Save bytes immediately
        if shopify_file is not None:
            st.session_state["s1_shopify_bytes"] = shopify_file.read()
            st.session_state["s1_shopify_name"]  = shopify_file.name
            shopify_file.seek(0)

    with col3:
        st.markdown("""...""", unsafe_allow_html=True)
        discount_file = st.file_uploader("Discount list", type=["csv","xlsx"], key="s1_disc",
                                          label_visibility="collapsed")
        # ✅ Save bytes immediately
        if discount_file is not None:
            st.session_state["s1_disc_bytes"] = discount_file.read()
            st.session_state["s1_disc_name"]  = discount_file.name
            discount_file.seek(0)

    if run_s1:
        # ✅ Read from session_state instead of file objects
        meta_bytes    = st.session_state.get("s1_meta_bytes")
        shopify_bytes = st.session_state.get("s1_shopify_bytes")
        disc_bytes    = st.session_state.get("s1_disc_bytes")

        if not meta_bytes or not shopify_bytes or not disc_bytes:
            st.error("Upload all 3 files to run.")
            st.session_state["_run_s1"] = False
            st.stop()

        with st.spinner("Cleaning and processing data…"):
            try:
                import io
                from data_cleaner import clean_meta, clean_shopify, _read_file

                # Reconstruct file-like objects
                meta_io    = io.BytesIO(meta_bytes);    meta_io.name    = st.session_state["s1_meta_name"]
                shopify_io = io.BytesIO(shopify_bytes); shopify_io.name = st.session_state["s1_shopify_name"]
                disc_io    = io.BytesIO(disc_bytes);    disc_io.name    = st.session_state["s1_disc_name"]

                meta_df,    meta_warns  = clean_meta(meta_io)
                shopify_df, shop_warns  = clean_shopify(shopify_io)

                # Discount list
                disc_name = st.session_state["s1_disc_name"]
                if disc_name.lower().endswith((".xlsx", ".xls")):
                    disc_df = pd.read_excel(disc_io)
                else:
                    disc_df = pd.read_csv(disc_io)

                if "Product ID" not in disc_df.columns:
                    pid_alt = next((c for c in disc_df.columns
                                   if "id" in c.lower() or "sku" in c.lower()), disc_df.columns[0])
                    disc_df = disc_df.rename(columns={pid_alt: "Product ID"})

                (results_df, months_ordered, merged,
                 insights, overall_insights, title_map) = run_discount_analysis(
                    meta_df, shopify_df, disc_df, spend_pct, rev_pct
                )
                st.session_state.update({
                    "s1_results":          results_df,
                    "s1_months":           months_ordered,
                    "s1_merged":           merged,
                    "s1_insights":         insights,
                    "s1_overall_insights": overall_insights,
                })
                for w in meta_warns + shop_warns:
                    st.warning(w)
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
                st.stop()
        st.session_state["_run_s1"] = False
    if "s1_results" not in st.session_state:
        st.info("👈 Upload 3 files and click **Run Discount Analysis** in the sidebar.")
        st.stop()

    results_df       = st.session_state["s1_results"]
    months_ordered   = st.session_state["s1_months"]
    merged           = st.session_state["s1_merged"]
    insights         = st.session_state["s1_insights"]
    overall_insights = st.session_state["s1_overall_insights"]

    st.success(f"✅ {len(months_ordered)} month(s) loaded: {', '.join(months_ordered)}")
    st.markdown("")
    kpi_row([
        ("Total Products",  merged["Product ID"].nunique(),                                "#0F172A", "#F8FAFC"),
        ("Discounted",      merged[merged["Is_Discounted"]]["Product ID"].nunique(),       "#2563EB", "#EFF6FF"),
        ("Non-Discounted",  merged[~merged["Is_Discounted"]]["Product ID"].nunique(),      "#059669", "#ECFDF5"),
        ("Overall ROI",     fmt_roi(merged["Revenue"].sum()/merged["Spend"].sum())
                            if merged["Spend"].sum() else "—",                             "#7C3AED", "#F5F3FF"),
    ])
    st.markdown("")
    st.markdown("---")

    # Timeline filter
    selected_months = st.multiselect("Months", months_ordered, default=months_ordered,
                                     key="s1_timeline")
    active_months  = selected_months if selected_months else months_ordered
    active_results = results_df[results_df["Month"].isin(active_months)]

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊  Summary · Charts", "🔍  Product Insights", "⬇  Download"])

    with tab1:
        view_mode = st.radio("View", ["📋 Table / Matrix", "📈 Charts"],
                             horizontal=True, label_visibility="collapsed", key="s1_view")
        if view_mode == "📋 Table / Matrix":
            section_header("Monthly Summary Matrix", "Spend, Revenue, ROI by category per month", "#2563EB")
            for month in active_months:
                md = active_results[active_results["Month"] == month].copy()
                if md.empty:
                    continue
                st.markdown(f"""<div style="background:#2563EB;border-radius:6px;padding:3px 12px;
                    font-size:12px;font-weight:700;color:white;display:inline-block;
                    margin:14px 0 8px">{month}</div>""", unsafe_allow_html=True)
                disp = md[["Category","Spend","Revenue","Spend_Pct","Revenue_Pct","ROI"]].copy()
                disp.columns = ["Category","Spend (INR)","Revenue (INR)","Spend %","Revenue %","ROI"]
                disp["Spend (INR)"]   = disp["Spend (INR)"].apply(fmt_inr)
                disp["Revenue (INR)"] = disp["Revenue (INR)"].apply(fmt_inr)
                disp["Spend %"]       = disp["Spend %"].apply(fmt_pct)
                disp["Revenue %"]     = disp["Revenue %"].apply(fmt_pct)
                disp["ROI"]           = disp["ROI"].apply(fmt_roi)
                st.dataframe(disp.set_index("Category"), use_container_width=True)
        else:
            section_header("Performance Charts", "Visual comparison across months", "#059669")
            st.plotly_chart(make_combo_chart(active_results, active_months), use_container_width=True)
            st.caption("🔵 Blue = Spend  ·  🟢 Green = Revenue  ·  🟡 Line = ROI (right axis)")
            st.markdown("<div style='margin:16px 0 6px'></div>", unsafe_allow_html=True)
            st.plotly_chart(make_share_chart(active_results, active_months), use_container_width=True)

    with tab2:
        analysis_mode = st.radio("Mode",
                                  ["📅 Monthly Analysis", "🌐 Full Analysis (Overall)"],
                                  horizontal=True, key="s1_mode",
                                  label_visibility="collapsed")
        cat_key    = "s1_cat_monthly" if analysis_mode == "📅 Monthly Analysis" else "s1_cat_overall"
        cat_choice = st.radio("Category", ["Discounted", "Non-Discounted"],
                              horizontal=True, key=cat_key)
        cat_color  = "#2563EB" if cat_choice == "Discounted" else "#059669"
        st.markdown(f"""<div style="background:{'#EFF6FF' if cat_choice=='Discounted' else '#ECFDF5'};
            border-radius:8px;padding:7px 14px;display:inline-block;margin-bottom:16px;
            border:1.5px solid {cat_color}33">
            <span style="font-size:12px;font-weight:700;color:{cat_color}">
            {'🏷 Discounted Products' if cat_choice=='Discounted' else '🔓 Non-Discounted Products'}
            </span></div>""", unsafe_allow_html=True)

        if analysis_mode == "📅 Monthly Analysis":
            for month in active_months:
                st.markdown(f"""<div style="background:#FFFFFF;border-radius:10px;
                    padding:11px 16px;margin:18px 0 10px;border-left:4px solid {cat_color};
                    box-shadow:0 1px 4px rgba(0,0,0,.06)">
                    <div style="font-size:14px;font-weight:700;color:#0F172A">
                    📅 {month} · <span style="font-weight:400;font-size:12px;color:#64748B">{cat_choice}</span>
                    </div></div>""", unsafe_allow_html=True)
                ins    = insights.get((month, cat_choice), {})
                col_a, col_b = st.columns(2)
                with col_a:
                    insight_bucket_ui("hslr", ins.get("hslr", pd.DataFrame()), f"m_{month}_{cat_choice}_hslr")
                with col_b:
                    insight_bucket_ui("lshr", ins.get("lshr", pd.DataFrame()), f"m_{month}_{cat_choice}_lshr")
        else:
            ov = overall_insights.get(cat_choice, {})
            col_a, col_b = st.columns(2)
            with col_a:
                insight_bucket_ui("hslr", ov.get("hslr", pd.DataFrame()), f"ov_{cat_choice}_hslr")
            with col_b:
                insight_bucket_ui("lshr", ov.get("lshr", pd.DataFrame()), f"ov_{cat_choice}_lshr")

    with tab3:
        section_header("Download Excel Report", "Full analysis with monthly + overall insight sheets", "#7C3AED")
        excel_buf = build_s1_excel(active_results, active_months, insights, overall_insights)
        st.download_button(
            label=f"📥 Download {brand_name} Discount Analysis.xlsx",
            data=excel_buf,
            file_name=f"{brand_name}_discount_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )


# ══════════════════════════════════════════════════════════════════════
#  SECTION 2 — QUADRANT VIEW
# ══════════════════════════════════════════════════════════════════════

QUAD_CONFIG = {
    "q1": {"color":"#059669","bg":"#ECFDF5","border":"#6EE7B7","icon":"🚀","label":"High Potential"},
    "q2": {"color":"#2563EB","bg":"#EFF6FF","border":"#93C5FD","icon":"💎","label":"High Conversion"},
    "q3": {"color":"#DC2626","bg":"#FEF2F2","border":"#FCA5A5","icon":"⚠️","label":"Low Performing"},
    "q4": {"color":"#64748B","bg":"#F8FAFC","border":"#CBD5E1","icon":"🧟","label":"Zombie"},
}


def quadrant_card(qkey, df, desc):
    cfg = QUAD_CONFIG[qkey]
    n   = len(df)
    sp  = df["Spend"].sum()
    rv  = df["Revenue"].sum()
    roi = round(rv / sp, 2) if sp else 0

    st.markdown(f"""
    <div style="background:#FFFFFF;border-radius:14px;padding:20px 22px;
                border-left:5px solid {cfg['color']};margin-bottom:2px;
                box-shadow:0 1px 6px rgba(0,0,0,.08)">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px">
        <div>
          <div style="font-size:22px;margin-bottom:4px">{cfg['icon']}</div>
          <div style="font-size:16px;font-weight:700;color:#0F172A;margin-bottom:2px">{cfg['label']}</div>
          <div style="font-size:12px;color:#64748B">{desc}</div>
        </div>
        <div style="display:flex;gap:20px;flex-wrap:wrap">
          <div style="text-align:center">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px">Products</div>
            <div style="font-size:24px;font-weight:800;color:{cfg['color']}">{n}</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px">Spend</div>
            <div style="font-size:16px;font-weight:700;color:#1E293B">{compact_currency(sp)}</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px">Revenue</div>
            <div style="font-size:16px;font-weight:700;color:#1E293B">{compact_currency(rv)}</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px">ROI</div>
            <div style="font-size:24px;font-weight:800;color:{cfg['color']}">{roi:.2f}x</div>
          </div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    with st.expander(f"📋 View all {n} products in {cfg['label']}"):
        if df.empty:
            st.info("No products in this quadrant.")
        else:
            disp = df.copy()
            disp["Spend"]   = disp["Spend"].apply(fmt_inr)
            disp["Revenue"] = disp["Revenue"].apply(fmt_inr)
            disp["ROI"]     = disp["ROI"].apply(fmt_roi)
            st.dataframe(disp, use_container_width=True, hide_index=True)


def render_quadrant_view():
    st.title("🔲 Quadrant View")
    st.caption("Upload raw exports — auto-cleaned then split into 4 performance quadrants with AI insights.")

    run_s2       = st.session_state.get("_run_s2",  False)
    s2_spend_pct = st.session_state.get("s2_sp",    100)
    s2_rev_pct   = st.session_state.get("s2_rv",    100)

    # ── Upload panel (Meta + Shopify only) ───────────────────────
    section_header("📤 Upload Raw Exports", "Meta + Shopify exports — auto-cleaned", "#2563EB")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div style="background:#EFF6FF;border-radius:10px;padding:10px 14px;
            margin-bottom:8px;border-left:3px solid #2563EB">
            <div style="font-size:12px;font-weight:700;color:#2563EB">① Meta Ads</div>
            <div style="font-size:11px;color:#64748B;margin-top:3px">Raw export — auto-cleaned</div>
        </div>""", unsafe_allow_html=True)
        s2_meta_file = st.file_uploader("Meta CSV", type=["csv","xlsx"], key="s2_meta",
                                         label_visibility="collapsed")
        # ✅ ADD THIS: save bytes immediately on upload
        if s2_meta_file is not None:
            st.session_state["s2_meta_bytes"] = s2_meta_file.read()
            st.session_state["s2_meta_name"]  = s2_meta_file.name
            s2_meta_file.seek(0)
    
    with col2:
        st.markdown("""<div style="background:#ECFDF5;border-radius:10px;padding:10px 14px;
            margin-bottom:8px;border-left:3px solid #059669">
            <div style="font-size:12px;font-weight:700;color:#059669">② Shopify</div>
            <div style="font-size:11px;color:#64748B;margin-top:3px">Raw export — auto-cleaned</div>
        </div>""", unsafe_allow_html=True)
        s2_shopify_file = st.file_uploader("Shopify CSV", type=["csv","xlsx"], key="s2_shop",
                                            label_visibility="collapsed")
        # ✅ ADD THIS: save bytes immediately on upload
        if s2_shopify_file is not None:
            st.session_state["s2_shopify_bytes"] = s2_shopify_file.read()
            st.session_state["s2_shopify_name"]  = s2_shopify_file.name
            s2_shopify_file.seek(0)

    if run_s2:
        # ✅ REPLACE the old check with this:
        meta_bytes    = st.session_state.get("s2_meta_bytes")
        shopify_bytes = st.session_state.get("s2_shopify_bytes")
    
        if not meta_bytes or not shopify_bytes:
            st.error("Upload Meta and Shopify CSV files.")
            st.session_state["_run_s2"] = False
            st.stop()
    
        with st.spinner("Cleaning and analysing data…"):
            try:
                import io
                from data_cleaner import clean_meta, clean_shopify
    
                # Reconstruct BytesIO with the original filename for extension detection
                meta_io    = io.BytesIO(meta_bytes);    meta_io.name    = st.session_state["s2_meta_name"]
                shopify_io = io.BytesIO(shopify_bytes); shopify_io.name = st.session_state["s2_shopify_name"]
    
                meta_df,    meta_warns  = clean_meta(meta_io)
                shopify_df, shop_warns  = clean_shopify(shopify_io)
    
                data = run_product_analysis(meta_df, shopify_df, s2_spend_pct, s2_rev_pct)
                st.session_state.update({
                    "s2_data":   data,
                    "s2_sp_pct": s2_spend_pct,
                    "s2_rv_pct": s2_rev_pct,
                })
                if "s2_ai_insights" in st.session_state:
                    del st.session_state["s2_ai_insights"]
                for w in meta_warns + shop_warns:
                    st.warning(w)
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
                st.stop()
        st.session_state["_run_s2"] = False

    if "s2_data" not in st.session_state:
        st.info("👈 Upload Meta + Shopify files and click **Run Product Analysis** in the sidebar.")
        st.stop()

    data     = st.session_state["s2_data"]
    sp_cut   = data["sp_cut"]; rv_cut = data["rv_cut"]
    all_df   = data["all"];    monthly = data["monthly"]
    total_sp = all_df["Spend"].sum()
    total_rv = all_df["Revenue"].sum()

    kpi_row([
        ("Total Products", len(all_df),               "#0F172A", "#F8FAFC"),
        ("Total Spend",    compact_currency(total_sp), "#64748B", "#F8FAFC"),
        ("Total Revenue",  compact_currency(total_rv), "#059669", "#ECFDF5"),
        ("Overall ROI",    fmt_roi(total_rv/total_sp) if total_sp else "—", "#7C3AED", "#F5F3FF"),
    ])
    st.markdown("")

    st.markdown(f"""
    <div style="background:#FFFFFF;border-radius:10px;padding:12px 18px;margin:8px 0 20px;
                display:flex;flex-wrap:wrap;gap:20px;border:1px solid #E2E8F0;
                box-shadow:0 1px 4px rgba(0,0,0,.04)">
      <div style="font-size:12px;color:#64748B">
        <strong style="color:#1E293B">High Spend</strong> ≥ {compact_currency(sp_cut)}
        <span style="color:#2563EB;margin-left:4px">({st.session_state.get('s2_sp_pct',100)}% of avg)</span>
      </div>
      <div style="font-size:12px;color:#64748B">
        <strong style="color:#1E293B">High Revenue</strong> ≥ {compact_currency(rv_cut)}
        <span style="color:#2563EB;margin-left:4px">({st.session_state.get('s2_rv_pct',100)}% of avg)</span>
      </div>
      <div style="font-size:12px;color:#64748B">
        <strong style="color:#1E293B">Months in data:</strong>
        <span style="color:#7C3AED;margin-left:4px">{data['total_months']}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    section_header("Quadrant Breakdown",
                   "Products split into 4 groups by spend and revenue performance", "#2563EB")

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    with r1c1: quadrant_card("q1", data["q1"], "High Revenue · Low Spend — great ROI, underinvested")
    with r1c2: quadrant_card("q2", data["q2"], "High Revenue · High Spend — strong performers, worth the budget")
    with r2c1: quadrant_card("q4", data["q4"], "Low Revenue · Low Spend — minimal activity, assess or drop")
    with r2c2: quadrant_card("q3", data["q3"], "Low Revenue · High Spend — budget drain, review urgently")

    # ── AI Analysis ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="background:#FFFFFF;border-radius:14px;padding:22px 26px;
                border:2px solid #E2E8F0;margin-bottom:20px;
                box-shadow:0 2px 8px rgba(0,0,0,.06)">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <span style="font-size:28px">🤖</span>
        <div>
          <div style="font-size:18px;font-weight:800;color:#0F172A">Overall AI Analysis</div>
          <div style="font-size:12px;color:#64748B;margin-top:2px">
            Powered by <strong style="color:#7C3AED">Gemini 2.5 Flash</strong> ·
            Analyses all 4 quadrants in one comprehensive report
          </div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    col_btn, col_note = st.columns([2, 3])
    with col_btn:
        gen_clicked = st.button("✨ Generate Overall Analysis", type="primary",
                                use_container_width=True, key="btn_overall_ai")
    with col_note:
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                    padding:10px 14px;font-size:12px;color:#64748B">
          Sends full product data across all 4 quadrants to Gemini.<br>
          Results appear as <strong style="color:#1E293B">4 numbered dropdowns</strong> below.
        </div>""", unsafe_allow_html=True)

    if gen_clicked:
        with st.spinner("Preparing data and calling Gemini…"):
            ai_data = prepare_full_ai_data(
                data["q1"], data["q2"], data["q3"], data["q4"], monthly, all_df
            )
            ins_list, err = generate_overall_ai_insights(ai_data)
            st.session_state["s2_ai_insights"] = (ins_list, err)

    if "s2_ai_insights" in st.session_state:
        ins_list, err = st.session_state["s2_ai_insights"]
        if err:
            st.error(err)
        elif ins_list:
            st.markdown(f"""
            <div style="font-size:12px;color:#64748B;margin:12px 0 8px;
                        padding:8px 14px;background:#F8FAFC;border-radius:8px;border:1px solid #E2E8F0">
              ✅ {len(ins_list)} insights generated · click each dropdown to expand
            </div>""", unsafe_allow_html=True)
            render_ai_insights(ins_list)
        else:
            st.warning("No insights returned. Please try again.")


# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("growify_studio_logo.jpg", width=150)
    st.markdown("### 📊 Growify")
    st.markdown("""
    <div style="padding:4px 0 16px">
      <div style="font-size:12px;color:#94A3B8;margin-top:2px">Product Performance Marketing</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <style>
    
    /* Target sidebar radio buttons */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        min-height: 60px !important;   /* Equal height */
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        padding: 10px 15px !important;
        border-radius: 20px !important;
        margin-bottom: 10px !important;
    }
    
    /* Keep text on one line */
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        white-space: nowrap !important;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 16px;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    
    with st.sidebar:
        page = st.radio(
            "Section",
            [
                "🌐 Overall View",
                "🔲 Quadrant View",
                "📋 Discount Vs Non Discount Analysis"
            ],
            label_visibility="collapsed"
        )
    # page = st.radio("Section", [
    #     "🌐 Overall View",
    #     "🔲 Quadrant View",
    #     "📋 Discount Vs Non Discount Analysis",
    # ], label_visibility="collapsed")
    # st.markdown("---")

    if page == "📋 Discount Vs Non Discount Analysis":
        st.markdown("### ⚙️ Analysis Settings")
        brand_name = st.text_input("Brand Name", value="Brand", key="brand_name")
        st.markdown("**🎚 Insight Thresholds**")
        st.slider("High Spend threshold (%)",   50, 300, 100, 10, key="s1_sp")
        st.slider("Low Revenue threshold (%)",  10, 200, 100, 10, key="s1_rv")
        st.markdown("---")
        if st.button("▶ Run Discount Analysis", type="primary", use_container_width=True):
            st.session_state["_run_s1"] = True
            st.rerun()

    elif page == "🔲 Quadrant View":
        st.markdown("### ⚙️ Analysis Settings")
        st.markdown("**🎚 Quadrant Thresholds**")
        st.slider("High Spend threshold (%)",   50, 300, 100, 10, key="s2_sp")
        st.slider("High Revenue threshold (%)", 50, 300, 100, 10, key="s2_rv")
        st.markdown("---")
        if st.button("▶ Run Product Analysis", type="primary", use_container_width=True):
            st.session_state["_run_s2"] = True
            st.rerun()
    
    else:
        # st.markdown("### 📁 Upload 3 Files")
        # st.markdown("""Raw Exports
        # <div style="font-size:12px;color:#64748B;line-height:1.6;margin-bottom:8px">
        #   Upload in the main area →<br>
        #   Meta · Shopify · Google (optional)<br>
        #   Merged on <strong style="color:#1E293B">Product ID</strong>
        # </div>""", unsafe_allow_html=True)
        # st.markdown("""
        # <div style="background:#EFF6FF;border-radius:8px;padding:10px 12px;
        #             border-left:3px solid #2563EB;font-size:11px;color:#1E40AF;margin-bottom:8px">
        #   <strong>ROI:</strong> Revenue ÷ (Meta Spend + Google Cost)<br>
        # </div>""", unsafe_allow_html=True)

        # ── Avg KPIs in sidebar (only when data is available) ────
        if "ov_data" in st.session_state:
            _df = st.session_state["ov_data"]
            _has_google = st.session_state.get("ov_has_google", False)

            def _sb_kpi(label, value, color, bg):
                st.markdown(f"""
                <div style="background:{bg};border-radius:8px;padding:8px 10px;
                            border-left:3px solid {color};margin-bottom:6px">
                  <div style="font-size:10px;color:#64748B;font-weight:600;
                              text-transform:uppercase;letter-spacing:.06em">{label}</div>
                  <div style="font-size:15px;font-weight:700;color:{color};margin-top:2px">{value}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("<div style='font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px'>📊   Averages per Product</div>", unsafe_allow_html=True)

            n = _df["Product ID"].nunique() or 1

            if "Meta Spend" in _df.columns:
                avg_meta = _df["Meta Spend"].sum() / n
                _sb_kpi("Avg Meta Spend", f"₹{avg_meta:,.0f}", "#2563EB", "#EFF6FF")

            if _has_google and "Google Cost" in _df.columns:
                avg_google = _df["Google Cost"].sum() / n
                _sb_kpi("Avg Google Spend", f"₹{avg_google:,.0f}", "#D97706", "#FFF7ED")

            if "Total Spend" in _df.columns:
                avg_total = _df["Total Spend"].sum() / n
                _sb_kpi("Avg Total Spend", f"₹{avg_total:,.0f}", "#7C3AED", "#F5F3FF")

            if "Shopify Revenue" in _df.columns:
                avg_rev = _df["Shopify Revenue"].sum() / n
                _sb_kpi("Avg Revenue", f"₹{avg_rev:,.0f}", "#059669", "#ECFDF5")
    # else:
    #     st.markdown("### 📁 Upload 3 Files")
    #     st.markdown("""Raw Exports
    #     <div style="font-size:12px;color:#64748B;line-height:1.6;margin-bottom:8px">
    #       Upload in the main area →<br>
    #       Meta · Shopify · Google (optional)<br>
    #       Merged on <strong style="color:#1E293B">Product ID</strong>
    #     </div>""", unsafe_allow_html=True)
    #     st.markdown("""
    #     <div style="background:#EFF6FF;border-radius:8px;padding:10px 12px;
    #                 border-left:3px solid #2563EB;font-size:11px;color:#1E40AF;margin-bottom:8px">
    #       <strong>ROI:</strong> Revenue ÷ (Meta Spend + Google Cost)<br>
    #     </div>""", unsafe_allow_html=True)
        # st.markdown("""
        # <div style="background:#ECFDF5;border-radius:8px;padding:10px 12px;
        #             border-left:3px solid #059669;font-size:11px;color:#065F46">
        #   <strong>Auto-cleaning:</strong><br>
        #   ✓ Meta: splits Product ID + Title<br>
        #   ✓ Shopify: renames variant ID<br>
        #   ✓ Google: skips metadata rows, extracts numeric ID, converts month format
        # </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  ROUTE
# ══════════════════════════════════════════════════════════════════════

if page == "🌐 Overall View":
    render_overall_view()
elif page == "📋 Discount Vs Non Discount Analysis":
    render_discount_view()
else:
    render_quadrant_view() 