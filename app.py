# ╔══════════════════════════════════════════════════════════════════════╗
# ║  app.py  —  Brand Analysis Tool  (modular, v10 — theme-aware UI)   ║
# ╚══════════════════════════════════════════════════════════════════════╝

import streamlit as st
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


# ══════════════════════════════════════════════════════════════════════
#  UI COMPONENT HELPERS  (all using CSS variables via classes)
# ══════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = "", icon: str = ""):
    sub_html = (
        f'<p class="th-page-sub">{subtitle}</p>' if subtitle else ""
    )
    st.markdown(
        f'<div class="th-page-header">'
        f'<div class="th-page-title">{icon} {title}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "", accent: str = "#2563EB"):
    sub_html = (
        f'<div class="th-section-sub">{subtitle}</div>' if subtitle else ""
    )
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
    """items: list of (label, value, accent_color, bg_color)"""
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
    """Source file upload header card."""
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
}


def _fmt_val(v, fmt: str) -> str:
    if fmt == "currency": return f"₹{v:,.0f}"
    if fmt == "roi":      return f"{v:.2f}x"
    if fmt == "int":      return f"{int(v):,}"
    if fmt == "pct":      return f"{float(v)*100:.2f}%"
    return str(v)


# ══════════════════════════════════════════════════════════════════════
#  SECTION 0 — OVERALL VIEW
# ══════════════════════════════════════════════════════════════════════

def render_overall_view():
    page_header("Overall View",
                "Merge Meta, Shopify & Google exports into one unified performance table",
                "🌐")

    section_header("Upload Raw Exports",
                   "Drop your unmodified platform exports below", "#2563EB")
    cleaned = render_upload_panel("ov", show_google=True, google_optional=True)

    st.markdown("<div style='margin:12px 0'></div>", unsafe_allow_html=True)
    btn_col, _ = st.columns([2, 5])
    with btn_col:
        run_ov = st.button("▶  Merge & Analyse", type="primary",
                           key="btn_run_ov", use_container_width=True)

    if run_ov:
        if not cleaned["ready"]:
            st.error("Please upload at least Meta and Shopify files before running.")
            return
        with st.spinner("Merging data sources…"):
            try:
                merged_df, has_month = run_overall_view(
                    cleaned["meta_df"],
                    cleaned["shopify_df"],
                    cleaned["google_df"],
                )
                st.session_state["ov_data"]       = merged_df
                st.session_state["ov_has_month"]  = has_month
                st.session_state["ov_has_google"] = cleaned["google_df"] is not None
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
                return

    if "ov_data" not in st.session_state:
        if cleaned["ready"]:
            render_clean_preview(cleaned)
        else:
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

    render_clean_preview(cleaned)
    df         = st.session_state["ov_data"].copy()
    has_month  = st.session_state["ov_has_month"]
    has_google = st.session_state.get("ov_has_google", False)

    # ── KPIs ─────────────────────────────────────────────────────────
    total_meta   = df["Meta Spend"].sum()      if "Meta Spend"      in df.columns else 0
    total_google = df["Google Cost"].sum()     if "Google Cost"     in df.columns else 0
    total_spend  = df["Total Spend"].sum()     if "Total Spend"     in df.columns else 0
    total_rev    = df["Shopify Revenue"].sum() if "Shopify Revenue" in df.columns else 0
    overall_roi  = total_rev / total_spend if total_spend else 0

    divider()
    kpi_row([
        ("Total Products", f"{df['Product ID'].nunique():,}", "#0F172A", "#F8FAFC"),
        ("Meta Spend",     compact_currency(total_meta),      "#2563EB", "#EFF6FF"),
        ("Google Cost",    compact_currency(total_google),    "#D97706", "#FFF7ED"),
        ("Total Spend",    compact_currency(total_spend),     "#7C3AED", "#F5F3FF"),
        ("Revenue",        compact_currency(total_rev),       "#059669", "#ECFDF5"),
        ("Overall ROI",    f"{overall_roi:.2f}x",
         "#059669" if overall_roi >= 1 else "#DC2626",
         "#ECFDF5" if overall_roi >= 1 else "#FEF2F2"),
    ])
    divider()

    # ── Column selector ───────────────────────────────────────────────
    section_header("Columns & Filters",
                   "Select metrics to display — filters appear automatically", "#2563EB")

    available_cols = [c for c in _OV_COLS if c in df.columns]
    if not has_month and "Month" in available_cols:
        available_cols.remove("Month")
    if not has_google:
        available_cols = [c for c in available_cols if c not in ("Google Cost","Conversions")]

    default_sel = [
        c for c in ["Meta Spend","Google Cost","Total Spend","Shopify Revenue",
                    "ROI","Net Items Sold","CTR","CPM","Variant Title"]
        if c in available_cols
    ]

    col_options = list(available_cols)
    col_labels  = [
        f"{_OV_COLS.get(c,{}).get('label',c)}  [{_OV_COLS.get(c,{}).get('source','?')}]"
        for c in col_options
    ]
    label_to_key = {lbl: key for key, lbl in zip(col_options, col_labels)}

    selected_labels = st.multiselect(
        "Columns",
        options=col_labels,
        default=[col_labels[col_options.index(c)] for c in default_sel if c in col_options],
        label_visibility="collapsed",
        key="ov_col_sel",
        placeholder="Choose metrics to display…",
    )
    selected_cols = [label_to_key[lbl] for lbl in selected_labels]

    if not selected_cols:
        st.info("Select at least one metric above to begin filtering.")
        return

    # ── Quick search + period row ─────────────────────────────────────
    srch_a, srch_b, srch_c = st.columns([3, 3, 2])
    with srch_a:
        st.markdown(
            '<div class="th-filter-label" style="font-size:11px;font-weight:600;'
            'margin-bottom:4px">🔎 Product Search</div>',
            unsafe_allow_html=True,
        )
        search_text = st.text_input(
            "Search", placeholder="Product title or ID…",
            label_visibility="collapsed", key="ov_search",
        )

    with srch_b:
        if "Variant Title" in selected_cols and "Variant Title" in df.columns:
            st.markdown(
                '<div class="th-filter-label" style="font-size:11px;font-weight:600;'
                'margin-bottom:4px">🏷 Variant Search</div>',
                unsafe_allow_html=True,
            )
            variant_search = st.text_input(
                "Variant", placeholder="e.g. XL, M, Blue…",
                label_visibility="collapsed", key="ov_variant_search",
            )
        else:
            variant_search = ""

    with srch_c:
        st.markdown(
            '<div class="th-filter-label" style="font-size:11px;font-weight:600;'
            'margin-bottom:4px">📅 Period</div>',
            unsafe_allow_html=True,
        )
        if has_month and "Month" in df.columns:
            months_avail  = sorted(df["Month"].dropna().unique().tolist())
            period_options = ["All Months", "Last 7 Days"] + months_avail
            sel_period = st.selectbox("Period", period_options,
                                      label_visibility="collapsed", key="ov_period")
            if sel_period == "All Months":
                sel_months = months_avail; _last7 = False
            elif sel_period == "Last 7 Days":
                sel_months = months_avail; _last7 = True
            else:
                sel_months = [sel_period]; _last7 = False
        else:
            sel_months = None; _last7 = False

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Metric filters (inside expander) ─────────────────────────────
    filter_specs = {}
    num_fmts = ("currency", "int", "roi", "pct")
    num_cols  = [c for c in selected_cols if _OV_COLS.get(c, {}).get("fmt") in num_fmts]
    text_cols = [c for c in selected_cols
                 if _OV_COLS.get(c, {}).get("fmt") == "text"
                 and c not in ("Month", "Variant Title")]

    with st.expander("⚙️  Metric Filters", expanded=False):
        if num_cols:
            st.markdown(
                '<div class="th-text-faint" style="font-size:11px;margin-bottom:12px">'
                'Set a condition for each metric — only matching rows will be shown.'
                '</div>',
                unsafe_allow_html=True,
            )
            for i in range(0, len(num_cols), 3):
                chunk    = num_cols[i:i+3]
                row_cols = st.columns(len(chunk))
                for rc, col_key in zip(row_cols, chunk):
                    mi      = _OV_COLS[col_key]
                    col_min = float(df[col_key].min()) if col_key in df.columns else 0.0
                    col_max = float(df[col_key].max()) if col_key in df.columns else 100.0
                    fmt_str = ("%.4f" if mi["fmt"] == "pct"
                               else "%.2f" if mi["fmt"] == "roi" else "%.0f")
                    step    = (0.0001 if mi["fmt"] == "pct"
                               else 0.01 if mi["fmt"] == "roi" else 1.0)
                    with rc:
                        # filter cell — uses CSS class, no hardcoded bg
                        st.markdown(
                            f'<div class="th-filter-cell">'
                            f'<div class="th-filter-metric-title" style="color:{mi["color"]}">'
                            f'{mi["label"]}</div>',
                            unsafe_allow_html=True,
                        )
                        op_col, val_col = st.columns([1, 2])
                        with op_col:
                            st.markdown(
                                '<div class="th-filter-label">Operator</div>',
                                unsafe_allow_html=True,
                            )
                            operator = st.selectbox(
                                f"op_{col_key}", options=["—",">","<","="],
                                label_visibility="collapsed", key=f"ov_op_{col_key}",
                            )
                        with val_col:
                            st.markdown(
                                '<div class="th-filter-label">Value</div>',
                                unsafe_allow_html=True,
                            )
                            filter_val = st.number_input(
                                f"val_{col_key}", value=col_min,
                                step=step, format=fmt_str,
                                label_visibility="collapsed", key=f"ov_val_{col_key}",
                            )
                        st.markdown("</div>", unsafe_allow_html=True)

                        if operator != "—":
                            filter_specs[col_key] = (operator, filter_val)

        if text_cols:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            for col_key in text_cols:
                mi   = _OV_COLS[col_key]
                uniq = sorted(df[col_key].dropna().unique().tolist()) if col_key in df.columns else []
                if uniq:
                    st.markdown(
                        f'<div style="font-size:11px;font-weight:600;color:{mi["color"]};'
                        f'margin-bottom:3px">{mi["label"]}</div>',
                        unsafe_allow_html=True,
                    )
                    sel_vals = st.multiselect(f"filter_{col_key}", uniq, default=uniq,
                                              label_visibility="collapsed", key=f"ov_txt_{col_key}")
                    filter_specs[col_key] = ("text", sel_vals)

        if not num_cols and not text_cols:
            st.markdown(
                '<div class="th-text-faint" style="font-size:12px;text-align:center;'
                'padding:12px">Select metric columns above to see filters here.</div>',
                unsafe_allow_html=True,
            )

        _, rst_col = st.columns([6, 1])
        with rst_col:
            if st.button("↺ Reset", key="ov_reset"):
                keys_to_del = ["ov_search","ov_period","ov_col_sel","ov_variant_search"]
                for c in available_cols:
                    keys_to_del += [f"ov_op_{c}", f"ov_val_{c}", f"ov_txt_{c}"]
                for k in keys_to_del:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    # ── Apply filters ─────────────────────────────────────────────────
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
        fdf = fdf[fdf["Variant Title"].str.lower()
                  .str.contains(variant_search.strip().lower(), na=False)]
    if _last7 and "Month" in fdf.columns:
        today  = datetime.date.today()
        cutoff = today - datetime.timedelta(days=7)
        def _month_in_last7(m):
            try:
                p = parse_month_start(m)
                if p is None: return False
                if hasattr(p, "date"): p = p.date()
                return p >= cutoff
            except Exception:
                return False
        fdf = fdf[fdf["Month"].apply(_month_in_last7)]

    for col_key, spec in filter_specs.items():
        if col_key not in fdf.columns:
            continue
        if spec[0] == "text":
            _, sel_vals = spec
            if sel_vals:
                fdf = fdf[fdf[col_key].isin(sel_vals)]
        else:
            op, fv = spec
            if op == ">": fdf = fdf[fdf[col_key] > fv]
            elif op == "<": fdf = fdf[fdf[col_key] < fv]
            elif op == "=": fdf = fdf[fdf[col_key] == fv]

    # ── Result strip ──────────────────────────────────────────────────
    n_shown     = len(fdf)
    n_total     = len(df)
    is_filtered = n_shown < n_total

    badge_color = "#2563EB" if not is_filtered else "#059669"
    filter_badge = (
        '<span style="background:#DBEAFE;border-radius:6px;padding:3px 10px;'
        'font-size:11px;color:#1E40AF;font-weight:600">Filters active</span>'
        if is_filtered else ""
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

    # Filtered summary KPIs
    if is_filtered and not fdf.empty:
        kpi_items = []
        for col_key in selected_cols:
            mi = _OV_COLS.get(col_key, {})
            if mi.get("fmt") in ("currency","int") and col_key in fdf.columns:
                kpi_items.append((mi["label"], _fmt_val(fdf[col_key].sum(), mi["fmt"]),
                                  mi["color"], mi["bg"]))
            elif mi.get("fmt") == "roi" and col_key in fdf.columns:
                sp  = fdf["Total Spend"].sum()      if "Total Spend"     in fdf.columns else 0
                rv  = fdf["Shopify Revenue"].sum()  if "Shopify Revenue" in fdf.columns else 0
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
    always_cols = ["Product ID", "Product Title"]
    if "Variant Title" in fdf.columns:
        always_cols.append("Variant Title")
    if has_month and "Month" in selected_cols and "Month" in fdf.columns:
        always_cols.append("Month")

    disp = fdf[[c for c in always_cols if c in fdf.columns]].copy()
    display_col_map: dict = {}

    for col_key in selected_cols:
        if col_key in always_cols or col_key not in fdf.columns:
            continue
        mi       = _OV_COLS.get(col_key, {})
        disp_lbl = mi.get("label", col_key)
        disp[disp_lbl] = fdf[col_key].apply(lambda v: _fmt_val(v, mi.get("fmt","text")))
        display_col_map[disp_lbl] = col_key

    disp_cols_data = [c for c in always_cols if c in disp.columns] + list(display_col_map.keys())

    # Totals
    totals_row = {c: ("∑ TOTAL" if c == "Product ID" else "") for c in always_cols}
    for disp_lbl, col_key in display_col_map.items():
        mi  = _OV_COLS.get(col_key, {})
        fmt = mi.get("fmt","text")
        if fmt in ("currency","int") and col_key in fdf.columns:
            totals_row[disp_lbl] = _fmt_val(fdf[col_key].sum(), fmt)
        elif fmt == "roi":
            sp = fdf["Total Spend"].sum()     if "Total Spend"     in fdf.columns else 0
            rv = fdf["Shopify Revenue"].sum() if "Shopify Revenue" in fdf.columns else 0
            totals_row[disp_lbl] = f"{rv/sp:.2f}x" if sp else "—"
        else:
            totals_row[disp_lbl] = ""

    # Totals pills — accent colours still accent, background is from column definition
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
        # Uses .th-totals-bar which maps to var(--surface-totals) — light/dark safe
        st.markdown(
            f'<div class="th-totals-bar">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.1em;margin-bottom:6px;" class="th-text-faint">'
            f'∑ Totals · {n_shown:,} rows</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px">{totals_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.dataframe(
        disp[disp_cols_data].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    # Grand totals dark bar — intentionally always dark (brand style), just like the sidebar
    st.markdown(
        f'<div class="th-grand-bar">'
        f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:8px;" class="th-text-grandtot">'
        f'∑ Grand Totals — {n_shown:,} products</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px">{totals_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Download ──────────────────────────────────────────────────────
    dl1, dl2 = st.columns([2, 4])
    with dl1:
        export_cols = ["Product ID","Product Title"]
        if has_month and "Month" in df.columns:
            export_cols.append("Month")
        for col_key in selected_cols:
            if col_key not in export_cols and col_key in fdf.columns:
                export_cols.append(col_key)
        csv_buf = fdf[export_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇  Download CSV",
            data=csv_buf,
            file_name="overall_view_filtered.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    with dl2:
        col_names = ", ".join([_OV_COLS.get(c, {}).get("label", c) for c in selected_cols])
        st.markdown(
            f'<div class="th-card-muted" style="padding:10px 14px;height:100%;'
            f'display:flex;align-items:center;">'
            f'<span class="th-text-muted" style="font-size:12px">'
            f'Exporting <strong class="th-text-primary">{n_shown:,} rows</strong>'
            f' with <strong class="th-text-primary">{len(selected_cols)} columns</strong>'
            f'</span></div>',
            unsafe_allow_html=True,
        )


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
            'text-align:center;margin-bottom:12px;" >'
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
        disp = disp.rename(columns={
            "Product ID":"PID","Product Title":"Title",
            "Spend":"Spend (INR)","Revenue":"Revenue (INR)",
        })
        st.dataframe(disp, use_container_width=True, hide_index=True)


def render_discount_view():
    page_header("Discount vs Non-Discount",
                "Compare discounted and non-discounted product performance", "📋")

    run_s1     = st.session_state.get("_run_s1",    False)
    spend_pct  = st.session_state.get("s1_sp",      100)
    rev_pct    = st.session_state.get("s1_rv",      100)
    brand_name = st.session_state.get("brand_name", "Brand")

    section_header("Upload Raw Exports",
                   "Meta + Shopify required · Discount list is the 3rd file", "#2563EB")

    col1, col2, col3 = st.columns(3)
    with col1:
        upload_card("#2563EB","#EFF6FF","① Meta Ads",
                    "Raw export — Product ID split + cleaned automatically")
        meta_file = st.file_uploader("Meta CSV", type=["csv","xlsx"],
                                      key="s1_meta", label_visibility="collapsed")
        if meta_file is not None:
            st.session_state["s1_meta_bytes"] = meta_file.read()
            st.session_state["s1_meta_name"]  = meta_file.name
            meta_file.seek(0)

    with col2:
        upload_card("#059669","#ECFDF5","② Shopify",
                    "Raw export — variant ID renamed automatically")
        shopify_file = st.file_uploader("Shopify CSV", type=["csv","xlsx"],
                                         key="s1_shop", label_visibility="collapsed")
        if shopify_file is not None:
            st.session_state["s1_shopify_bytes"] = shopify_file.read()
            st.session_state["s1_shopify_name"]  = shopify_file.name
            shopify_file.seek(0)

    with col3:
        upload_card("#D97706","#FFF7ED","③ Discount Product List",
                    "CSV with Product ID column of discounted SKUs")
        discount_file = st.file_uploader("Discount list", type=["csv","xlsx"],
                                          key="s1_disc", label_visibility="collapsed")
        if discount_file is not None:
            st.session_state["s1_disc_bytes"] = discount_file.read()
            st.session_state["s1_disc_name"]  = discount_file.name
            discount_file.seek(0)

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
        ("Total Products",  f"{merged['Product ID'].nunique():,}",                         "#0F172A","#F8FAFC"),
        ("Discounted",      f"{merged[merged['Is_Discounted']]['Product ID'].nunique():,}", "#2563EB","#EFF6FF"),
        ("Non-Discounted",  f"{merged[~merged['Is_Discounted']]['Product ID'].nunique():,}","#059669","#ECFDF5"),
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
            section_header("Performance Charts", "Visual comparison across months", "#059669")
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
                       "Full analysis with monthly + overall insight sheets", "#7C3AED")
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
        f'padding:20px 22px;margin-bottom:2px;transition:box-shadow 0.2s">'
        f'<div style="display:flex;align-items:flex-start;justify-content:space-between;'
        f'flex-wrap:wrap;gap:10px">'
        f'<div>'
        f'<div style="font-size:20px;margin-bottom:4px">{cfg["icon"]}</div>'
        f'<div class="th-text-primary" style="font-size:15px;font-weight:700;margin-bottom:3px">'
        f'{cfg["label"]}</div>'
        f'<div class="th-text-faint" style="font-size:11px;max-width:200px;line-height:1.4">'
        f'{desc}</div>'
        f'</div>'
        f'<div style="display:flex;gap:24px;flex-wrap:wrap">'
        f'<div style="text-align:right">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:2px">Products</div>'
        f'<div style="font-size:26px;font-weight:800;color:{cfg["color"]}">{n}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:2px">Spend</div>'
        f'<div class="th-text-secondary" style="font-size:16px;font-weight:700">'
        f'{compact_currency(sp)}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:2px">Revenue</div>'
        f'<div class="th-text-secondary" style="font-size:16px;font-weight:700">'
        f'{compact_currency(rv)}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div class="th-text-faint" style="font-size:9px;text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:2px">ROI</div>'
        f'<div style="font-size:26px;font-weight:800;color:{cfg["color"]}">'
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


def render_quadrant_view():
    page_header("Quadrant View",
                "Products split into 4 performance groups with AI insights", "🔲")

    run_s2       = st.session_state.get("_run_s2",  False)
    s2_spend_pct = st.session_state.get("s2_sp",    100)
    s2_rev_pct   = st.session_state.get("s2_rv",    100)

    section_header("Upload Raw Exports", "Meta + Shopify exports — auto-cleaned", "#2563EB")

    col1, col2 = st.columns(2)
    with col1:
        upload_card("#2563EB","#EFF6FF","① Meta Ads","Raw export — auto-cleaned")
        s2_meta_file = st.file_uploader("Meta CSV", type=["csv","xlsx"],
                                         key="s2_meta", label_visibility="collapsed")
        if s2_meta_file is not None:
            st.session_state["s2_meta_bytes"] = s2_meta_file.read()
            st.session_state["s2_meta_name"]  = s2_meta_file.name
            s2_meta_file.seek(0)

    with col2:
        upload_card("#059669","#ECFDF5","② Shopify","Raw export — auto-cleaned")
        s2_shopify_file = st.file_uploader("Shopify CSV", type=["csv","xlsx"],
                                            key="s2_shop", label_visibility="collapsed")
        if s2_shopify_file is not None:
            st.session_state["s2_shopify_bytes"] = s2_shopify_file.read()
            st.session_state["s2_shopify_name"]  = s2_shopify_file.name
            s2_shopify_file.seek(0)

    if run_s2:
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
            'Meta + Shopify required</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    data     = st.session_state["s2_data"]
    all_df   = data["all"];    monthly  = data["monthly"]
    sp_cut   = data["sp_cut"]; rv_cut   = data["rv_cut"]
    total_sp = all_df["Spend"].sum()
    total_rv = all_df["Revenue"].sum()

    divider()
    kpi_row([
        ("Total Products", f"{len(all_df):,}",         "#0F172A","#F8FAFC"),
        ("Total Spend",    compact_currency(total_sp),  "#64748B","#F8FAFC"),
        ("Total Revenue",  compact_currency(total_rv),  "#059669","#ECFDF5"),
        ("Overall ROI",    fmt_roi(total_rv/total_sp) if total_sp else "—", "#7C3AED","#F5F3FF"),
    ])

    st.markdown(
        f'<div class="th-card-muted" style="padding:10px 16px;margin:12px 0;'
        f'display:flex;flex-wrap:wrap;gap:20px">'
        f'<span class="th-text-muted" style="font-size:12px">'
        f'<strong class="th-text-primary">High Spend</strong> ≥ {compact_currency(sp_cut)}'
        f'<span style="color:#2563EB;margin-left:4px">'
        f'({st.session_state.get("s2_sp_pct",100)}% of avg)</span></span>'
        f'<span class="th-text-muted" style="font-size:12px">'
        f'<strong class="th-text-primary">High Revenue</strong> ≥ {compact_currency(rv_cut)}'
        f'<span style="color:#2563EB;margin-left:4px">'
        f'({st.session_state.get("s2_rv_pct",100)}% of avg)</span></span>'
        f'<span class="th-text-muted" style="font-size:12px">'
        f'<strong class="th-text-primary">Months:</strong>'
        f'<span style="color:#7C3AED;margin-left:4px">{data["total_months"]}</span></span>'
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

    # ── AI Analysis ───────────────────────────────────────────────────
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
#  SIDEBAR  — UNCHANGED from v10
# ══════════════════════════════════════════════════════════════════════

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

    page = st.radio(
        "Section",
        ["🌐 Overall View","🔲 Quadrant View","📋 Discount Vs Non Discount"],
        label_visibility="collapsed",
    )

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
        st.slider("High Spend (%)",   50, 300, 100, 10, key="s2_sp")
        st.slider("High Revenue (%)", 50, 300, 100, 10, key="s2_rv")
        st.markdown('<div style="height:1px;background:#1E293B;margin:16px 0"></div>',
                    unsafe_allow_html=True)
        if st.button("▶  Run Product Analysis", type="primary", use_container_width=True):
            st.session_state["_run_s2"] = True
            st.rerun()

    else:
        # Overall View — avg KPIs when data loaded
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

if page == "🌐 Overall View":
    render_overall_view()
elif page == "📋 Discount Vs Non Discount":
    render_discount_view()
else:
    render_quadrant_view()