# ╔══════════════════════════════════════════════════════════════════════╗
# ║  app.py  —  Brand Analysis Tool  (modular, v11 — 3 fixes applied)  ║
# ║  Fix 1: User Guide opens PDF in browser (not download)             ║
# ║  Fix 2: Metric Filters support "Between" (min–max range)           ║
# ║  Fix 3: Uploaded files persist across page switches                ║
# ╚══════════════════════════════════════════════════════════════════════╝

import streamlit as st # type: ignore
import pandas as pd
import numpy as np
import datetime

from theme_css    import inject_theme_css
from cleaning_ui  import render_upload_panel, render_clean_preview
from analytics    import (
    run_overall_view, run_discount_analysis, run_product_analysis,
    compact_currency, fmt_inr, fmt_roi, fmt_pct,
    make_month_label, parse_month_start,
)
from charts       import make_combo_chart, make_share_chart
from ai_insights  import (
    prepare_full_ai_data, generate_overall_ai_insights, render_ai_insights,
)
from excel_export import build_s1_excel


# ══════════════════════════════════════════════════════════════════════
#  PAGE CONFIG + THEME
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Product Performance Marketing",
    layout="wide",
    page_icon="📊",
)
inject_theme_css()

# ── FIX 1: User Guide button — opens PDF inline in browser tab ────────
# We use Google Docs Viewer to render the PDF in-browser instead of
# triggering a file download.
_PDF_RAW_URL = "https://raw.githubusercontent.com/vinayakjain01/GrowifyPPM/main/Growify_PPM_User_Guide.pdf"
_PDF_VIEWER_URL = f"https://docs.google.com/viewer?url={_PDF_RAW_URL}&embedded=false"

st.markdown(f"""
<style>
.user-guide-btn {{
    position: fixed;
    top: 14px;
    right: 60px;
    z-index: 999999;
}}
.user-guide-btn a {{
    background: #1E293B;
    color: #F1F5F9 !important;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 8px;
    text-decoration: none;
    border: 1px solid #334155;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 0.15s;
}}
.user-guide-btn a:hover {{
    background: #2563EB;
    border-color: #2563EB;
}}
</style>
<div class="user-guide-btn">
  <a href="{_PDF_VIEWER_URL}" target="_blank">
    📖 User Guide
  </a>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  UI COMPONENT HELPERS
# ══════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = "", icon: str = ""):
    sub_html = f'<p class="th-page-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="th-page-header">'
        f'<div class="th-page-title">{icon} {title}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "", accent: str = "#2563EB"):
    sub_html = f'<div class="th-section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="th-section-header">'
        f'<div style="width:3px;height:20px;background:{accent};'
        f'border-radius:2px;flex-shrink:0"></div>'
        f'<div>'
        f'<div class="th-section-title">{title}</div>'
        f'{sub_html}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_row(items):
    cols = st.columns(len(items))
    for col, (label, value, color, _bg) in zip(cols, items):
        with col:
            st.markdown(
                f'<div class="th-kpi">'
                f'<div class="th-kpi-label">{label}</div>'
                f'<div style="font-size:22px;font-weight:800;color:{color};line-height:1.1">'
                f'{value}</div>'
                f'<div class="th-kpi-bar" style="background:{color}"></div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def divider():
    st.markdown('<div class="th-divider"></div>', unsafe_allow_html=True)


def upload_card(color: str, _bg: str, title: str, desc: str):
    st.markdown(
        f'<div class="th-source-card" '
        f'style="border-left:3px solid {color};background:{_bg};">'
        f'<div class="th-source-title" style="color:{color}">{title}</div>'
        f'<div class="th-source-desc">{desc}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════
#  OVERALL VIEW — COLUMN DEFINITIONS
# ══════════════════════════════════════════════════════════════════════

_OV_COLS = {
    "Meta Spend":         {"label": "Meta Spend (₹)",  "fmt": "currency", "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "Google Cost":        {"label": "Google Cost (₹)", "fmt": "currency", "source": "Google",  "color": "#D97706", "bg": "#FFF7ED"},
    "Total Spend":        {"label": "Total Spend (₹)", "fmt": "currency", "source": "Derived", "color": "#7C3AED", "bg": "#F5F3FF"},
    "Shopify Revenue":    {"label": "Revenue (₹)",     "fmt": "currency", "source": "Shopify", "color": "#059669", "bg": "#ECFDF5"},
    "ROI":                {"label": "ROI",             "fmt": "roi",      "source": "Derived", "color": "#059669", "bg": "#ECFDF5"},
    "Net Items Sold":     {"label": "Items Sold",      "fmt": "int",      "source": "Shopify", "color": "#0F172A", "bg": "#F8FAFC"},
    "Landing Page Views": {"label": "LPV",             "fmt": "int",      "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "Conversions":        {"label": "Conversions",     "fmt": "int",      "source": "Google",  "color": "#D97706", "bg": "#FFF7ED"},
    "CTR":                {"label": "CTR",             "fmt": "pct",      "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "CPM":                {"label": "CPM (₹)",         "fmt": "currency", "source": "Meta",    "color": "#2563EB", "bg": "#EFF6FF"},
    "Variant Title":      {"label": "Variant Title",   "fmt": "text",     "source": "Shopify", "color": "#059669", "bg": "#ECFDF5"},
    "Month":              {"label": "Month",           "fmt": "text",     "source": "All",     "color": "#64748B", "bg": "#F8FAFC"},
    "Product type":       {"label": "Product Type",    "fmt": "text",     "source": "Shopify", "color": "#059669", "bg": "#ECFDF5"},
    "Product vendor":     {"label": "Product Vendor",  "fmt": "text",     "source": "Shopify", "color": "#059669", "bg": "#ECFDF5"},
    "Product collection": {"label": "Product Collection","fmt": "text",   "source": "Shopify", "color": "#059669", "bg": "#ECFDF5"},
}


def _fmt_val(v, fmt: str) -> str:
    if fmt == "currency": return f"₹{v:,.0f}"
    if fmt == "roi":      return f"{v:.2f}x"
    if fmt == "int":      return f"{int(v):,}"
    if fmt == "pct":      return f"{float(v)*100:.2f}%"
    return str(v)


# ══════════════════════════════════════════════════════════════════════
#  FIX 3 HELPERS — Persistent file storage across page switches
# ══════════════════════════════════════════════════════════════════════

def _persist_upload(file_obj, bytes_key: str, name_key: str):
    """If a new file is uploaded, save its bytes to session_state."""
    if file_obj is not None:
        st.session_state[bytes_key] = file_obj.read()
        st.session_state[name_key]  = file_obj.name
        file_obj.seek(0)


def _show_stored_badge(bytes_key: str, name_key: str, color: str = "#059669"):
    """Show a green badge if a file is already stored from a previous upload."""
    if st.session_state.get(bytes_key) and st.session_state.get(name_key):
        fname = st.session_state[name_key]
        size_kb = len(st.session_state[bytes_key]) // 1024
        st.markdown(
            f'<div style="background:#ECFDF5;border:1px solid #6EE7B7;border-radius:6px;'
            f'padding:5px 10px;font-size:11px;color:#065F46;margin-top:4px;display:flex;'
            f'align-items:center;gap:6px">'
            f'<span>✅</span>'
            f'<span><strong>{fname}</strong> ({size_kb} KB) — stored, no re-upload needed</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════
#  FIX 2 HELPER — Between filter logic
# ══════════════════════════════════════════════════════════════════════

# Operator options now include "Between"
OP_OPTIONS = ["— None", "> Greater than", "< Less than", "= Equals", "↔ Between"]
OP_MAP     = {
    "— None":        None,
    "> Greater than":">",
    "< Less than":   "<",
    "= Equals":      "=",
    "↔ Between":     "between",
}


def _apply_num_filter(series, spec):
    """Apply a filter spec to a pandas Series. Returns boolean mask."""
    op = spec[0]
    if op == ">":       return series > spec[1]
    if op == "<":       return series < spec[1]
    if op == "=":       return series == spec[1]
    if op == "between": return (series >= spec[1]) & (series <= spec[2])
    return pd.Series([True] * len(series), index=series.index)


# ══════════════════════════════════════════════════════════════════════
#  SECTION 0 — OVERALL VIEW
# ══════════════════════════════════════════════════════════════════════

def render_overall_view():
    page_header("Product Analysis — Overall View",
                "Merge Meta, Shopify & Google exports into one unified performance table",
                "🌐")

    section_header("Upload Raw Exports",
                   "Drop your unmodified platform exports below — files are remembered across pages",
                   "#2563EB")

    # ── FIX 3: Persistent upload widgets for Overall View ─────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        upload_card("#2563EB", "#EFF6FF", "① Meta Ads",
                "Product ID · Month · Amount Spent · Landing Page Views · CTR · CPM")
        meta_file = st.file_uploader("Meta CSV", type=["csv","xlsx"],
                                      key="ov_meta_upload", label_visibility="collapsed")
        _persist_upload(meta_file, "ov_meta_bytes", "ov_meta_name")
        _show_stored_badge("ov_meta_bytes", "ov_meta_name")

    with col2:
        upload_card("#059669", "#ECFDF5", "② Shopify",
                "Product Variant ID · Product Title · Month · Product type · Product vendor	· Product collection· Net Sales · Net Items Sold")
        shopify_file = st.file_uploader("Shopify CSV", type=["csv","xlsx"],
                                         key="ov_shopify_upload", label_visibility="collapsed")
        _persist_upload(shopify_file, "ov_shopify_bytes", "ov_shopify_name")
        _show_stored_badge("ov_shopify_bytes", "ov_shopify_name")

    with col3:
        upload_card("#D97706", "#FFF7ED", "③ Google Ads (optional)",
                "Item ID · Product Title · Month · Cost · Conversions")
        google_file = st.file_uploader("Google CSV", type=["csv","xlsx"],
                                        key="ov_google_upload", label_visibility="collapsed")
        _persist_upload(google_file, "ov_google_bytes", "ov_google_name")
        _show_stored_badge("ov_google_bytes", "ov_google_name")

    # Check readiness from persisted bytes
    _meta_ready    = bool(st.session_state.get("ov_meta_bytes"))
    _shopify_ready = bool(st.session_state.get("ov_shopify_bytes"))
    _google_ready  = bool(st.session_state.get("ov_google_bytes"))

    st.markdown("<div style='margin:12px 0'></div>", unsafe_allow_html=True)
    btn_col, _ = st.columns([2, 5])
    with btn_col:
        run_ov = st.button("▶  Merge & Analyse", type="primary",
                           key="btn_run_ov", use_container_width=True)

    if run_ov:
        if not _meta_ready or not _shopify_ready:
            st.error("Please upload at least Meta and Shopify files before running.")
            return
        with st.spinner("Merging data sources…"):
            try:
                import io
                from data_cleaner import clean_meta, clean_shopify

                meta_io    = io.BytesIO(st.session_state["ov_meta_bytes"])
                meta_io.name = st.session_state["ov_meta_name"]
                shopify_io = io.BytesIO(st.session_state["ov_shopify_bytes"])
                shopify_io.name = st.session_state["ov_shopify_name"]

                meta_df,    meta_warns  = clean_meta(meta_io)
                shopify_df, shop_warns  = clean_shopify(shopify_io)

                google_df = None
                if _google_ready:
                    google_io = io.BytesIO(st.session_state["ov_google_bytes"])
                    google_io.name = st.session_state["ov_google_name"]
                    from data_cleaner import clean_google
                    google_df, g_warns = clean_google(google_io)
                    for w in g_warns:
                        st.warning(w)

                merged_df, has_month = run_overall_view(meta_df, shopify_df, google_df)
                st.session_state["ov_data"]            = merged_df
                st.session_state["ov_has_month"]       = has_month
                st.session_state["ov_has_google"]      = google_df is not None
                # Store cleaned DFs for Quadrant View handoff
                st.session_state["ov_cleaned_meta_df"]    = meta_df
                st.session_state["ov_cleaned_shopify_df"] = shopify_df

                for w in meta_warns + shop_warns:
                    st.warning(w)
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
                return

    if "ov_data" not in st.session_state:
        st.markdown(
            '<div class="th-empty" style="margin-top:16px">'
            '<div style="font-size:24px;margin-bottom:8px">📁</div>'
            '<div style="font-size:14px;font-weight:600;color:#1E40AF;margin-bottom:4px">'
            'Upload your data files to get started</div>'
            '<div class="th-text-muted" style="font-size:12px">'
            'Meta + Shopify required · Google is optional</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    df         = st.session_state["ov_data"].copy()
    has_month  = st.session_state["ov_has_month"]
    has_google = st.session_state.get("ov_has_google", False)

    # ── Period Selector ───────────────────────────────────────────────
    if has_month and "Month" in df.columns:
        months_avail   = sorted(df["Month"].dropna().unique().tolist())
        period_options = ["All Months"] + months_avail
        sel_period = st.selectbox("📅  Period", period_options, key="ov_period")
        if sel_period == "All Months":
            sel_months           = months_avail
            _all_months_selected = True
        else:
            sel_months           = [sel_period]
            _all_months_selected = False
    else:
        sel_months           = None
        _all_months_selected = True

    # ── Dynamic KPIs ──────────────────────────────────────────────────
    if has_month and sel_months and "Month" in df.columns:
        kpi_df = df[df["Month"].isin(sel_months)]
    else:
        kpi_df = df

    total_meta   = kpi_df["Meta Spend"].sum()      if "Meta Spend"      in kpi_df.columns else 0
    total_google = kpi_df["Google Cost"].sum()     if "Google Cost"     in kpi_df.columns else 0
    total_spend  = kpi_df["Total Spend"].sum()     if "Total Spend"     in kpi_df.columns else 0
    total_rev    = kpi_df["Shopify Revenue"].sum() if "Shopify Revenue" in kpi_df.columns else 0
    overall_roi  = total_rev / total_spend if total_spend else 0
    n_products   = kpi_df["Product ID"].nunique()
    period_label = sel_period if (has_month and "Month" in df.columns) else "All Time"

    divider()
    st.markdown(
        f'<div style="font-size:10px;font-weight:700;color:var(--text-faint);'
        f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">'
        f'📊 KPIs — {period_label}</div>',
        unsafe_allow_html=True,
    )
    kpi_row([
        ("Total Products", f"{n_products:,}",             "#0F172A", "#F8FAFC"),
        ("Meta Spend",     compact_currency(total_meta),   "#2563EB", "#EFF6FF"),
        ("Google Cost",    compact_currency(total_google), "#D97706", "#FFF7ED"),
        ("Total Spend",    compact_currency(total_spend),  "#7C3AED", "#F5F3FF"),
        ("Revenue",        compact_currency(total_rev),    "#059669", "#ECFDF5"),
        ("Overall ROI",    f"{overall_roi:.2f}x",
         "#059669" if overall_roi >= 1 else "#DC2626",
         "#ECFDF5" if overall_roi >= 1 else "#FEF2F2"),
    ])
    divider()

    # ── Build working dataframe ───────────────────────────────────────
    SUM_COLS  = ["Meta Spend","Google Cost","Total Spend","Shopify Revenue",
                 "Net Items Sold","Landing Page Views","Conversions"]
    RATE_COLS = ["CTR","CPM"]

    if _all_months_selected and has_month and "Month" in df.columns:
        agg_dict = {}
        for c in SUM_COLS:
            if c in df.columns: agg_dict[c] = "sum"
        for c in RATE_COLS:
            if c in df.columns: agg_dict[c] = "mean"
        if "Variant Title" in df.columns:
            agg_dict["Variant Title"] = "first"
        # Preserve Shopify text attributes
        for _txt_col in ["Product type", "Product vendor", "Product collection"]:
            if _txt_col in df.columns:
                agg_dict[_txt_col] = "first"
        group_keys = [k for k in ["Product ID","Product Title"] if k in df.columns]
        work_df = df.groupby(group_keys, as_index=False).agg(agg_dict) if agg_dict \
                  else df.groupby(group_keys, as_index=False).first()
        if "Total Spend" in work_df.columns and "Shopify Revenue" in work_df.columns:
            work_df["ROI"] = (
                work_df["Shopify Revenue"] /
                work_df["Total Spend"].replace(0, float("nan"))
            ).fillna(0).round(4)
    else:
        work_df = df[df["Month"].isin(sel_months)].copy() \
                  if (has_month and sel_months and "Month" in df.columns) else df.copy()

    # ── Column Selector ───────────────────────────────────────────────
    section_header("Columns & Filters",
                   "Select metrics to display — set ranges in the filter panel", "#2563EB")

    available_cols = [c for c in _OV_COLS if c in work_df.columns]
    if _all_months_selected and "Month" in available_cols:
        available_cols.remove("Month")
    if not has_google:
        available_cols = [c for c in available_cols if c not in ("Google Cost","Conversions")]

    default_sel = [
        c for c in ["Meta Spend","Google Cost","Total Spend","Shopify Revenue",
                    "ROI","Net Items Sold","CTR","CPM","Variant Title"]
        if c in available_cols
    ]

    col_options  = list(available_cols)
    col_labels   = [
        f"{_OV_COLS.get(c,{}).get('label',c)}  [{_OV_COLS.get(c,{}).get('source','?')}]"
        for c in col_options
    ]
    label_to_key = {lbl: key for key, lbl in zip(col_options, col_labels)}

    selected_labels = st.multiselect(
        "Columns", options=col_labels,
        default=[col_labels[col_options.index(c)] for c in default_sel if c in col_options],
        label_visibility="collapsed", key="ov_col_sel",
        placeholder="Choose metrics to display…",
    )
    selected_cols = [label_to_key[lbl] for lbl in selected_labels]

    if not selected_cols:
        st.info("Select at least one metric above to begin filtering.")
        return

    # ── Smart Search: field dropdown + search bar ─────────────────────
    # Build list of searchable fields — only include columns that exist in work_df
    _SEARCH_FIELD_MAP = {
        "Product ID":         "Product ID",
        "Product Title":      "Product Title",
        "Variant Title":      "Variant Title",
        "Product Type":       "Product type",       # ← lowercase 't' matches Shopify output
        "Product Vendor":     "Product vendor",     # ← lowercase 'v'
        "Product Collection": "Product collection", # ← lowercase 'c'
    }
    # Only show options where the underlying column exists in work_df
    _available_search_options = [
        label for label, col in _SEARCH_FIELD_MAP.items()
        if col in work_df.columns
    ]

    sch_drop, sch_input = st.columns([2, 5])
    with sch_drop:
        st.markdown(
            '<div class="th-filter-label" style="font-size:11px;font-weight:600;'
            'margin-bottom:4px">🔎 Search Field</div>',
            unsafe_allow_html=True,
        )
        search_field_label = st.selectbox(
            "Search by field",
            options=_available_search_options,
            label_visibility="collapsed",
            key="ov_search_field",
        )
    # Resolve label → actual column name in work_df
    search_col = _SEARCH_FIELD_MAP[search_field_label]

    with sch_input:
        st.markdown(
            f'<div class="th-filter-label" style="font-size:11px;font-weight:600;'
            f'margin-bottom:4px">Search in {search_field_label}</div>',
            unsafe_allow_html=True,
        )
        search_text = st.text_input(
            "Search value",
            placeholder=f"Type to search {search_field_label}…",
            label_visibility="collapsed",
            key="ov_search",
        )

    variant_search = ""   # no longer a separate box; handled via dropdown above

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── FIX 2: Metric Filters with "Between" support ──────────────────
    num_fmts  = ("currency","int","roi","pct")
    num_cols  = [c for c in selected_cols if _OV_COLS.get(c,{}).get("fmt") in num_fmts]
    text_cols = [c for c in selected_cols
                 if _OV_COLS.get(c,{}).get("fmt") == "text"
                 and c not in ("Month","Variant Title")]

    pending_specs: dict = {}
    _filter_open = st.session_state.get("ov_filter_panel_open", False)

    with st.expander("⚙️ Metric Filters", expanded=_filter_open):
        st.session_state["ov_filter_panel_open"] = True
        if num_cols:
            st.markdown(
                '<p style="font-size:11px;color:var(--text-faint);margin-bottom:12px">'
                'Choose a condition per metric — use <strong>↔ Between</strong> for a min–max range. '
                'Click <strong>Apply Filters</strong> to update results.</p>',
                unsafe_allow_html=True,
            )
            for i in range(0, len(num_cols), 2):   # 2-per-row so Between inputs have room
                chunk    = num_cols[i:i+2]
                row_cols = st.columns(len(chunk))
                for rc, col_key in zip(row_cols, chunk):
                    mi      = _OV_COLS[col_key]
                    col_min = float(work_df[col_key].min()) if col_key in work_df.columns else 0.0
                    col_max = float(work_df[col_key].max()) if col_key in work_df.columns else 100.0
                    fmt_str = ("%.4f" if mi["fmt"] == "pct"
                               else "%.2f" if mi["fmt"] == "roi" else "%.0f")
                    step    = (0.0001 if mi["fmt"] == "pct"
                               else 0.01 if mi["fmt"] == "roi" else 1.0)
                    with rc:
                        st.markdown(
                            f'<div class="th-filter-cell">'
                            f'<div class="th-filter-metric-title" style="color:{mi["color"]}">'
                            f'{mi["label"]}</div>',
                            unsafe_allow_html=True,
                        )
                        op_col, val_col = st.columns([2, 3])
                        with op_col:
                            st.markdown('<div class="th-filter-label">Condition</div>',
                                        unsafe_allow_html=True)
                            op_label = st.selectbox(
                                f"op_{col_key}", options=OP_OPTIONS,
                                label_visibility="collapsed",
                                key=f"ov_op_{col_key}",
                            )
                        op_symbol = OP_MAP.get(op_label)

                        if op_symbol == "between":
                            # Show two inputs: Min and Max
                            min_col, max_col = st.columns(2)
                            with min_col:
                                st.markdown('<div class="th-filter-label">Min</div>',
                                            unsafe_allow_html=True)
                                min_val = st.number_input(
                                    f"min_{col_key}", value=col_min,
                                    step=step, format=fmt_str,
                                    label_visibility="collapsed",
                                    key=f"ov_min_{col_key}",
                                )
                            with max_col:
                                st.markdown('<div class="th-filter-label">Max</div>',
                                            unsafe_allow_html=True)
                                max_val = st.number_input(
                                    f"max_{col_key}", value=col_max,
                                    step=step, format=fmt_str,
                                    label_visibility="collapsed",
                                    key=f"ov_max_{col_key}",
                                )
                            # Range hint
                            if mi["fmt"] == "currency":
                                hint = f"₹{min_val:,.0f} – ₹{max_val:,.0f}"
                            elif mi["fmt"] == "pct":
                                hint = f"{min_val*100:.2f}% – {max_val*100:.2f}%"
                            elif mi["fmt"] == "roi":
                                hint = f"{min_val:.2f}x – {max_val:.2f}x"
                            else:
                                hint = f"{min_val:,.0f} – {max_val:,.0f}"
                            st.markdown(
                                f'<div style="font-size:10px;color:{mi["color"]};'
                                f'font-weight:600;margin-top:2px">Range: {hint}</div>',
                                unsafe_allow_html=True,
                            )
                            pending_specs[col_key] = ("between", min_val, max_val)
                        else:
                            with val_col:
                                st.markdown('<div class="th-filter-label">Value</div>',
                                            unsafe_allow_html=True)
                                filter_val = st.number_input(
                                    f"val_{col_key}", value=col_min,
                                    step=step, format=fmt_str,
                                    label_visibility="collapsed",
                                    key=f"ov_val_{col_key}",
                                )
                            if op_symbol is not None:
                                pending_specs[col_key] = (op_symbol, filter_val)

                        st.markdown("</div>", unsafe_allow_html=True)

        if text_cols:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            for col_key in text_cols:
                mi   = _OV_COLS[col_key]
                uniq = sorted(work_df[col_key].dropna().unique().tolist()) if col_key in work_df.columns else []
                if uniq:
                    st.markdown(
                        f'<div style="font-size:11px;font-weight:600;color:{mi["color"]};'
                        f'margin-bottom:3px">{mi["label"]}</div>',
                        unsafe_allow_html=True,
                    )
                    sel_vals = st.multiselect(
                        f"filter_{col_key}", uniq, default=uniq,
                        label_visibility="collapsed",
                        key=f"ov_txt_{col_key}",
                    )
                    pending_specs[col_key] = ("text", sel_vals)

        if not num_cols and not text_cols:
            st.markdown(
                '<div class="th-text-faint" style="font-size:12px;text-align:center;'
                'padding:12px">Select metric columns above to see filters here.</div>',
                unsafe_allow_html=True,
            )

        # Apply + Reset
        st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
        apply_col, reset_col = st.columns([3, 1])
        with apply_col:
            apply_clicked = st.button("✅  Apply Filters", type="primary",
                                       key="ov_apply_filters", use_container_width=True)
        with reset_col:
            if st.button("↺ Reset", key="ov_reset"):
                keys_to_del = ["ov_search","ov_period","ov_col_sel","ov_variant_search",
                               "ov_active_filters","ov_filter_panel_open",
                               "ov_search_field","ov_search_col_snap","ov_search_snap",
                               "ov_variant_snap"]
                for c in available_cols:
                    keys_to_del += [f"ov_op_{c}",f"ov_val_{c}",f"ov_txt_{c}",
                                    f"ov_min_{c}",f"ov_max_{c}"]
                for k in keys_to_del:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

        if apply_clicked:
            st.session_state["ov_active_filters"]    = dict(pending_specs)
            st.session_state["ov_search_snap"]       = search_text
            st.session_state["ov_search_col_snap"]   = search_col   # save which column
            st.session_state["ov_variant_snap"]      = variant_search
            st.session_state["ov_filter_panel_open"] = False
            st.rerun()
    # ── Apply committed filters ───────────────────────────────────────
    active_filters    = st.session_state.get("ov_active_filters", {})
    committed_search  = st.session_state.get("ov_search_snap",  search_text)
    committed_variant = st.session_state.get("ov_variant_snap", variant_search)

    fdf = work_df.copy()

    if committed_search.strip():
        q = committed_search.strip().lower()
        # Use the saved search column from the last Apply click;
        # fall back to search_col from the current widget if no snap yet
        _active_search_col = st.session_state.get("ov_search_col_snap", search_col)
        if _active_search_col in fdf.columns:
            fdf = fdf[
                fdf[_active_search_col].astype(str).str.lower().str.contains(q, na=False)
            ]
        else:
            # Fallback: search Product Title + Product ID
            fdf = fdf[
                fdf["Product Title"].astype(str).str.lower().str.contains(q, na=False) |
                fdf["Product ID"].astype(str).str.lower().str.contains(q, na=False)
            ]

    if committed_variant.strip() and "Variant Title" in fdf.columns:
        fdf = fdf[
            fdf["Variant Title"].str.lower()
            .str.contains(committed_variant.strip().lower(), na=False)
        ]

    for col_key, spec in active_filters.items():
        if col_key not in fdf.columns: continue
        if spec[0] == "text":
            _, sel_vals = spec
            if sel_vals: fdf = fdf[fdf[col_key].isin(sel_vals)]
        else:
            mask = _apply_num_filter(fdf[col_key], spec)
            fdf  = fdf[mask]

    # ── Result strip ──────────────────────────────────────────────────
    n_shown     = len(fdf)
    n_total     = len(work_df)
    is_filtered = n_shown < n_total

    badge_color  = "#2563EB" if not is_filtered else "#059669"
    filter_badge = (
        '<span style="background:#DBEAFE;border-radius:6px;padding:3px 10px;'
        'font-size:11px;color:#1E40AF;font-weight:600">Filters active</span>'
        if is_filtered else ""
    )

    # Show active filter summary chips
    if active_filters:
        chips = ""
        for col_key, spec in active_filters.items():
            mi = _OV_COLS.get(col_key, {})
            lbl = mi.get("label", col_key)
            color = mi.get("color", "#64748B")
            if spec[0] == "between":
                desc = f"between {_fmt_val(spec[1], mi.get('fmt','text'))} – {_fmt_val(spec[2], mi.get('fmt','text'))}"
            elif spec[0] == "text":
                desc = f"in {len(spec[1])} values"
            else:
                desc = f"{spec[0]} {_fmt_val(spec[1], mi.get('fmt','text'))}"
            chips += (
                f'<span style="background:#F1F5F9;border:1px solid {color}44;'
                f'border-radius:5px;padding:2px 8px;font-size:10px;color:{color};'
                f'font-weight:600;margin:2px">{lbl} {desc}</span>'
            )
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin:4px 0 8px">'
            f'<span style="font-size:10px;color:var(--text-faint);align-self:center;'
            f'margin-right:4px">Active filters:</span>{chips}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin:12px 0 8px">'
        f'<span style="background:{badge_color};color:white;border-radius:6px;'
        f'padding:3px 10px;font-size:12px;font-weight:700">{n_shown:,} rows</span>'
        f'<span class="th-text-faint" style="font-size:12px">'
        f'{"showing all products" if not is_filtered else f"filtered from {n_total:,} total"}'
        f'</span>'
        f'{filter_badge}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if is_filtered and not fdf.empty:
        kpi_items = []
        for col_key in selected_cols:
            mi = _OV_COLS.get(col_key, {})
            if mi.get("fmt") in ("currency","int") and col_key in fdf.columns:
                kpi_items.append((mi["label"], _fmt_val(fdf[col_key].sum(), mi["fmt"]),
                                  mi["color"], mi["bg"]))
            elif mi.get("fmt") == "roi" and col_key in fdf.columns:
                sp    = fdf["Total Spend"].sum()     if "Total Spend"     in fdf.columns else 0
                rv    = fdf["Shopify Revenue"].sum() if "Shopify Revenue" in fdf.columns else 0
                roi_v = rv / sp if sp else 0
                kpi_items.append(("Filtered ROI", f"{roi_v:.2f}x",
                                  "#059669" if roi_v >= 1 else "#DC2626",
                                  "#ECFDF5" if roi_v >= 1 else "#FEF2F2"))
        if kpi_items:
            kpi_row(kpi_items[:6])
            st.markdown("<div style='margin:10px 0'></div>", unsafe_allow_html=True)

    if fdf.empty:
        st.markdown(
            '<div class="th-empty">'
            '<div style="font-size:28px;margin-bottom:8px">🔍</div>'
            '<div style="font-size:14px;font-weight:600;color:#DC2626;margin-bottom:4px">'
            'No results found</div>'
            '<div class="th-text-faint" style="font-size:12px">'
            'Try adjusting your filters above</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Build display table ───────────────────────────────────────────
    if "Total Spend" in fdf.columns:
        fdf = fdf.sort_values("Total Spend", ascending=False, na_position="last")
    elif "Meta Spend" in fdf.columns:
        fdf = fdf.sort_values("Meta Spend", ascending=False, na_position="last")

    always_cols = ["Product ID","Product Title"]
    if "Variant Title" in fdf.columns: always_cols.append("Variant Title")
    if not _all_months_selected and "Month" in selected_cols and "Month" in fdf.columns:
        always_cols.append("Month")

    disp            = fdf[[c for c in always_cols if c in fdf.columns]].copy()
    display_col_map: dict = {}

    for col_key in selected_cols:
        if col_key in always_cols or col_key not in fdf.columns: continue
        mi       = _OV_COLS.get(col_key, {})
        disp_lbl = mi.get("label", col_key)
        disp[disp_lbl] = fdf[col_key].apply(lambda v: _fmt_val(v, mi.get("fmt","text")))
        display_col_map[disp_lbl] = col_key

    disp_cols_data = [c for c in always_cols if c in disp.columns] + list(display_col_map.keys())

    totals_row = {c: ("∑ TOTAL" if c == "Product ID" else "") for c in always_cols}
    for disp_lbl, col_key in display_col_map.items():
        mi  = _OV_COLS.get(col_key, {})
        fmt = mi.get("fmt","text")
        if fmt in ("currency","int") and col_key in fdf.columns:
            # CPM is a rate — average, not sum
            if col_key == "CPM":
                totals_row[disp_lbl] = _fmt_val(fdf[col_key].mean(), fmt)
            else:
                totals_row[disp_lbl] = _fmt_val(fdf[col_key].sum(), fmt)
        elif fmt == "pct" and col_key in fdf.columns:
            totals_row[disp_lbl] = _fmt_val(fdf[col_key].mean(), fmt)
        elif fmt == "roi":
            sp = fdf["Total Spend"].sum()     if "Total Spend"     in fdf.columns else 0
            rv = fdf["Shopify Revenue"].sum() if "Shopify Revenue" in fdf.columns else 0
            totals_row[disp_lbl] = f"{rv/sp:.2f}x" if sp else "—"
        else:
            totals_row[disp_lbl] = ""

    totals_html = ""
    for disp_lbl, col_key in display_col_map.items():
        mi  = _OV_COLS.get(col_key, {})
        val = totals_row.get(disp_lbl, "")
        if val and val != "":
            totals_html += (
                f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'background:{mi["bg"]};border:1px solid {mi["color"]}22;'
                f'border-radius:6px;padding:4px 10px;font-size:11px;margin:2px;'
                f'color:{mi["color"]};font-weight:700">'
                f'{disp_lbl}: {val}</span>'
            )

    if totals_html:
        st.markdown(
            f'<div class="th-totals-bar">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.1em;margin-bottom:6px;" class="th-text-faint">'
            f'∑ Totals · {n_shown:,} products</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px">{totals_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.dataframe(
        disp[disp_cols_data].reset_index(drop=True),
        use_container_width=True, hide_index=True, height=500,
    )

    st.markdown(
        f'<div class="th-grand-bar">'
        f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:8px;" class="th-text-grandtot">'
        f'∑ Grand Totals — {n_shown:,} products'
        f'{"  ·  All months combined" if _all_months_selected and has_month else ""}'
        f'</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px">{totals_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Download ──────────────────────────────────────────────────────
    dl_name_col, dl_btn_col, dl_info_col = st.columns([3, 2, 3])
    with dl_name_col:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#64748B;margin-bottom:4px'>📄 File Name</div>", unsafe_allow_html=True)
        custom_filename = st.text_input("File name", value="overall_view_filtered",
                                         placeholder="Enter file name…",
                                         label_visibility="collapsed", key="ov_download_name")
        safe_name = (custom_filename.strip().replace(" ","_") or "overall_view_filtered").removesuffix(".csv")
    with dl_btn_col:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#64748B;margin-bottom:4px'>⬇ Download</div>", unsafe_allow_html=True)
        export_cols = [c for c in always_cols if c in fdf.columns]
        for col_key in selected_cols:
            if col_key not in export_cols and col_key in fdf.columns:
                export_cols.append(col_key)
        # Always append Google Item ID if present — maps cleaned ID back to original
        if "Google Item ID" in fdf.columns and "Google Item ID" not in export_cols:
            export_cols.append("Google Item ID")

        # Build filter summary rows to prepend above data
        filter_lines = []
        filter_lines.append(["APPLIED FILTERS"])
        filter_lines.append([f"Period: {sel_period if has_month and 'Month' in df.columns else 'All Time'}"])
        if committed_search.strip():
            filter_lines.append([f"Product Search: {committed_search.strip()}"])
        if committed_variant.strip():
            filter_lines.append([f"Variant Search: {committed_variant.strip()}"])
        for col_key, spec in active_filters.items():
            mi  = _OV_COLS.get(col_key, {})
            lbl = mi.get("label", col_key)
            fmt = mi.get("fmt", "text")
            if spec[0] == "between":
                filter_lines.append([f"{lbl}: between {_fmt_val(spec[1], fmt)} and {_fmt_val(spec[2], fmt)}"])
            elif spec[0] == "text":
                filter_lines.append([f"{lbl}: {len(spec[1])} values selected"])
            else:
                op_display = {">": "greater than", "<": "less than", "=": "equals"}.get(spec[0], spec[0])
                filter_lines.append([f"{lbl}: {op_display} {_fmt_val(spec[1], fmt)}"])
        filter_lines.append([f"Rows returned: {n_shown:,} of {n_total:,} total"])
        filter_lines.append([])  # blank separator row
        filter_lines.append(export_cols)  # column headers

        import io as _io
        output = _io.StringIO()
        import csv as _csv
        writer = _csv.writer(output)
        for row in filter_lines:
            writer.writerow(row)
        # Write data rows
        for _, row in fdf[export_cols].iterrows():
            writer.writerow([str(v) for v in row.values])
        csv_buf = output.getvalue().encode("utf-8")
        st.download_button(
            label="⬇  Download CSV", data=csv_buf,
            file_name=f"{safe_name}.csv", mime="text/csv",
            type="primary", use_container_width=True, key="ov_dl_btn",
        )
    with dl_info_col:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#64748B;margin-bottom:4px'>ℹ Info</div>", unsafe_allow_html=True)
        col_names = ", ".join([_OV_COLS.get(c,{}).get("label",c) for c in export_cols])
        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
            f'padding:8px 12px;font-size:12px;color:#64748B;line-height:1.5">'
            f'<strong style="color:#1E293B">{n_shown:,} rows</strong> · '
            f'<strong style="color:#1E293B">{len(export_cols)} cols</strong><br>'
            f'<span style="font-size:10px;color:#94A3B8">'
            f'{col_names[:80]}{"…" if len(col_names)>80 else ""}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Go to Quadrant View ───────────────────────────────────────────
    divider()
    st.markdown(
        '<div style="background:linear-gradient(135deg,#EEF2FF,#F5F3FF);'
        'border-radius:14px;padding:20px 24px;border:1px solid #C7D2FE;margin-bottom:8px">'
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">'
        '<span style="font-size:26px">🔲</span>'
        '<div>'
        '<div style="font-size:15px;font-weight:800;color:#3730A3">Continue to Quadrant View</div>'
        '<div style="font-size:12px;color:#6366F1;margin-top:2px">'
        'Run the 4-quadrant analysis with your cleaned data — no re-upload needed'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔲  Go to Quadrant View →", type="primary",
                 key="ov_goto_quadrant", use_container_width=False):
        if st.session_state.get("ov_cleaned_meta_df") is not None:
            st.session_state["s2_from_ov_meta_df"]    = st.session_state["ov_cleaned_meta_df"]
            st.session_state["s2_from_ov_shopify_df"] = st.session_state["ov_cleaned_shopify_df"]
            st.session_state["s2_use_ov_data"]        = True

        if "Total Spend" in work_df.columns and len(work_df) > 0:
            st.session_state["s2_avg_spend_abs"] = work_df["Total Spend"].mean()
            st.session_state["s2_avg_rev_abs"]   = work_df["Shopify Revenue"].mean() \
                                                    if "Shopify Revenue" in work_df.columns else 0

        st.session_state["_nav_page"] = "🔲 Quadrant View"
        st.session_state["_run_s2"]   = True
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  SECTION 1 — DISCOUNT ANALYSIS
# ══════════════════════════════════════════════════════════════════════

def insight_bucket_ui(itype: str, df_sec, key_prefix: str):
    CONF = {
        "hslr": {"icon":"🔴","label":"High Spend · Low Revenue",
                 "tip":"Consuming budget with poor returns — review or pause",
                 "color":"#DC2626","bg":"#FEF2F2","border":"#FCA5A5"},
        "lshr": {"icon":"🟢","label":"Low Spend · High Revenue",
                 "tip":"Highly efficient — consider scaling spend",
                 "color":"#059669","bg":"#ECFDF5","border":"#6EE7B7"},
    }
    c = CONF[itype]
    st.markdown(
        f'<div style="background:{c["bg"]};border:1.5px solid {c["border"]};'
        f'border-radius:12px;padding:14px 18px;margin-bottom:12px">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
        f'<span style="font-size:16px">{c["icon"]}</span>'
        f'<span style="font-weight:700;color:{c["color"]};font-size:13px">{c["label"]}</span>'
        f'</div>'
        f'<div class="th-text-muted" style="font-size:11px">{c["tip"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if df_sec.empty:
        st.markdown(
            '<div class="th-card-muted" style="padding:12px;font-size:12px;'
            'text-align:center;margin-bottom:12px;">'
            '<span class="th-text-faint">No products match this criteria</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    t_sp  = df_sec["Spend"].sum()
    t_rv  = df_sec["Revenue"].sum()
    t_roi = round(t_rv / t_sp, 2) if t_sp else 0
    kpi_row([
        ("Products",  f"{len(df_sec):,}",    c["color"], c["bg"]),
        ("Spend",     compact_currency(t_sp), "#64748B",  "#F8FAFC"),
        ("Revenue",   compact_currency(t_rv), "#059669",  "#ECFDF5"),
        ("ROI",       fmt_roi(t_roi),         c["color"], c["bg"]),
    ])
    with st.expander(f"View {len(df_sec)} products"):
        disp = df_sec.copy()
        disp["Spend"]   = disp["Spend"].apply(fmt_inr)
        disp["Revenue"] = disp["Revenue"].apply(fmt_inr)
        disp["ROI"]     = disp["ROI"].apply(fmt_roi)
        disp = disp.rename(columns={"Product ID":"PID","Product Title":"Title",
                                     "Spend":"Spend (INR)","Revenue":"Revenue (INR)"})
        st.dataframe(disp, use_container_width=True, hide_index=True)


def render_discount_view():
    page_header("Discount vs Non-Discount",
                "Compare discounted and non-discounted product performance", "📋")

    run_s1     = st.session_state.get("_run_s1",    False)
    spend_pct  = st.session_state.get("s1_sp",      100)
    rev_pct    = st.session_state.get("s1_rv",      100)
    brand_name = st.session_state.get("brand_name", "Brand")

    section_header("Upload Raw Exports",
                   "Meta + Shopify required · Discount list is the 3rd file — files are remembered",
                   "#2563EB")

    # ── FIX 3: Persistent uploads for Discount View ───────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        upload_card("#2563EB", "#EFF6FF", "① Meta Ads",
                "Cols: Product ID · Month · Amount Spent · Landing Page Views · CTR · CPM")
        meta_file = st.file_uploader("Meta CSV", type=["csv","xlsx"],
                                      key="s1_meta", label_visibility="collapsed")
        _persist_upload(meta_file, "s1_meta_bytes", "s1_meta_name")
        _show_stored_badge("s1_meta_bytes", "s1_meta_name")

    with col2:
        upload_card("#059669", "#ECFDF5", "② Shopify",
                "Cols: Product Variant ID · Product Title · Month · Net Sales · Net Items Sold")
        shopify_file = st.file_uploader("Shopify CSV", type=["csv","xlsx"],
                                         key="s1_shop", label_visibility="collapsed")
        _persist_upload(shopify_file, "s1_shopify_bytes", "s1_shopify_name")
        _show_stored_badge("s1_shopify_bytes", "s1_shopify_name")

    with col3:
        upload_card("#D97706", "#FFF7ED", "③ Google Ads (optional)",
                "Cols: Item ID · Product Title · Month · Cost · Conversions")
        discount_file = st.file_uploader("Discount list", type=["csv","xlsx"],
                                          key="s1_disc", label_visibility="collapsed")
        _persist_upload(discount_file, "s1_disc_bytes", "s1_disc_name")
        _show_stored_badge("s1_disc_bytes", "s1_disc_name")

    if run_s1:
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
                from data_cleaner import clean_meta, clean_shopify

                meta_io    = io.BytesIO(meta_bytes);    meta_io.name    = st.session_state["s1_meta_name"]
                shopify_io = io.BytesIO(shopify_bytes); shopify_io.name = st.session_state["s1_shopify_name"]
                disc_io    = io.BytesIO(disc_bytes);    disc_io.name    = st.session_state["s1_disc_name"]

                meta_df,    meta_warns  = clean_meta(meta_io)
                shopify_df, shop_warns  = clean_shopify(shopify_io)

                disc_name = st.session_state["s1_disc_name"]
                if disc_name.lower().endswith((".xlsx",".xls")):
                    disc_df = pd.read_excel(disc_io)
                else:
                    disc_df = pd.read_csv(disc_io)

                if "Product ID" not in disc_df.columns:
                    pid_alt = next(
                        (c for c in disc_df.columns if "id" in c.lower() or "sku" in c.lower()),
                        disc_df.columns[0],
                    )
                    disc_df = disc_df.rename(columns={pid_alt:"Product ID"})

                (results_df, months_ordered, merged,
                 insights, overall_insights, title_map) = run_discount_analysis(
                    meta_df, shopify_df, disc_df, spend_pct, rev_pct,
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
                st.error(f"Error: {e}"); st.exception(e); st.stop()
        st.session_state["_run_s1"] = False

    if "s1_results" not in st.session_state:
        st.markdown(
            '<div class="th-empty" style="background:#FFF7ED;border:1px solid #FDE68A;'
            'margin-top:16px">'
            '<div style="font-size:24px;margin-bottom:8px">📊</div>'
            '<div style="font-size:14px;font-weight:600;color:#92400E;margin-bottom:4px">'
            'Upload 3 files and click Run in the sidebar</div>'
            '<div class="th-text-muted" style="font-size:12px">'
            'Meta · Shopify · Discount list required</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    results_df       = st.session_state["s1_results"]
    months_ordered   = st.session_state["s1_months"]
    merged           = st.session_state["s1_merged"]
    insights         = st.session_state["s1_insights"]
    overall_insights = st.session_state["s1_overall_insights"]

    st.success(f"✅ {len(months_ordered)} month(s) loaded: {', '.join(months_ordered)}")
    divider()
    kpi_row([
        ("Total Products",  f"{merged['Product ID'].nunique():,}",                          "#0F172A","#F8FAFC"),
        ("Discounted",      f"{merged[merged['Is_Discounted']]['Product ID'].nunique():,}",  "#2563EB","#EFF6FF"),
        ("Non-Discounted",  f"{merged[~merged['Is_Discounted']]['Product ID'].nunique():,}", "#059669","#ECFDF5"),
        ("Overall ROI",
         fmt_roi(merged["Revenue"].sum()/merged["Spend"].sum()) if merged["Spend"].sum() else "—",
         "#7C3AED","#F5F3FF"),
    ])
    divider()

    selected_months = st.multiselect("Months", months_ordered, default=months_ordered, key="s1_timeline")
    active_months   = selected_months if selected_months else months_ordered
    active_results  = results_df[results_df["Month"].isin(active_months)]
    divider()

    tab1, tab2, tab3 = st.tabs(["📊  Summary · Charts","🔍  Product Insights","⬇  Download"])

    with tab1:
        view_mode = st.radio("View", ["📋 Table / Matrix","📈 Charts"],
                             horizontal=True, label_visibility="collapsed", key="s1_view")
        if view_mode == "📋 Table / Matrix":
            section_header("Monthly Summary Matrix",
                           "Spend, Revenue, ROI by category per month", "#2563EB")
            for month in active_months:
                md = active_results[active_results["Month"]==month].copy()
                if md.empty: continue
                st.markdown(
                    f'<div style="background:#2563EB;border-radius:6px;padding:4px 12px;'
                    f'font-size:12px;font-weight:700;color:white;display:inline-block;'
                    f'margin:14px 0 8px">{month}</div>',
                    unsafe_allow_html=True,
                )
                disp = md[["Category","Spend","Revenue","Spend_Pct","Revenue_Pct","ROI"]].copy()
                disp.columns = ["Category","Spend (INR)","Revenue (INR)","Spend %","Revenue %","ROI"]
                disp["Spend (INR)"]   = disp["Spend (INR)"].apply(fmt_inr)
                disp["Revenue (INR)"] = disp["Revenue (INR)"].apply(fmt_inr)
                disp["Spend %"]       = disp["Spend %"].apply(fmt_pct)
                disp["Revenue %"]     = disp["Revenue %"].apply(fmt_pct)
                disp["ROI"]           = disp["ROI"].apply(fmt_roi)
                st.dataframe(disp.set_index("Category"), use_container_width=True)
        else:
            section_header("Performance Charts","Visual comparison across months","#059669")
            st.plotly_chart(make_combo_chart(active_results, active_months), use_container_width=True)
            st.caption("🔵 Blue = Spend  ·  🟢 Green = Revenue  ·  🟡 Line = ROI")
            divider()
            st.plotly_chart(make_share_chart(active_results, active_months), use_container_width=True)

    with tab2:
        analysis_mode = st.radio("Mode",
                                  ["📅 Monthly Analysis","🌐 Full Analysis (Overall)"],
                                  horizontal=True, key="s1_mode", label_visibility="collapsed")
        cat_key    = "s1_cat_monthly" if analysis_mode == "📅 Monthly Analysis" else "s1_cat_overall"
        cat_choice = st.radio("Category", ["Discounted","Non-Discounted"],
                              horizontal=True, key=cat_key)
        cat_color  = "#2563EB" if cat_choice == "Discounted" else "#059669"

        if analysis_mode == "📅 Monthly Analysis":
            for month in active_months:
                st.markdown(
                    f'<div class="th-card" style="padding:10px 16px;margin:16px 0 8px;'
                    f'border-left:4px solid {cat_color}">'
                    f'<div class="th-text-primary" style="font-size:13px;font-weight:700">'
                    f'{month} · <span class="th-text-muted" style="font-weight:400;'
                    f'font-size:12px">{cat_choice}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                ins = insights.get((month, cat_choice), {})
                col_a, col_b = st.columns(2)
                with col_a: insight_bucket_ui("hslr", ins.get("hslr", pd.DataFrame()), f"m_{month}_{cat_choice}_hslr")
                with col_b: insight_bucket_ui("lshr", ins.get("lshr", pd.DataFrame()), f"m_{month}_{cat_choice}_lshr")
        else:
            ov = overall_insights.get(cat_choice, {})
            col_a, col_b = st.columns(2)
            with col_a: insight_bucket_ui("hslr", ov.get("hslr", pd.DataFrame()), f"ov_{cat_choice}_hslr")
            with col_b: insight_bucket_ui("lshr", ov.get("lshr", pd.DataFrame()), f"ov_{cat_choice}_lshr")

    with tab3:
        section_header("Download Excel Report",
                       "Full analysis with monthly + overall insight sheets","#7C3AED")
        excel_buf = build_s1_excel(active_results, active_months, insights, overall_insights)
        st.download_button(
            label=f"📥  Download {brand_name} Discount Analysis.xlsx",
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


def quadrant_card(qkey: str, df, desc: str):
    cfg = QUAD_CONFIG[qkey]
    n   = len(df)
    sp  = df["Spend"].sum()
    rv  = df["Revenue"].sum()
    roi = round(rv / sp, 2) if sp else 0

    st.markdown(
        f'<div class="th-card" style="border-top:4px solid {cfg["color"]};'
        f'padding:20px 22px;margin-bottom:2px;min-height:160px">'
        f'<div style="display:flex;align-items:flex-start;justify-content:space-between;'
        f'flex-wrap:nowrap;gap:10px">'
        f'<div style="min-width:130px;max-width:160px">'
        f'<div style="font-size:20px;margin-bottom:4px">{cfg["icon"]}</div>'
        f'<div class="th-text-primary" style="font-size:14px;font-weight:700;'
        f'margin-bottom:4px;line-height:1.2">{cfg["label"]}</div>'
        f'<div class="th-text-faint" style="font-size:11px;line-height:1.4">{desc}</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:repeat(4,72px);gap:8px;flex-shrink:0">'
        f'<div style="text-align:center">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:4px">Products</div>'
        f'<div style="font-size:22px;font-weight:800;color:{cfg["color"]}">{n}</div>'
        f'</div>'
        f'<div style="text-align:center">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:4px">Spend</div>'
        f'<div class="th-text-secondary" style="font-size:13px;font-weight:700;'
        f'line-height:1.2">{compact_currency(sp)}</div>'
        f'</div>'
        f'<div style="text-align:center">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:4px">Revenue</div>'
        f'<div class="th-text-secondary" style="font-size:13px;font-weight:700;'
        f'line-height:1.2">{compact_currency(rv)}</div>'
        f'</div>'
        f'<div style="text-align:center">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:4px">ROI</div>'
        f'<div style="font-size:22px;font-weight:800;color:{cfg["color"]}">'
        f'{roi:.2f}x</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    with st.expander(f"View all {n} products"):
        if df.empty:
            st.info("No products in this quadrant.")
        else:
            disp = df.copy()
            disp["Spend"]   = disp["Spend"].apply(fmt_inr)
            disp["Revenue"] = disp["Revenue"].apply(fmt_inr)
            disp["ROI"]     = disp["ROI"].apply(fmt_roi)
            st.dataframe(disp, use_container_width=True, hide_index=True)

            # Download raw (unformatted) CSV for this quadrant
            dl_col, info_col = st.columns([2, 3])
            with dl_col:
                raw_csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"⬇  Download {cfg['label']} Products",
                    data=raw_csv,
                    file_name=f"quadrant_{qkey}_{cfg['label'].lower().replace(' ','_')}.csv",
                    mime="text/csv",
                    key=f"dl_quad_{qkey}",
                    use_container_width=True,
                )
            with info_col:
                st.markdown(
                    f'<div style="font-size:11px;color:var(--text-faint);'
                    f'padding:6px 0;line-height:1.5">'
                    f'{n:,} products · Spend, Revenue, ROI columns · raw ₹ values</div>',
                    unsafe_allow_html=True,
                )


def render_quadrant_view():
    page_header("Quadrant View",
                "Products split into 4 performance groups with AI insights", "🔲")

    run_s2       = st.session_state.get("_run_s2",  False)
    s2_spend_pct = st.session_state.get("s2_sp",    100)
    s2_rev_pct   = st.session_state.get("s2_rv",    100)
    _use_ov_data = st.session_state.get("s2_use_ov_data", False)

    if not _use_ov_data:
        section_header("Upload Raw Exports",
                       "Meta + Shopify exports — files are remembered if already uploaded",
                       "#2563EB")

        # ── FIX 3: Persistent uploads for Quadrant View ───────────────
        col1, col2 = st.columns(2)
        with col1:
            upload_card("#2563EB","#EFF6FF","① Meta Ads","Raw export — auto-cleaned")
            s2_meta_file = st.file_uploader("Meta CSV", type=["csv","xlsx"],
                                             key="s2_meta", label_visibility="collapsed")
            _persist_upload(s2_meta_file, "s2_meta_bytes", "s2_meta_name")
            _show_stored_badge("s2_meta_bytes", "s2_meta_name")

        with col2:
            upload_card("#059669","#ECFDF5","② Shopify","Raw export — auto-cleaned")
            s2_shopify_file = st.file_uploader("Shopify CSV", type=["csv","xlsx"],
                                                key="s2_shop", label_visibility="collapsed")
            _persist_upload(s2_shopify_file, "s2_shopify_bytes", "s2_shopify_name")
            _show_stored_badge("s2_shopify_bytes", "s2_shopify_name")
    else:
        st.markdown(
            '<div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;'
            'padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:10px">'
            '<span style="font-size:18px">✅</span>'
            '<div>'
            '<div style="font-size:13px;font-weight:700;color:#065F46">'
            'Using data from Product Analysis — Overall View</div>'
            '<div style="font-size:11px;color:#047857;margin-top:2px">'
            'Cleaned Meta & Shopify files transferred automatically</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    if run_s2:
        with st.spinner("Cleaning and analysing data…"):
            try:
                import io
                from data_cleaner import clean_meta, clean_shopify

                if _use_ov_data:
                    meta_df    = st.session_state["s2_from_ov_meta_df"]
                    shopify_df = st.session_state["s2_from_ov_shopify_df"]
                    meta_warns = shop_warns = []
                else:
                    meta_bytes    = st.session_state.get("s2_meta_bytes")
                    shopify_bytes = st.session_state.get("s2_shopify_bytes")
                    if not meta_bytes or not shopify_bytes:
                        st.error("Upload Meta and Shopify CSV files.")
                        st.session_state["_run_s2"] = False
                        st.stop()
                    meta_io    = io.BytesIO(meta_bytes);    meta_io.name    = st.session_state["s2_meta_name"]
                    shopify_io = io.BytesIO(shopify_bytes); shopify_io.name = st.session_state["s2_shopify_name"]
                    meta_df,    meta_warns  = clean_meta(meta_io)
                    shopify_df, shop_warns  = clean_shopify(shopify_io)

                avg_spend_abs = st.session_state.get("s2_avg_spend_abs", None)
                avg_rev_abs   = st.session_state.get("s2_avg_rev_abs",   None)

                data = run_product_analysis(meta_df, shopify_df, s2_spend_pct, s2_rev_pct)

                if avg_spend_abs is not None:
                    data["sp_cut"] = avg_spend_abs
                    data["avg_sp"] = avg_spend_abs
                if avg_rev_abs is not None:
                    data["rv_cut"] = avg_rev_abs
                    data["avg_rv"] = avg_rev_abs
                    all_df_ = data["all"]
                    cols    = ["Product ID","Product Title","Spend","Revenue","ROI"]
                    sp_c    = data["sp_cut"]
                    rv_c    = data["rv_cut"]
                    data["q1"] = all_df_[(all_df_["Revenue"]>=rv_c)&(all_df_["Spend"]< sp_c)][cols].sort_values("Revenue",ascending=False).reset_index(drop=True)
                    data["q2"] = all_df_[(all_df_["Revenue"]>=rv_c)&(all_df_["Spend"]>=sp_c)][cols].sort_values("Revenue",ascending=False).reset_index(drop=True)
                    data["q3"] = all_df_[(all_df_["Revenue"]< rv_c)&(all_df_["Spend"]>=sp_c)][cols].sort_values("Spend",  ascending=False).reset_index(drop=True)
                    data["q4"] = all_df_[(all_df_["Revenue"]< rv_c)&(all_df_["Spend"]< sp_c)][cols].sort_values("Revenue",ascending=False).reset_index(drop=True)

                st.session_state.update({
                    "s2_data":   data,
                    "s2_sp_pct": s2_spend_pct,
                    "s2_rv_pct": s2_rev_pct,
                })
                if "s2_ai_insights" in st.session_state:
                    del st.session_state["s2_ai_insights"]
                for w in (meta_warns or []) + (shop_warns or []):
                    st.warning(w)
            except Exception as e:
                st.error(f"Error: {e}"); st.exception(e); st.stop()
        st.session_state["_run_s2"] = False

    if "s2_data" not in st.session_state:
        st.markdown(
            '<div class="th-empty" style="background:#EFF6FF;border:1px solid #BFDBFE;'
            'margin-top:16px">'
            '<div style="font-size:24px;margin-bottom:8px">🔲</div>'
            '<div style="font-size:14px;font-weight:600;color:#1E40AF;margin-bottom:4px">'
            'Upload files and click Run Product Analysis in the sidebar</div>'
            '<div class="th-text-muted" style="font-size:12px">'
            'Meta + Shopify required · or navigate from Product Analysis view</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    data     = st.session_state["s2_data"]
    all_df   = data["all"];    monthly  = data["monthly"]
    sp_cut   = data["sp_cut"]; rv_cut   = data["rv_cut"]
    avg_sp   = data.get("avg_sp", sp_cut)
    avg_rv   = data.get("avg_rv", rv_cut)
    total_sp = all_df["Spend"].sum()
    total_rv = all_df["Revenue"].sum()

    divider()
    kpi_row([
        ("Total Products", f"{len(all_df):,}",        "#0F172A","#F8FAFC"),
        ("Total Spend",    compact_currency(total_sp), "#64748B","#F8FAFC"),
        ("Total Revenue",  compact_currency(total_rv), "#059669","#ECFDF5"),
        ("Overall ROI",    fmt_roi(total_rv/total_sp) if total_sp else "—","#7C3AED","#F5F3FF"),
    ])

    st.markdown(
        f'<div class="th-card-muted" style="padding:14px 18px;margin:12px 0;">'
        f'<div style="font-size:11px;font-weight:700;color:var(--text-faint);'
        f'text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px">'
        f'Quadrant Axis Thresholds</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:24px">'
        f'<div>'
        f'<div style="font-size:10px;color:var(--text-faint);font-weight:600;'
        f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">'
        f'X-Axis — Total Spend (Ad Cost)</div>'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'<span style="font-size:13px;font-weight:700;color:#7C3AED">'
        f'Low Spend &lt; {compact_currency(sp_cut)}</span>'
        f'<span style="font-size:11px;color:var(--text-faint)">|</span>'
        f'<span style="font-size:13px;font-weight:700;color:#2563EB">'
        f'High Spend ≥ {compact_currency(sp_cut)}</span>'
        f'</div>'
        f'<div style="font-size:10px;color:var(--text-faint);margin-top:2px">'
        f'Average: {compact_currency(avg_sp)} per product</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size:10px;color:var(--text-faint);font-weight:600;'
        f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">'
        f'Y-Axis — Shopify Revenue</div>'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'<span style="font-size:13px;font-weight:700;color:#64748B">'
        f'Low Revenue &lt; {compact_currency(rv_cut)}</span>'
        f'<span style="font-size:11px;color:var(--text-faint)">|</span>'
        f'<span style="font-size:13px;font-weight:700;color:#059669">'
        f'High Revenue ≥ {compact_currency(rv_cut)}</span>'
        f'</div>'
        f'<div style="font-size:10px;color:var(--text-faint);margin-top:2px">'
        f'Average: {compact_currency(avg_rv)} per product</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size:10px;color:var(--text-faint);font-weight:600;'
        f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">'
        f'Months in Data</div>'
        f'<div style="font-size:16px;font-weight:800;color:#7C3AED">'
        f'{data["total_months"]}</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    divider()
    section_header("Quadrant Breakdown",
                   "Products split by spend and revenue vs average", "#2563EB")

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    with r1c1: quadrant_card("q1", data["q1"], "High Revenue · Low Spend — great ROI, underinvested")
    with r1c2: quadrant_card("q2", data["q2"], "High Revenue · High Spend — strong performers")
    with r2c1: quadrant_card("q4", data["q4"], "Low Revenue · Low Spend — assess or drop")
    with r2c2: quadrant_card("q3", data["q3"], "Low Revenue · High Spend — budget drain")

    divider()
    st.markdown(
        '<div class="th-card" style="background:linear-gradient(135deg,#EEF2FF,#F5F3FF);'
        'border:1px solid #C7D2FE;padding:20px 24px;margin-bottom:16px">'
        '<div style="display:flex;align-items:center;gap:12px">'
        '<span style="font-size:26px">🤖</span>'
        '<div>'
        '<div style="font-size:16px;font-weight:800;color:#3730A3">AI Analysis</div>'
        '<div style="font-size:12px;color:#6366F1;margin-top:2px">'
        'Powered by Gemini 2.5 Flash · Analyses all 4 quadrants'
        '</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_btn, col_note = st.columns([2, 3])
    with col_btn:
        gen_clicked = st.button("✨  Generate AI Analysis", type="primary",
                                use_container_width=True, key="btn_overall_ai")
    with col_note:
        st.markdown(
            '<div class="th-card-muted" style="padding:10px 14px">'
            '<span class="th-text-muted" style="font-size:12px">'
            'Sends full product data to Gemini. Results appear as expandable insight cards below.'
            '</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    if gen_clicked:
        with st.spinner("Generating insights with Gemini…"):
            ai_data = prepare_full_ai_data(
                data["q1"], data["q2"], data["q3"], data["q4"], monthly, all_df,
            )
            ins_list, err = generate_overall_ai_insights(ai_data)
            st.session_state["s2_ai_insights"] = (ins_list, err)

    if "s2_ai_insights" in st.session_state:
        ins_list, err = st.session_state["s2_ai_insights"]
        if err:
            st.error(err)
        elif ins_list:
            st.markdown(
                f'<div style="font-size:12px;font-weight:600;color:#059669;margin:10px 0 8px">'
                f'✅ {len(ins_list)} insights ready</div>',
                unsafe_allow_html=True,
            )
            render_ai_insights(ins_list)
        else:
            st.warning("No insights returned. Please try again.")


# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════

if "_nav_page" in st.session_state:
    _forced_page = st.session_state.pop("_nav_page")
else:
    _forced_page = None

with st.sidebar:
    try:
        st.image("growify_studio_logo.jpg", width=125)
    except Exception:
        pass

    st.markdown(
        '<div style="padding:8px 4px 0">'
        '<div style="font-size:16px;font-weight:800;color:#F1F5F9">Growify</div>'
        '<div style="font-size:11px;color:#475569;margin-top:2px">Product Performance Marketing</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:1px;background:#1E293B;margin:16px 0"></div>',
                unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
        'letter-spacing:.1em;margin-bottom:8px;padding:0 4px">Navigation</div>',
        unsafe_allow_html=True,
    )

    _nav_options = ["📊 Product Analysis", "🔲 Quadrant View", "📋 Discount Vs Non Discount"]

    if _forced_page == "🔲 Quadrant View":
        st.session_state["_current_page"] = "🔲 Quadrant View"

    _default_page = st.session_state.get("_current_page", "📊 Product Analysis")
    _nav_index    = _nav_options.index(_default_page) if _default_page in _nav_options else 0

    page = st.radio("Section", _nav_options, index=_nav_index, label_visibility="collapsed")
    st.session_state["_current_page"] = page

    st.markdown('<div style="height:1px;background:#1E293B;margin:16px 0"></div>',
                unsafe_allow_html=True)

    if page == "📋 Discount Vs Non Discount":
        st.markdown(
            '<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:.1em;margin-bottom:12px">Settings</div>',
            unsafe_allow_html=True,
        )
        brand_name = st.text_input("Brand Name", value="Brand", key="brand_name",
                                   placeholder="Your brand name…")
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:11px;color:#64748B;margin-bottom:8px">Insight Thresholds</div>',
                    unsafe_allow_html=True)
        st.slider("High Spend (%)",  50, 300, 100, 10, key="s1_sp")
        st.slider("Low Revenue (%)", 10, 200, 100, 10, key="s1_rv")
        st.markdown('<div style="height:1px;background:#1E293B;margin:16px 0"></div>',
                    unsafe_allow_html=True)
        if st.button("▶  Run Discount Analysis", type="primary", use_container_width=True):
            st.session_state["_run_s1"] = True
            st.rerun()

    elif page == "🔲 Quadrant View":
        st.markdown(
            '<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:.1em;margin-bottom:12px">Settings</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div style="font-size:11px;color:#64748B;margin-bottom:8px">Quadrant Thresholds</div>',
                    unsafe_allow_html=True)

        s2_sp_val = st.slider("High Spend (%)",   50, 300, 100, 10, key="s2_sp")
        s2_rv_val = st.slider("High Revenue (%)", 50, 300, 100, 10, key="s2_rv")

        _prev_sp = st.session_state.get("_prev_s2_sp", s2_sp_val)
        _prev_rv = st.session_state.get("_prev_s2_rv", s2_rv_val)
        if (s2_sp_val != _prev_sp or s2_rv_val != _prev_rv) and "s2_data" in st.session_state:
            st.session_state["_prev_s2_sp"] = s2_sp_val
            st.session_state["_prev_s2_rv"] = s2_rv_val
            _d      = st.session_state["s2_data"]
            _all_df = _d["all"]
            _avg_sp = _all_df["Spend"].mean()   if "Spend"   in _all_df.columns else 0
            _avg_rv = _all_df["Revenue"].mean() if "Revenue" in _all_df.columns else 0
            _sp_cut = _avg_sp * s2_sp_val / 100
            _rv_cut = _avg_rv * s2_rv_val / 100
            _cols   = [c for c in ["Product ID","Product Title","Spend","Revenue","ROI"]
                       if c in _all_df.columns]
            _d["sp_cut"] = _sp_cut; _d["rv_cut"] = _rv_cut
            _d["avg_sp"] = _avg_sp; _d["avg_rv"] = _avg_rv
            _d["q1"] = _all_df[(_all_df["Revenue"]>=_rv_cut)&(_all_df["Spend"]< _sp_cut)][_cols].sort_values("Revenue",ascending=False).reset_index(drop=True)
            _d["q2"] = _all_df[(_all_df["Revenue"]>=_rv_cut)&(_all_df["Spend"]>=_sp_cut)][_cols].sort_values("Revenue",ascending=False).reset_index(drop=True)
            _d["q3"] = _all_df[(_all_df["Revenue"]< _rv_cut)&(_all_df["Spend"]>=_sp_cut)][_cols].sort_values("Spend",  ascending=False).reset_index(drop=True)
            _d["q4"] = _all_df[(_all_df["Revenue"]< _rv_cut)&(_all_df["Spend"]< _sp_cut)][_cols].sort_values("Revenue",ascending=False).reset_index(drop=True)
            st.session_state["s2_data"]   = _d
            st.session_state["s2_sp_pct"] = s2_sp_val
            st.session_state["s2_rv_pct"] = s2_rv_val
        else:
            st.session_state["_prev_s2_sp"] = s2_sp_val
            st.session_state["_prev_s2_rv"] = s2_rv_val

        if "s2_data" in st.session_state:
            _d   = st.session_state["s2_data"]
            _all = _d.get("all", pd.DataFrame())
            if not _all.empty:
                _avg_sp      = _all["Spend"].mean()   if "Spend"   in _all.columns else 0
                _avg_rv      = _all["Revenue"].mean() if "Revenue" in _all.columns else 0
                _live_sp_cut = _avg_sp * s2_sp_val / 100
                _live_rv_cut = _avg_rv * s2_rv_val / 100
                st.markdown(
                    f'<div style="background:#1E293B;border-radius:8px;padding:8px 10px;'
                    f'margin-top:4px;margin-bottom:8px">'
                    f'<div style="font-size:10px;color:#64748B;font-weight:600;'
                    f'text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">'
                    f'Live Cut-off Values</div>'
                    f'<div style="font-size:12px;font-weight:700;color:#A78BFA;margin-bottom:3px">'
                    f'Spend ≥ {compact_currency(_live_sp_cut)}'
                    f'<span style="font-size:10px;color:#64748B;margin-left:4px">'
                    f'({s2_sp_val}% of avg)</span></div>'
                    f'<div style="font-size:12px;font-weight:700;color:#34D399">'
                    f'Revenue ≥ {compact_currency(_live_rv_cut)}'
                    f'<span style="font-size:10px;color:#64748B;margin-left:4px">'
                    f'({s2_rv_val}% of avg)</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div style="font-size:10px;color:#475569;margin-top:2px;margin-bottom:8px">'
                f'Spend: {s2_sp_val}% of avg · Revenue: {s2_rv_val}% of avg'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div style="height:1px;background:#1E293B;margin:16px 0"></div>',
                    unsafe_allow_html=True)
        if st.button("▶  Run Product Analysis", type="primary", use_container_width=True):
            st.session_state["_run_s2"] = True
            st.rerun()

    else:
        # ── Product Analysis sidebar — averages per product ───────────
        if "ov_data" in st.session_state:
            _df         = st.session_state["ov_data"]
            _has_google = st.session_state.get("ov_has_google", False)
            n           = _df["Product ID"].nunique() or 1

            st.markdown(
                '<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
                'letter-spacing:.1em;margin-bottom:10px">Averages per Product</div>',
                unsafe_allow_html=True,
            )

            def _sb_kpi(label, value, color):
                st.markdown(
                    f'<div style="background:#1E293B;border-radius:8px;padding:8px 12px;'
                    f'margin-bottom:6px;border-left:3px solid {color}">'
                    f'<div style="font-size:10px;color:#64748B;font-weight:600;'
                    f'text-transform:uppercase;letter-spacing:.06em">{label}</div>'
                    f'<div style="font-size:15px;font-weight:700;color:{color};margin-top:2px">'
                    f'{value}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            if "Meta Spend" in _df.columns:
                _sb_kpi("Avg Meta Spend", f"₹{_df['Meta Spend'].sum()/n:,.0f}", "#60A5FA")
            if _has_google and "Google Cost" in _df.columns:
                _sb_kpi("Avg Google Spend", f"₹{_df['Google Cost'].sum()/n:,.0f}", "#FBBF24")
            if "Total Spend" in _df.columns:
                _sb_kpi("Avg Total Spend", f"₹{_df['Total Spend'].sum()/n:,.0f}", "#A78BFA")
            if "Shopify Revenue" in _df.columns:
                _sb_kpi("Avg Revenue", f"₹{_df['Shopify Revenue'].sum()/n:,.0f}", "#34D399")
            if "ROI" in _df.columns and "Total Spend" in _df.columns:
                _ts = _df["Total Spend"].sum()
                _rv = _df["Shopify Revenue"].sum() if "Shopify Revenue" in _df.columns else 0
                _avg_roi = _rv / _ts if _ts else 0
                _sb_kpi("Avg ROI", f"{_avg_roi:.2f}x", "#34D399")
            if "Landing Page Views" in _df.columns:
                _avg_lpv = int(_df["Landing Page Views"].sum() / n)
                _sb_kpi("Avg LPV", f"{_avg_lpv:,}", "#60A5FA")
        else:
            st.markdown(
                '<div style="background:#1E293B;border-radius:10px;padding:14px;'
                'border:1px dashed #334155">'
                '<div style="font-size:12px;color:#475569;text-align:center;line-height:1.6">'
                'Upload Meta + Shopify<br>then run Merge & Analyse<br>to see averages here'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════
#  ROUTE
# ══════════════════════════════════════════════════════════════════════

if page == "📊 Product Analysis":
    render_overall_view()
elif page == "📋 Discount Vs Non Discount":
    render_discount_view()
else:
    render_quadrant_view()