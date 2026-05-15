# ╔══════════════════════════════════════════════════════════════════════╗
# ║  ai_insights.py  —  AI data preparation + Gemini API + renderer   ║
# ╚══════════════════════════════════════════════════════════════════════╝

import json
import streamlit as st
import pandas as pd
from typing import Optional, Tuple, List
from analytics import compact_currency


# ──────────────────────────────────────────────────────────────────────
#  AI DATA PREPARATION
# ──────────────────────────────────────────────────────────────────────

def _spend_trend_label(series: pd.Series) -> str:
    if len(series) < 2:
        return "single_month"
    diffs = series.diff().dropna()
    mean  = series.mean()
    if all(diffs > 0):  return "increasing"
    if all(diffs < 0):  return "decreasing"
    if mean > 0 and diffs.abs().max() / mean <= 0.20:
        return "stable"
    return "volatile"


def _product_monthly_summary(pid: str, merged_monthly: pd.DataFrame) -> list:
    grp = merged_monthly[merged_monthly["Product ID"] == pid].sort_values("Month")
    rows = []
    for _, r in grp.iterrows():
        rows.append({
            "month":   r["Month"],
            "spend":   round(float(r["Spend"]),   2),
            "revenue": round(float(r["Revenue"]), 2),
            "roi":     round(float(r["Revenue"] / r["Spend"]), 2) if r["Spend"] > 0 else 0,
        })
    return rows


def _to_product_list(df: pd.DataFrame, merged_monthly: pd.DataFrame, limit: int = 10) -> list:
    out = []
    for _, r in df.head(limit).iterrows():
        monthly = _product_monthly_summary(r["Product ID"], merged_monthly)
        out.append({
            "product_id":        r["Product ID"],
            "product_title":     str(r.get("Product Title", "Unknown"))[:60],
            "total_spend":       round(float(r["Spend"]),   2),
            "total_revenue":     round(float(r["Revenue"]), 2),
            "roi":               round(float(r["ROI"]),     2),
            "months_active":     len([m for m in monthly if m["spend"] > 0 or m["revenue"] > 0]),
            "monthly_breakdown": monthly,
        })
    return out


def prepare_full_ai_data(
    q1: pd.DataFrame,
    q2: pd.DataFrame,
    q3: pd.DataFrame,
    q4: pd.DataFrame,
    merged_monthly: pd.DataFrame,
    all_df: pd.DataFrame,
) -> dict:
    total_rev = float(all_df["Revenue"].sum())
    total_sp  = float(all_df["Spend"].sum())
    total_months = merged_monthly["Month"].nunique()

    def quad_summary(df, label):
        if df.empty:
            return {"quadrant": label, "products": 0,
                    "total_spend": 0, "total_revenue": 0, "roi": 0, "top_products": []}
        sp = float(df["Spend"].sum())
        rv = float(df["Revenue"].sum())
        return {
            "quadrant":      label,
            "products":      len(df),
            "total_spend":   round(sp, 2),
            "total_revenue": round(rv, 2),
            "roi":           round(rv / sp, 2) if sp else 0,
            "revenue_share": round(rv / total_rev * 100, 1) if total_rev else 0,
            "spend_share":   round(sp / total_sp  * 100, 1) if total_sp  else 0,
            "top_products":  _to_product_list(df, merged_monthly, 15),
        }

    p75_q1  = q1["Revenue"].quantile(0.75) if not q1.empty else 0
    q1_top  = q1[q1["Revenue"] >= p75_q1].sort_values("Revenue", ascending=False)

    p75_q2  = q2["Revenue"].quantile(0.75) if not q2.empty else 0
    q2_top  = q2[q2["Revenue"] >= p75_q2].sort_values("Revenue", ascending=False)

    p25_q3  = q3["ROI"].quantile(0.25) if not q3.empty else 0
    q3_bot  = q3[q3["ROI"] <= p25_q3].sort_values("Spend", ascending=False)

    p25_q4  = q4["Revenue"].quantile(0.25) if not q4.empty else 0
    q4_bot  = q4[q4["Revenue"] <= p25_q4].sort_values("Revenue")

    all_monthly_agg = (
        merged_monthly.groupby("Month")[["Spend", "Revenue"]].sum().reset_index()
    )
    all_monthly_agg["roi"] = (
        all_monthly_agg["Revenue"]
        / all_monthly_agg["Spend"].replace(0, float("nan"))
    ).fillna(0).round(2)
    monthly_trend = all_monthly_agg.to_dict(orient="records")

    return {
        "summary": {
            "total_products":  len(all_df),
            "total_spend":     round(total_sp,  2),
            "total_revenue":   round(total_rev, 2),
            "overall_roi":     round(total_rev / total_sp, 2) if total_sp else 0,
            "total_months":    total_months,
            "monthly_trend":   monthly_trend,
        },
        "quadrant_overview": {
            "high_potential":  quad_summary(q1, "High Potential (High Revenue, Low Spend)"),
            "high_conversion": quad_summary(q2, "High Conversion (High Revenue, High Spend)"),
            "low_performing":  quad_summary(q3, "Low Performing (Low Revenue, High Spend)"),
            "zombie":          quad_summary(q4, "Zombie (Low Revenue, Low Spend)"),
        },
        "high_potential_top25": {
            "cutoff_revenue": round(p75_q1, 2),
            "count":          len(q1_top),
            "total_revenue":  round(float(q1_top["Revenue"].sum()), 2) if not q1_top.empty else 0,
            "total_spend":    round(float(q1_top["Spend"].sum()),   2) if not q1_top.empty else 0,
            "products":       _to_product_list(q1_top, merged_monthly, 10),
        },
        "high_conversion_top25": {
            "cutoff_revenue": round(p75_q2, 2),
            "count":          len(q2_top),
            "total_revenue":  round(float(q2_top["Revenue"].sum()), 2) if not q2_top.empty else 0,
            "total_spend":    round(float(q2_top["Spend"].sum()),   2) if not q2_top.empty else 0,
            "products":       _to_product_list(q2_top, merged_monthly, 10),
        },
        "low_performing_worst25": {
            "cutoff_roi":    round(p25_q3, 4),
            "count":         len(q3_bot),
            "total_spend":   round(float(q3_bot["Spend"].sum()),   2) if not q3_bot.empty else 0,
            "total_revenue": round(float(q3_bot["Revenue"].sum()), 2) if not q3_bot.empty else 0,
            "revenue_lost":  round(float((q3_bot["Spend"] - q3_bot["Revenue"]).sum()), 2) if not q3_bot.empty else 0,
            "products":      _to_product_list(q3_bot, merged_monthly, 10),
        },
        "zombie_bottom25": {
            "cutoff_revenue": round(p25_q4, 2),
            "count":          len(q4_bot),
            "zero_revenue":   int((q4_bot["Revenue"] == 0).sum()) if not q4_bot.empty else 0,
            "total_spend":    round(float(q4_bot["Spend"].sum()), 2) if not q4_bot.empty else 0,
            "products":       _to_product_list(q4_bot, merged_monthly, 10),
        },
    }


# ──────────────────────────────────────────────────────────────────────
#  MASTER PROMPT
# ──────────────────────────────────────────────────────────────────────

MASTER_PROMPT = """
You are a senior e-commerce performance analyst. You are given complete product-level advertising data across 4 quadrants.

YOUR TASK: Generate exactly 4 structured insights — one per quadrant. Each insight must be deeply data-backed, precise, and immediately actionable. Write as a bullet-point analyst report.

STRICT RULES:
1. Use ONLY the numbers provided in the JSON. Never invent or estimate figures.
2. Always cite exact product titles, exact ₹ values, exact ROI, exact month names from monthly_breakdown.
3. ROAS = Revenue ÷ Spend — calculate and show it wherever relevant.
4. Budget Waste = Spend − Revenue for low-performing products. Show it.
5. Revenue Contribution % = (product revenue ÷ total_revenue) × 100. Show it.
6. Keep each insight focused, clear, and concise. Bullet points only inside insights.

---

INSIGHT 1 — HIGH POTENTIAL PRODUCTS (Top 25% by Revenue, Low Spend):
These are the best-return products. Analyse high_potential_top25 products.
For each product in the list provide:
  • Product title, Total Spend, Total Revenue, ROI, Revenue contribution % of overall total
  • Monthly breakdown: list each month with spend / revenue / ROI
  • Trend: is revenue growing, stable, or declining month-over-month?
  • ROAS calculation
After all products, give:
  • Combined revenue of these top 25% products as % of total portfolio revenue
  • Top 3 products by ROI with exact numbers
  • Action: Specific budget increase recommendation with ₹ numbers per product

INSIGHT 2 — HIGH CONVERSION PRODUCTS (Top 25% by Revenue, High Spend):
These are heavy spenders with strong returns. Analyse high_conversion_top25 products.
For each product in the list provide:
  • Product title, Total Spend, Total Revenue, ROI
  • Monthly spend trend (increasing/stable/decreasing) with ₹ values per month
  • Monthly revenue trend with ₹ values per month
  • Efficiency: Revenue per ₹1 spent (ROAS)
After all products, give:
  • Which products show both spend and revenue increasing? List them.
  • Which products have declining revenue despite high spend? Flag them for review.
  • Action: Budget allocation changes with exact ₹ figures

INSIGHT 3 — LOW PERFORMING PRODUCTS (Bottom 25% by ROI, High Spend = Wasted Budget):
These are the biggest budget drains. Analyse low_performing_worst25 products.
For each product in the list provide:
  • Product title, Total Spend, Total Revenue, ROI, Budget Waste (₹ Spend − ₹ Revenue)
  • Monthly breakdown: each month's spend/revenue/ROI
  • How many months has this product been underperforming?
After all products, give:
  • Total budget waste across all these products (₹)
  • Products with ROI < 0.5x — list with exact waste amounts
  • Action: Which to pause immediately (with ₹ recovery) and which to test at reduced spend

INSIGHT 4 — OVERALL PORTFOLIO ANALYSIS:
Using the summary and quadrant_overview data:
  • Total spend vs total revenue vs overall ROI
  • Revenue distribution across 4 quadrants with % breakdown
  • Spend efficiency: which quadrant gives best ROI vs worst ROI
  • Month-over-month portfolio trend from monthly_trend data
  • Top 3 strategic recommendations for next campaign cycle with ₹ budget reallocation numbers

---

Return ONLY this JSON. No markdown, no explanation, no extra keys:
{
  "insights": [
    {
      "insight_number": 1,
      "title": "High Potential Products — Top 25% Analysis",
      "type": "High Potential",
      "product_details": [
        {
          "product_title": "exact title",
          "total_spend": 0,
          "total_revenue": 0,
          "roi": 0,
          "roas": 0,
          "revenue_contribution_pct": 0,
          "monthly_breakdown": [{"month":"","spend":0,"revenue":0,"roi":0}],
          "trend": "increasing|stable|decreasing|volatile",
          "key_stat": "one-line summary"
        }
      ],
      "combined_metrics": {
        "combined_revenue": 0,
        "combined_spend": 0,
        "combined_roi": 0,
        "revenue_pct_of_portfolio": 0
      },
      "top_performers": ["exact product title with ROI: X.Xx"],
      "action": "specific ₹ recommendation"
    },
    {
      "insight_number": 2,
      "title": "High Conversion Products — Top 25% Analysis",
      "type": "High Conversion",
      "product_details": [
        {
          "product_title": "exact title",
          "total_spend": 0,
          "total_revenue": 0,
          "roi": 0,
          "roas": 0,
          "spend_trend": "increasing|stable|decreasing",
          "revenue_trend": "increasing|stable|decreasing",
          "monthly_breakdown": [{"month":"","spend":0,"revenue":0,"roi":0}],
          "key_stat": "one-line summary"
        }
      ],
      "combined_metrics": {
        "combined_revenue": 0,
        "combined_spend": 0,
        "combined_roi": 0,
        "revenue_pct_of_portfolio": 0
      },
      "scaling_candidates": ["products where both spend and revenue are increasing"],
      "review_flags": ["products with declining revenue"],
      "action": "specific ₹ recommendation"
    },
    {
      "insight_number": 3,
      "title": "Low Performing Products — Budget Waste Analysis",
      "type": "Low Performing",
      "product_details": [
        {
          "product_title": "exact title",
          "total_spend": 0,
          "total_revenue": 0,
          "roi": 0,
          "budget_waste": 0,
          "months_underperforming": 0,
          "monthly_breakdown": [{"month":"","spend":0,"revenue":0,"roi":0}],
          "key_stat": "one-line summary"
        }
      ],
      "combined_metrics": {
        "total_wasted_spend": 0,
        "total_revenue_from_waste": 0,
        "avg_roi": 0
      },
      "immediate_pause": ["products to pause with ₹ recovery amount"],
      "reduce_test": ["products to test at 50% spend"],
      "action": "specific ₹ recovery recommendation"
    },
    {
      "insight_number": 4,
      "title": "Overall Portfolio Analysis",
      "type": "Portfolio",
      "portfolio_metrics": {
        "total_spend": 0,
        "total_revenue": 0,
        "overall_roi": 0
      },
      "quadrant_breakdown": [
        {"quadrant": "", "revenue": 0, "spend": 0, "roi": 0, "revenue_pct": 0, "spend_pct": 0}
      ],
      "monthly_trend_summary": "describe the overall trend across months",
      "best_quadrant_roi": "quadrant name with ROI",
      "worst_quadrant_roi": "quadrant name with ROI",
      "strategic_recommendations": [
        "recommendation 1 with ₹ numbers",
        "recommendation 2 with ₹ numbers",
        "recommendation 3 with ₹ numbers"
      ]
    }
  ]
}
"""


# ──────────────────────────────────────────────────────────────────────
#  GEMINI API CALL
# ──────────────────────────────────────────────────────────────────────

def generate_overall_ai_insights(
    ai_data: dict,
) -> Tuple[Optional[List[dict]], Optional[str]]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
    except Exception:
        return None, "⚠️ Gemini API key not configured. Add `GEMINI_API_KEY` to your Streamlit secrets."

    full_prompt = f"{MASTER_PROMPT}\n\nDATA:\n{json.dumps(ai_data, indent=2)}"
    try:
        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.05, "max_output_tokens": 250000},
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        return parsed.get("insights", []), None
    except json.JSONDecodeError as e:
        return None, f"AI response could not be parsed: {e}"
    except Exception as e:
        return None, f"Gemini API error: {e}"


# ──────────────────────────────────────────────────────────────────────
#  AI INSIGHT RENDERER
# ──────────────────────────────────────────────────────────────────────

INSIGHT_CONFIG = {
    "High Potential": {
        "color": "#059669", "bg": "#ECFDF5", "border": "#A7F3D0",
        "icon": "🚀", "tag_bg": "#D1FAE5", "tag_color": "#065F46",
    },
    "High Conversion": {
        "color": "#2563EB", "bg": "#EFF6FF", "border": "#BFDBFE",
        "icon": "💎", "tag_bg": "#DBEAFE", "tag_color": "#1E40AF",
    },
    "Low Performing": {
        "color": "#DC2626", "bg": "#FEF2F2", "border": "#FECACA",
        "icon": "⚠️", "tag_bg": "#FEE2E2", "tag_color": "#991B1B",
    },
    "Portfolio": {
        "color": "#7C3AED", "bg": "#F5F3FF", "border": "#DDD6FE",
        "icon": "📊", "tag_bg": "#EDE9FE", "tag_color": "#4C1D95",
    },
}


def _kpi_row(items):
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


def _product_detail_card(prod: dict, insight_type: str) -> str:
    cfg     = INSIGHT_CONFIG.get(insight_type, INSIGHT_CONFIG["Portfolio"])
    is_waste = insight_type == "Low Performing"

    monthly = prod.get("monthly_breakdown", [])
    monthly_html = ""
    if monthly:
        rows_html = ""
        for m in monthly:
            roi_color = "#DC2626" if m.get("roi", 0) < 1 else "#059669"
            rows_html += f"""
            <tr style="border-bottom:1px solid #F1F5F9">
              <td style="padding:5px 10px;color:#475569;font-size:12px">{m.get("month","")}</td>
              <td style="padding:5px 10px;color:#1E293B;font-size:12px;text-align:right">₹{m.get("spend",0):,.0f}</td>
              <td style="padding:5px 10px;color:#1E293B;font-size:12px;text-align:right">₹{m.get("revenue",0):,.0f}</td>
              <td style="padding:5px 10px;font-size:12px;text-align:right;color:{roi_color};font-weight:600">{m.get("roi",0):.2f}x</td>
            </tr>"""
        monthly_html = f"""
        <div style="margin-top:10px">
          <div style="font-size:11px;font-weight:600;color:#94A3B8;text-transform:uppercase;
                      letter-spacing:.08em;margin-bottom:6px">Monthly Breakdown</div>
          <table style="width:100%;border-collapse:collapse;background:#F8FAFC;border-radius:8px;overflow:hidden">
            <thead>
              <tr style="background:#F1F5F9">
                <th style="padding:6px 10px;font-size:11px;color:#64748B;text-align:left;font-weight:600">Month</th>
                <th style="padding:6px 10px;font-size:11px;color:#64748B;text-align:right;font-weight:600">Spend</th>
                <th style="padding:6px 10px;font-size:11px;color:#64748B;text-align:right;font-weight:600">Revenue</th>
                <th style="padding:6px 10px;font-size:11px;color:#64748B;text-align:right;font-weight:600">ROI</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>"""

    pills = [
        ("Spend",   f"₹{prod.get('total_spend',0):,.0f}"),
        ("Revenue", f"₹{prod.get('total_revenue',0):,.0f}"),
        ("ROI",     f"{prod.get('roi',0):.2f}x"),
    ]
    if prod.get("roas"):
        pills.append(("ROAS", f"{prod.get('roas',0):.2f}x"))
    if prod.get("revenue_contribution_pct"):
        pills.append(("Rev Contribution", f"{prod.get('revenue_contribution_pct',0):.1f}%"))
    if is_waste and prod.get("budget_waste"):
        pills.append(("Budget Waste", f"₹{prod.get('budget_waste',0):,.0f}"))
    if prod.get("months_underperforming"):
        pills.append(("Months Underperforming", str(prod.get("months_underperforming", 0))))
    if prod.get("trend"):
        trend_colors = {
            "increasing": "#059669", "stable": "#2563EB",
            "decreasing": "#DC2626", "volatile": "#D97706",
        }
        tc = trend_colors.get(prod.get("trend", "stable"), "#64748B")
        pills.append((f"<span style='color:{tc}'>Trend</span>",
                       f"<span style='color:{tc}'>{prod.get('trend','').title()}</span>"))
    if prod.get("spend_trend"):
        pills.append(("Spend Trend", prod.get("spend_trend", "").title()))
    if prod.get("revenue_trend"):
        tr_c = ("#059669" if prod.get("revenue_trend") == "increasing"
                else "#DC2626" if prod.get("revenue_trend") == "decreasing"
                else "#2563EB")
        pills.append((f"<span style='color:{tr_c}'>Rev Trend</span>",
                       f"<span style='color:{tr_c}'>{prod.get('revenue_trend','').title()}</span>"))

    pills_html = "".join(
        f"""<span style="display:inline-flex;align-items:center;gap:4px;
            background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;
            padding:3px 10px;font-size:11px;margin:2px;color:#475569">
            {lbl}: <strong style="color:#1E293B">{val}</strong></span>"""
        for lbl, val in pills
    )

    key_stat = prod.get("key_stat", "")
    return f"""
    <div style="background:#FFFFFF;border:1px solid {cfg['border']};border-radius:10px;
                padding:14px 16px;margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <div style="background:{cfg['bg']};border-radius:6px;padding:4px 10px;
                    font-size:12px;font-weight:700;color:{cfg['color']}">
          {prod.get('product_title','Unknown')}
        </div>
      </div>
      <div style="margin-bottom:6px;flex-wrap:wrap">{pills_html}</div>
      {f'<div style="font-size:11px;color:#64748B;font-style:italic;margin-top:6px">💡 {key_stat}</div>' if key_stat else ''}
      {monthly_html}
    </div>"""


def render_ai_insights(insights_list: List[dict]):
    if not insights_list:
        st.warning("No insights returned. Please try again.")
        return

    for ins in insights_list:
        num   = ins.get("insight_number", 1)
        title = ins.get("title", f"Insight {num}")
        itype = ins.get("type", "Portfolio")
        cfg   = INSIGHT_CONFIG.get(itype, INSIGHT_CONFIG["Portfolio"])

        with st.expander(f"{cfg['icon']}  Insight {num} — {title}", expanded=False):
            if itype == "High Potential" and ins.get("combined_metrics"):
                cm = ins["combined_metrics"]
                _kpi_row([
                    ("Combined Revenue", compact_currency(cm.get("combined_revenue", 0)), cfg["color"], cfg["bg"]),
                    ("Combined Spend",   compact_currency(cm.get("combined_spend",   0)), "#64748B", "#F8FAFC"),
                    ("Combined ROI",     f"{cm.get('combined_roi',0):.2f}x",              cfg["color"], cfg["bg"]),
                    ("% of Portfolio",   f"{cm.get('revenue_pct_of_portfolio',0):.1f}%",  cfg["color"], cfg["bg"]),
                ])
            elif itype == "High Conversion" and ins.get("combined_metrics"):
                cm = ins["combined_metrics"]
                _kpi_row([
                    ("Combined Revenue", compact_currency(cm.get("combined_revenue", 0)), cfg["color"], cfg["bg"]),
                    ("Combined Spend",   compact_currency(cm.get("combined_spend",   0)), "#2563EB", "#EFF6FF"),
                    ("Combined ROI",     f"{cm.get('combined_roi',0):.2f}x",              cfg["color"], cfg["bg"]),
                    ("% of Portfolio",   f"{cm.get('revenue_pct_of_portfolio',0):.1f}%",  cfg["color"], cfg["bg"]),
                ])
            elif itype == "Low Performing" and ins.get("combined_metrics"):
                cm = ins["combined_metrics"]
                _kpi_row([
                    ("Total Wasted Spend", compact_currency(cm.get("total_wasted_spend",       0)), "#DC2626", "#FEF2F2"),
                    ("Revenue from Waste", compact_currency(cm.get("total_revenue_from_waste", 0)), "#64748B", "#F8FAFC"),
                    ("Average ROI",        f"{cm.get('avg_roi',0):.2f}x",                          "#DC2626", "#FEF2F2"),
                ])
            elif itype == "Portfolio" and ins.get("portfolio_metrics"):
                pm = ins["portfolio_metrics"]
                _kpi_row([
                    ("Total Spend",   compact_currency(pm.get("total_spend",   0)), "#64748B", "#F8FAFC"),
                    ("Total Revenue", compact_currency(pm.get("total_revenue", 0)), "#059669", "#ECFDF5"),
                    ("Overall ROI",   f"{pm.get('overall_roi',0):.2f}x",            "#7C3AED", "#F5F3FF"),
                ])

            st.markdown("")

            products = ins.get("product_details", [])
            if products:
                st.markdown(
                    f"""<div style="font-size:13px;font-weight:700;color:#1E293B;
                        margin:12px 0 8px;">📦 Product Details ({len(products)} products)</div>""",
                    unsafe_allow_html=True,
                )
            import streamlit.components.v1 as components
            for prod in products:
                components.html(_product_detail_card(prod, itype), height=450, scrolling=True)

            qb = ins.get("quadrant_breakdown", [])
            if qb:
                st.markdown(
                    """<div style="font-size:13px;font-weight:700;color:#1E293B;
                        margin:12px 0 8px">📊 Quadrant Breakdown</div>""",
                    unsafe_allow_html=True,
                )
                quad_colors = {
                    "High Potential": "#059669", "High Conversion": "#2563EB",
                    "Low Performing": "#DC2626", "Zombie": "#64748B",
                }
                for q in qb:
                    qc = quad_colors.get(q.get("quadrant", ""), "#64748B")
                    pills_q = "".join([
                        f"""<span style="display:inline-flex;align-items:center;gap:4px;
                            background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;
                            padding:3px 10px;font-size:11px;margin:2px;color:#475569">
                            {k}: <strong style="color:#1E293B">{v}</strong></span>"""
                        for k, v in [
                            ("Revenue", f"₹{q.get('revenue',0):,.0f}"),
                            ("Spend",   f"₹{q.get('spend',0):,.0f}"),
                            ("ROI",     f"{q.get('roi',0):.2f}x"),
                            ("Rev %",   f"{q.get('revenue_pct',0):.1f}%"),
                            ("Spend %", f"{q.get('spend_pct',0):.1f}%"),
                        ]
                    ])
                    st.markdown(f"""
                    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;
                                padding:10px 14px;margin-bottom:8px;border-left:4px solid {qc}">
                      <div style="font-size:13px;font-weight:700;color:{qc};margin-bottom:6px">
                        {q.get('quadrant','')}
                      </div>
                      <div>{pills_q}</div>
                    </div>""", unsafe_allow_html=True)

            def _bullet_list(items, color, heading, icon="•"):
                if not items:
                    return
                st.markdown(f"""
                <div style="background:#F8FAFC;border-radius:10px;padding:12px 16px;
                            margin-top:10px;border:1px solid #E2E8F0">
                  <div style="font-size:12px;font-weight:700;color:{color};text-transform:uppercase;
                              letter-spacing:.07em;margin-bottom:8px">{heading}</div>
                  {''.join([f"<div style='font-size:12px;color:#1E293B;padding:3px 0;border-bottom:1px solid #F1F5F9'>{icon} {item}</div>" for item in items])}
                </div>""", unsafe_allow_html=True)

            if itype == "High Potential":
                _bullet_list(ins.get("top_performers", []),     "#059669", "🏆 Top Performers by ROI", "★")
            if itype == "High Conversion":
                _bullet_list(ins.get("scaling_candidates", []), "#2563EB", "📈 Scaling Candidates (Both Increasing)", "↑")
                _bullet_list(ins.get("review_flags",       []), "#DC2626", "🚩 Review Flags (Declining Revenue)",     "!")
            if itype == "Low Performing":
                _bullet_list(ins.get("immediate_pause",    []), "#DC2626", "🛑 Pause Immediately", "✗")
                _bullet_list(ins.get("reduce_test",        []), "#D97706", "🧪 Reduce & Test at 50%", "⤵")
            if itype == "Portfolio":
                monthly_summary = ins.get("monthly_trend_summary", "")
                if monthly_summary:
                    st.markdown(f"""
                    <div style="background:#F8FAFC;border-radius:10px;padding:12px 16px;
                                margin-top:10px;border:1px solid #E2E8F0">
                      <div style="font-size:12px;font-weight:700;color:#7C3AED;text-transform:uppercase;
                                  letter-spacing:.07em;margin-bottom:6px">📅 Monthly Trend</div>
                      <div style="font-size:12px;color:#475569">{monthly_summary}</div>
                    </div>""", unsafe_allow_html=True)

                best  = ins.get("best_quadrant_roi",  "")
                worst = ins.get("worst_quadrant_roi", "")
                if best or worst:
                    cols_bw = st.columns(2)
                    if best:
                        cols_bw[0].markdown(f"""<div style="background:#ECFDF5;border:1px solid #A7F3D0;
                            border-radius:10px;padding:10px 14px;font-size:12px;color:#065F46">
                            <strong>🏆 Best ROI Quadrant:</strong><br>{best}</div>""",
                            unsafe_allow_html=True)
                    if worst:
                        cols_bw[1].markdown(f"""<div style="background:#FEF2F2;border:1px solid #FECACA;
                            border-radius:10px;padding:10px 14px;font-size:12px;color:#991B1B">
                            <strong>⚠️ Worst ROI Quadrant:</strong><br>{worst}</div>""",
                            unsafe_allow_html=True)

                recs = ins.get("strategic_recommendations", [])
                if recs:
                    st.markdown("""<div style="font-size:12px;font-weight:700;color:#7C3AED;
                        text-transform:uppercase;letter-spacing:.07em;margin-top:14px;
                        margin-bottom:8px">⚡ Strategic Recommendations</div>""",
                        unsafe_allow_html=True)
                    for i, rec in enumerate(recs, 1):
                        st.markdown(f"""
                        <div style="background:#F5F3FF;border:1px solid #DDD6FE;border-radius:8px;
                                    padding:10px 14px;margin-bottom:6px;font-size:12px;color:#1E293B">
                          <strong style="color:#7C3AED">{i}.</strong> {rec}
                        </div>""", unsafe_allow_html=True)

            action = ins.get("action", "")
            if action:
                st.markdown(f"""
                <div style="background:{cfg['bg']};border:2px solid {cfg['border']};
                            border-radius:10px;padding:12px 16px;margin-top:12px">
                  <div style="font-size:11px;font-weight:700;color:{cfg['color']};
                              text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px">⚡ Action</div>
                  <div style="font-size:13px;color:#1E293B;font-weight:600">{action}</div>
                </div>""", unsafe_allow_html=True)