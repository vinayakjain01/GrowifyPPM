# ╔══════════════════════════════════════════════════════════════════════╗
# ║  charts.py  —  Plotly chart builders                               ║
# ╚══════════════════════════════════════════════════════════════════════╝

import plotly.graph_objects as go
from typing import List
import pandas as pd


CHART_LAYOUT = dict(
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(color="#1E293B", family="DM Sans"),
    legend=dict(
        font=dict(color="#475569", size=11),
        bgcolor="rgba(0,0,0,0)",
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="left",   x=0,
    ),
    margin=dict(t=80, b=40, l=10, r=10),
    height=440,
    xaxis=dict(showgrid=False, tickfont=dict(color="#475569", size=11)),
    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(color="#475569", size=11)),
)


def make_combo_chart(results_df: pd.DataFrame, months_ordered: List[str]) -> go.Figure:
    disc_sp, ndisc_sp = [], []
    disc_rv, ndisc_rv = [], []
    disc_roi, ndisc_roi = [], []

    for m in months_ordered:
        md = results_df[results_df["Month"] == m]
        d  = md[md["Category"] == "Discounted"]
        nd = md[md["Category"] == "Non-Discounted"]
        dr = d.iloc[0]  if not d.empty  else None
        nr = nd.iloc[0] if not nd.empty else None
        disc_sp.append(dr["Spend"]    if dr is not None else 0)
        ndisc_sp.append(nr["Spend"]   if nr is not None else 0)
        disc_rv.append(dr["Revenue"]  if dr is not None else 0)
        ndisc_rv.append(nr["Revenue"] if nr is not None else 0)
        disc_roi.append(dr["ROI"]     if dr is not None else 0)
        ndisc_roi.append(nr["ROI"]    if nr is not None else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Spend — Disc",     x=months_ordered, y=disc_sp,
                         marker_color="#3B82F6", offsetgroup=0,
                         text=[f"₹{v:,.0f}" for v in disc_sp],
                         textposition="outside", textfont=dict(size=9, color="#1E40AF")))
    fig.add_trace(go.Bar(name="Spend — Non-Disc", x=months_ordered, y=ndisc_sp,
                         marker_color="#93C5FD", offsetgroup=1,
                         text=[f"₹{v:,.0f}" for v in ndisc_sp],
                         textposition="outside", textfont=dict(size=9, color="#1E3A5F")))
    fig.add_trace(go.Bar(name="Rev — Disc",       x=months_ordered, y=disc_rv,
                         marker_color="#10B981", offsetgroup=2,
                         text=[f"₹{v:,.0f}" for v in disc_rv],
                         textposition="outside", textfont=dict(size=9, color="#065F46")))
    fig.add_trace(go.Bar(name="Rev — Non-Disc",   x=months_ordered, y=ndisc_rv,
                         marker_color="#6EE7B7", offsetgroup=3,
                         text=[f"₹{v:,.0f}" for v in ndisc_rv],
                         textposition="outside", textfont=dict(size=9, color="#064E3B")))
    fig.add_trace(go.Scatter(name="ROI — Disc",   x=months_ordered, y=disc_roi,
                             mode="lines+markers+text", yaxis="y2",
                             line=dict(color="#F59E0B", width=3),
                             marker=dict(size=9, color="#F59E0B"),
                             text=[f"{v:.2f}x" for v in disc_roi],
                             textposition="top center",
                             textfont=dict(color="#B45309", size=11)))
    fig.add_trace(go.Scatter(name="ROI — Non-Disc", x=months_ordered, y=ndisc_roi,
                             mode="lines+markers+text", yaxis="y2",
                             line=dict(color="#EF4444", width=3, dash="dot"),
                             marker=dict(size=9, symbol="diamond", color="#EF4444"),
                             text=[f"{v:.2f}x" for v in ndisc_roi],
                             textposition="top center",
                             textfont=dict(color="#991B1B", size=11)))

    layout = {
        **CHART_LAYOUT, "barmode": "group",
        "title": dict(text="Spend · Revenue · ROI by Month",
                      font=dict(size=15, color="#0F172A"), x=0),
        "yaxis":  dict(title="Amount (₹)", showgrid=True, gridcolor="#F1F5F9",
                       tickfont=dict(color="#475569")),
        "yaxis2": dict(title="ROI", overlaying="y", side="right",
                       tickfont=dict(color="#B45309"), ticksuffix="x", showgrid=False),
    }
    fig.update_layout(**layout)
    return fig


def make_share_chart(results_df: pd.DataFrame, months_ordered: List[str]) -> go.Figure:
    dsp, ndsp, drp, ndrp = [], [], [], []
    for m in months_ordered:
        md = results_df[results_df["Month"] == m]
        d  = md[md["Category"] == "Discounted"]
        nd = md[md["Category"] == "Non-Discounted"]
        dsp.append(d.iloc[0]["Spend_Pct"]    if not d.empty  else 0)
        ndsp.append(nd.iloc[0]["Spend_Pct"]  if not nd.empty else 0)
        drp.append(d.iloc[0]["Revenue_Pct"]  if not d.empty  else 0)
        ndrp.append(nd.iloc[0]["Revenue_Pct"] if not nd.empty else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Spend% — Disc",     x=months_ordered, y=dsp,
                         marker_color="#3B82F6",
                         text=[f"{v*100:.1f}%" for v in dsp],
                         textposition="inside", textfont=dict(size=11, color="white"),
                         offsetgroup=0))
    fig.add_trace(go.Bar(name="Spend% — Non-Disc", x=months_ordered, y=ndsp,
                         marker_color="#BFDBFE",
                         text=[f"{v*100:.1f}%" for v in ndsp],
                         textposition="inside", textfont=dict(size=11, color="#1E3A5F"),
                         base=dsp, offsetgroup=0))
    fig.add_trace(go.Bar(name="Rev% — Disc",     x=months_ordered, y=drp,
                         marker_color="#10B981",
                         text=[f"{v*100:.1f}%" for v in drp],
                         textposition="inside", textfont=dict(size=11, color="white"),
                         offsetgroup=1))
    fig.add_trace(go.Bar(name="Rev% — Non-Disc", x=months_ordered, y=ndrp,
                         marker_color="#A7F3D0",
                         text=[f"{v*100:.1f}%" for v in ndrp],
                         textposition="inside", textfont=dict(size=11, color="#065F46"),
                         base=drp, offsetgroup=1))

    layout = {
        **CHART_LAYOUT, "barmode": "stack",
        "title": dict(text="Spend Share vs Revenue Share (%)",
                      font=dict(size=15, color="#0F172A"), x=0),
        "yaxis": dict(title="Share", tickformat=".0%", showgrid=True,
                      gridcolor="#F1F5F9", tickfont=dict(color="#475569")),
    }
    fig.update_layout(**layout)
    return fig