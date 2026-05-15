# ╔══════════════════════════════════════════════════════════════════════╗
# ║  cleaning_ui.py  —  Upload + Clean + Preview UI component          ║
# ║  Renders the file upload panel with live cleaning feedback          ║
# ╚══════════════════════════════════════════════════════════════════════╝

import streamlit as st
import pandas as pd
import io
from data_cleaner import (
    clean_meta, clean_shopify, clean_google, cleaning_summary, _read_file
)


# ──────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ──────────────────────────────────────────────────────────────────────

_SOURCE_META = {
    "label":       "Meta Ads",
    "color":       "#2563EB",
    "bg":          "#EFF6FF",
    "border":      "#93C5FD",
    "icon":        "",
    "desc":        "Product ID · Product Title · Month · Amount Spent · LPV · CTR · CPM",
    "raw_example": "Product ID column contains: 'ID, Title mixed together'",
    "clean_note":  "Splits Product ID + Title · drops Reporting start/end · normalises numerics",
}

_SOURCE_SHOPIFY = {
    "label":       "Shopify",
    "color":       "#059669",
    "bg":          "#ECFDF5",
    "border":      "#6EE7B7",
    "icon":        "",
    "desc":        "Product ID · Product Title · Month · Variant · Items Sold · Net Sales",
    "raw_example": "'Product variant ID' used as key — renamed to Product ID",
    "clean_note":  "Renames variant ID → Product ID · normalises column names · keeps relevant cols",
}

_SOURCE_GOOGLE = {
    "label":       "Google Ads",
    "color":       "#D97706",
    "bg":          "#FFF7ED",
    "border":      "#FCD34D",
    "icon":        "",
    "desc":        "Product ID · Product Title · Month · Cost · Conversions",
    "raw_example": "First 2 rows are metadata · Item ID is 'shopify_in_X_<id>' · Month is 'April 2026'",
    "clean_note":  "Skips metadata rows · extracts numeric ID from Item ID · converts month format",
}


# ──────────────────────────────────────────────────────────────────────
#  SINGLE SOURCE UPLOAD CARD
# ──────────────────────────────────────────────────────────────────────

def _source_header(cfg, optional=False):
    opt_badge = (
        '<span style="background:#F1F5F9;border:1px solid #CBD5E1;border-radius:999px;'
        'padding:1px 8px;font-size:10px;color:#64748B;font-weight:600;margin-left:6px">OPTIONAL</span>'
        if optional else ""
    )
    st.markdown(f"""
    <div style="background:{cfg['bg']};border-radius:10px;padding:10px 14px;
                margin-bottom:8px;border-left:3px solid {cfg['color']}">
      <div style="font-size:12px;font-weight:700;color:{cfg['color']}">
        {cfg['icon']}  {cfg['label']}{opt_badge}
      </div>
      <div style="font-size:11px;color:#64748B;margin-top:3px">{cfg['desc']}</div>
    </div>""", unsafe_allow_html=True)


# def _cleaning_diff_card(summary: dict, warnings: list, cfg: dict):
#     """Show a compact before/after diff after cleaning."""
#     col_added   = summary.get("cols_added",   [])
#     col_removed = summary.get("cols_removed", [])
#     rows_dropped = summary.get("rows_dropped", 0)

#     changes = []
#     if col_added:
#         changes.append(
#             f"<span style='color:#059669'>+ {', '.join(col_added)}</span>"
#         )
#     if col_removed:
#         changes.append(
#             f"<span style='color:#DC2626;text-decoration:line-through'>"
#             f"{', '.join(col_removed)}</span>"
#         )
#     if rows_dropped > 0:
#         changes.append(
#             f"<span style='color:#D97706'>{rows_dropped} empty rows removed</span>"
#         )

#     changes_html = " · ".join(changes) if changes else "<span style='color:#94A3B8'>No structural changes</span>"

#     warn_html = ""
#     if warnings:
#         warn_items = "".join(
#             f"<div style='font-size:11px;color:#D97706;padding:2px 0'>⚠ {w}</div>"
#             for w in warnings
#         )
#         warn_html = f"""
#         <div style="background:#FFF7ED;border-radius:6px;padding:8px 10px;
#                     margin-top:6px;border:1px solid #FCD34D">
#           {warn_items}
#         </div>"""

#     st.markdown(f"""
#     <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
#                 padding:10px 14px;margin-top:6px">
#       <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
#         <span style="font-size:18px">✅</span>
#         <span style="font-size:12px;font-weight:700;color:#0F172A">
#           Cleaned: {summary['clean_rows']:,} rows · {len(summary['clean_columns'])} columns
#         </span>
#         <span style="font-size:11px;color:#94A3B8">
#           (was {summary['raw_rows']:,} rows · {len(summary['raw_columns'])} cols)
#         </span>
#       </div>
#       <div style="font-size:11px;line-height:1.8">{changes_html}</div>
#       {warn_html}
#     </div>""", unsafe_allow_html=True)


# def _clean_col_table(cfg: dict):
#     """Small reference card showing what the cleaner does."""
#     st.markdown(f"""
#     <div style="background:#FFFFFF;border:1px solid {cfg['border']};border-radius:8px;
#                 padding:10px 14px;margin-top:4px">
#       <div style="font-size:11px;font-weight:700;color:{cfg['color']};
#                   text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px">
#         🔧 Auto-cleaning steps
#       </div>
#       <div style="font-size:11px;color:#475569;line-height:1.8">
#         <strong>Raw:</strong> {cfg['raw_example']}<br>
#         <strong>Cleaned:</strong> {cfg['clean_note']}
#       </div>
#     </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
#  MAIN UPLOAD PANEL  (renders all 3 uploaders + cleaning feedback)
# ──────────────────────────────────────────────────────────────────────

def render_upload_panel(
    section_key: str,
    show_google: bool = True,
    google_optional: bool = True,
) -> dict:
    """
    Renders upload UI for Meta, Shopify, and (optionally) Google files.

    Returns a dict:
      {
        "meta_df":    pd.DataFrame | None,
        "shopify_df": pd.DataFrame | None,
        "google_df":  pd.DataFrame | None,
        "meta_raw":   pd.DataFrame | None,   # for diff preview
        "shopify_raw": pd.DataFrame | None,
        "google_raw":  pd.DataFrame | None,
        "all_warnings": list[str],
        "ready": bool,   # True when minimum required files are clean
      }
    """
    result = {
        "meta_df":    None,
        "shopify_df": None,
        "google_df":  None,
        "meta_raw":   None,
        "shopify_raw": None,
        "google_raw":  None,
        "all_warnings": [],
        "ready": False,
    }

    n_cols = 3 if show_google else 2
    cols   = st.columns(n_cols)

    # ── META ────────────────────────────────────────────────────────
    with cols[0]:
        _source_header(_SOURCE_META)
        meta_file = st.file_uploader(
            "Meta CSV/XLSX",
            type=["csv", "xlsx"],
            key=f"{section_key}_meta_upload",
            label_visibility="collapsed",
        )
        if meta_file:
            with st.spinner("Cleaning Meta data…"):
                try:
                    raw_df = _read_file_safe(meta_file)
                    meta_file.seek(0)
        
                    clean_df, warns = clean_meta(meta_file)
        
                    result["meta_df"] = clean_df
                    result["meta_raw"] = raw_df
        
                    # persist
                    st.session_state[f"{section_key}_meta_df"] = clean_df
                    st.session_state[f"{section_key}_meta_raw"] = raw_df
        
                    result["all_warnings"].extend(warns)
        
                except Exception as e:
                    st.error(f"Meta cleaning failed: {e}")
        
        elif f"{section_key}_meta_df" in st.session_state:
            result["meta_df"] = st.session_state[f"{section_key}_meta_df"]
            result["meta_raw"] = st.session_state.get(f"{section_key}_meta_raw")
        if meta_file:
            with st.spinner("Cleaning Meta data…"):
                try:
                    raw_df = _read_file_safe(meta_file)
                    meta_file.seek(0)
                    clean_df, warns = clean_meta(meta_file)
                    summary = cleaning_summary(raw_df, clean_df, "Meta")
                    # _cleaning_diff_card(summary, warns, _SOURCE_META)
                    result["meta_df"]  = clean_df
                    result["meta_raw"] = raw_df
                    result["all_warnings"].extend(warns)
                except Exception as e:
                    st.error(f"Meta cleaning failed: {e}")
        # else:
        #     _clean_col_table(_SOURCE_META)

    # ── SHOPIFY ─────────────────────────────────────────────────────
    with cols[1]:
        _source_header(_SOURCE_SHOPIFY)
        shopify_file = st.file_uploader(
            "Shopify CSV/XLSX",
            type=["csv", "xlsx"],
            key=f"{section_key}_shopify_upload",
            label_visibility="collapsed",
        )
        if shopify_file:
            with st.spinner("Cleaning Shopify data…"):
                try:
                    raw_df = _read_file_safe(shopify_file)
                    shopify_file.seek(0)
                    clean_df, warns = clean_shopify(shopify_file)
                    summary = cleaning_summary(raw_df, clean_df, "Shopify")
                    # _cleaning_diff_card(summary, warns, _SOURCE_SHOPIFY)
                    result["shopify_df"]  = clean_df
                    result["shopify_raw"] = raw_df
                    result["all_warnings"].extend(warns)
                except Exception as e:
                    st.error(f"Shopify cleaning failed: {e}")
        # else:
        #     _clean_col_table(_SOURCE_SHOPIFY)

    # ── GOOGLE ──────────────────────────────────────────────────────
    if show_google:
        with cols[2]:
            _source_header(_SOURCE_GOOGLE, optional=google_optional)
            google_file = st.file_uploader(
                "Google CSV/XLSX",
                type=["csv", "xlsx"],
                key=f"{section_key}_google_upload",
                label_visibility="collapsed",
            )
            if google_file:
                with st.spinner("Cleaning Google data…"):
                    try:
                        raw_df = _read_file_safe(google_file)
                        google_file.seek(0)
                        clean_df, warns = clean_google(google_file)
                        summary = cleaning_summary(raw_df, clean_df, "Google")
                        # _cleaning_diff_card(summary, warns, _SOURCE_GOOGLE)
                        result["google_df"]  = clean_df
                        result["google_raw"] = raw_df
                        result["all_warnings"].extend(warns)
                    except Exception as e:
                        st.error(f"Google cleaning failed: {e}")
            # else:
            #     _clean_col_table(_SOURCE_GOOGLE)
                # if google_optional:
                #     st.markdown("""
                #     <div style="background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:8px;
                #                 padding:8px 12px;font-size:11px;color:#94A3B8;margin-top:4px">
                #       Google data is optional. Analysis will run on Meta + Shopify only if not provided.
                #     </div>""", unsafe_allow_html=True)

    # ── Determine readiness ─────────────────────────────────────────
    meta_ok    = result["meta_df"]    is not None
    shopify_ok = result["shopify_df"] is not None
    google_ok  = result["google_df"]  is not None

    required_ok = meta_ok and shopify_ok
    result["ready"] = required_ok

    # ── Status strip ────────────────────────────────────────────────
    _render_status_strip(meta_ok, shopify_ok, google_ok,
                         google_optional=google_optional,
                         show_google=show_google)

    return result


# def _read_file_safe(file_obj) -> pd.DataFrame:
#     """Read a file object into a raw DataFrame without any cleaning."""
#     name = getattr(file_obj, "name", "")
#     file_obj.seek(0)
#     if isinstance(name, str) and name.lower().endswith((".xlsx", ".xls")):
#         df = pd.read_excel(file_obj)
#     else:
#         # Try header=0 first; if it looks like a Google file (metadata rows), header=2
#         df = pd.read_csv(file_obj)
#         # Heuristic: if first column value is "Campaign performance" or similar metadata
#         if df.columns[0].lower() in ("campaign performance", "report", "unnamed: 0"):
#             file_obj.seek(0)
#             df = pd.read_csv(file_obj, header=2)
#     file_obj.seek(0)
#     return df

def _read_file_safe(file_obj) -> pd.DataFrame:
    """Read a file object into a raw DataFrame without any cleaning."""
    name = getattr(file_obj, "name", "")
    file_obj.seek(0)

    if isinstance(name, str) and name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_obj)

    else:
        try:
            # Normal CSV read
            df = pd.read_csv(file_obj)

        except Exception:
            # Google files often have metadata rows
            file_obj.seek(0)
            try:
                df = pd.read_csv(
                    file_obj,
                    header=2,
                    engine="python",
                    on_bad_lines="skip"
                )
            except Exception:
                file_obj.seek(0)
                df = pd.read_csv(
                    file_obj,
                    engine="python",
                    on_bad_lines="skip"
                )

    file_obj.seek(0)
    return df

def _render_status_strip(meta_ok, shopify_ok, google_ok,
                          google_optional=True, show_google=True):
    sources = [
        ("Meta",    meta_ok,    "#2563EB", "#EFF6FF"),
        ("Shopify", shopify_ok, "#059669", "#ECFDF5"),
    ]
    if show_google:
        sources.append(
            ("Google", google_ok, "#D97706", "#FFF7ED")
        )

    pills = ""
    for name, ok, color, bg in sources:
        if ok:
            pills += f"""<span style="display:inline-flex;align-items:center;gap:5px;
                background:{bg};border:1.5px solid {color};border-radius:999px;
                padding:3px 12px;font-size:11px;font-weight:700;color:{color};margin:2px">
                ✓ {name} ready</span>"""
        else:
            opt_label = " (optional)" if name == "Google" and google_optional else " (required)"
            req_color = "#94A3B8" if name == "Google" and google_optional else "#DC2626"
            pills += f"""<span style="display:inline-flex;align-items:center;gap:5px;
                background:#F8FAFC;border:1.5px dashed #CBD5E1;border-radius:999px;
                padding:3px 12px;font-size:11px;font-weight:600;color:{req_color};margin:2px">
                ○ {name}{opt_label}</span>"""

    required_ready = meta_ok and shopify_ok
    if required_ready:
        overall_color = "#059669"
        overall_bg    = "#ECFDF5"
        overall_msg   = "✅ Ready to analyse"
    else:
        overall_color = "#64748B"
        overall_bg    = "#F8FAFC"
        overall_msg   = "⏳ Upload Meta + Shopify to continue"

    st.markdown(f"""
    <div style="background:{overall_bg};border:1px solid {overall_color}33;
                border-radius:10px;padding:10px 16px;margin-top:12px;
                display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
      <div style="display:flex;flex-wrap:wrap;gap:4px">{pills}</div>
      <div style="font-size:12px;font-weight:700;color:{overall_color}">{overall_msg}</div>
    </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
#  PREVIEW EXPANDER  (show cleaned sample)
# ──────────────────────────────────────────────────────────────────────

def render_clean_preview(cleaned_results: dict):
    """
    Renders an expander showing sample rows of each cleaned DataFrame.
    Call this after render_upload_panel returns a ready=True result.
    """
    with st.expander("🔍 Preview cleaned data (first 5 rows per source)", expanded=False):
        for source_key, label, color in [
            ("meta_df",    "Meta Ads",    "#2563EB"),
            ("shopify_df", "Shopify",     "#059669"),
            ("google_df",  "Google Ads",  "#D97706"),
        ]:
            df = cleaned_results.get(source_key)
            if df is not None and not df.empty:
                st.markdown(f"""
                <div style="font-size:12px;font-weight:700;color:{color};
                            margin:10px 0 4px;padding-left:4px">
                  {label}  ({len(df):,} rows · {len(df.columns)} cols)
                </div>""", unsafe_allow_html=True)
                st.dataframe(df.head(5), use_container_width=True, hide_index=True)