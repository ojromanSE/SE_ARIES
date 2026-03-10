"""Plotly chart builders for SE_ARIES Streamlit app."""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

COLORS = {
    "oil": "#10b981",
    "gas": "#3b82f6",
    "ngl": "#f59e0b",
    "water": "#6b7280",
    "revenue": "#22c55e",
    "opex": "#ef4444",
    "capex": "#f97316",
    "ncf": "#8b5cf6",
    "cum_ncf": "#60a5fa",
    "cum_oil": "#34d399",
    "forecast": "#10b981",
    "history": "#fbbf24",
    "grid": "#1f2937",
    "bg": "rgba(0,0,0,0)",
    "paper": "rgba(0,0,0,0)",
    "font": "#9ca3af",
    "zero_line": "#374151",
}

LAYOUT_BASE = dict(
    plot_bgcolor=COLORS["bg"],
    paper_bgcolor=COLORS["paper"],
    font=dict(color=COLORS["font"], size=11),
    xaxis=dict(gridcolor=COLORS["grid"], zeroline=False, showline=False),
    yaxis=dict(gridcolor=COLORS["grid"], zeroline=False, showline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    margin=dict(l=50, r=20, t=30, b=40),
)


def decline_curve_chart(forecast_df: pd.DataFrame, history_df: pd.DataFrame | None = None) -> go.Figure:
    """Decline curve chart: oil/gas rate vs time, with history overlay."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # History — oil
    if history_df is not None and not history_df.empty:
        fig.add_trace(go.Scatter(
            x=history_df["prod_date"], y=history_df["oil_rate_bopd"],
            name="Hist. Oil (BOPD)", mode="markers+lines",
            line=dict(color=COLORS["history"], width=1.5, dash="dot"),
            marker=dict(size=4),
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=history_df["prod_date"], y=history_df["gas_rate_mcfd"],
            name="Hist. Gas (MCFD)", mode="markers",
            marker=dict(color=COLORS["gas"], size=3, opacity=0.6),
        ), secondary_y=True)

    # Forecast — oil
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df["date"], y=forecast_df["oil_rate_bopd"],
            name="Fcst. Oil (BOPD)", mode="lines",
            line=dict(color=COLORS["oil"], width=2.5),
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=forecast_df["date"], y=forecast_df["gas_rate_mcfd"],
            name="Fcst. Gas (MCFD)", mode="lines",
            line=dict(color=COLORS["gas"], width=1.5, dash="dash"),
        ), secondary_y=True)
        # Cumulative oil on secondary axis
        fig.add_trace(go.Scatter(
            x=forecast_df["date"], y=forecast_df["cum_oil_mstb"],
            name="Cum. Oil (MSTB)", mode="lines",
            line=dict(color=COLORS["cum_oil"], width=1, dash="dot"),
        ), secondary_y=True)

    fig.update_layout(
        **LAYOUT_BASE,
        height=380,
        title_text=None,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Rate (BOPD)", secondary_y=False, gridcolor=COLORS["grid"])
    fig.update_yaxes(title_text="Gas (MCFD) / Cum. Oil (MSTB)", secondary_y=True, gridcolor=COLORS["grid"])
    return fig


def cash_flow_chart(df: pd.DataFrame) -> go.Figure:
    """Monthly revenue, OPEX, and cumulative NCF chart."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df["date"], y=df["total_revenue"] / 1000,
        name="Revenue ($k)", marker_color=COLORS["revenue"], opacity=0.75,
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df["date"], y=-df["opex"] / 1000,
        name="OPEX ($k)", marker_color=COLORS["opex"], opacity=0.75,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["cum_cash_flow"] / 1_000_000,
        name="Cum. NCF ($MM)", mode="lines",
        line=dict(color=COLORS["cum_ncf"], width=2.5),
    ), secondary_y=True)
    fig.add_hline(y=0, line_color=COLORS["zero_line"], line_width=1, secondary_y=False)

    fig.update_layout(
        **LAYOUT_BASE,
        barmode="relative",
        height=360,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Monthly ($k)", secondary_y=False, gridcolor=COLORS["grid"])
    fig.update_yaxes(title_text="Cum. NCF ($MM)", secondary_y=True, gridcolor=COLORS["grid"])
    return fig


def production_bar_chart(history_df: pd.DataFrame) -> go.Figure:
    """Stacked monthly production bar chart (oil, gas, water)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=history_df["prod_date"], y=history_df["gross_oil_bbl"] / 1000,
                         name="Oil (MSTB)", marker_color=COLORS["oil"]))
    fig.add_trace(go.Bar(x=history_df["prod_date"], y=history_df["gross_gas_mcf"] / 1000,
                         name="Gas (MMCF)", marker_color=COLORS["gas"]))
    fig.add_trace(go.Bar(x=history_df["prod_date"], y=history_df["gross_water_bbl"] / 1000,
                         name="Water (MSTB)", marker_color=COLORS["water"], opacity=0.5))
    fig.update_layout(**LAYOUT_BASE, barmode="group", height=320, hovermode="x unified")
    fig.update_yaxes(title_text="Volume (MSTB / MMCF)")
    return fig


def sensitivity_tornado(base_npv: float, sensitivities: dict[str, tuple[float, float]]) -> go.Figure:
    """Tornado chart for sensitivity analysis."""
    items = sorted(sensitivities.items(), key=lambda x: abs(x[1][1] - x[1][0]))
    labels = [i[0] for i in items]
    lows = [i[1][0] for i in items]
    highs = [i[1][1] for i in items]

    fig = go.Figure()
    for i, (label, (low, high)) in enumerate(zip(labels, zip(lows, highs))):
        fig.add_trace(go.Bar(
            x=[high - base_npv], y=[label], orientation="h",
            marker_color=COLORS["revenue"], showlegend=i == 0,
            name="Upside", base=[base_npv / 1e6],
        ))
        fig.add_trace(go.Bar(
            x=[low - base_npv], y=[label], orientation="h",
            marker_color=COLORS["opex"], showlegend=i == 0,
            name="Downside", base=[base_npv / 1e6],
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        barmode="overlay",
        height=max(250, len(labels) * 40 + 60),
        xaxis_title="NPV10 ($MM)",
    )
    fig.add_vline(x=base_npv / 1e6, line_color=COLORS["font"], line_dash="dash", line_width=1)
    return fig


def waterfall_chart(df: pd.DataFrame) -> go.Figure:
    """Annual cash flow waterfall."""
    annual = df.groupby("date").apply(lambda g: g.iloc[0]).reset_index(drop=True)
    annual = df.copy()
    annual["year"] = annual["date"].dt.year
    by_year = annual.groupby("year").agg(
        revenue=("total_revenue", "sum"),
        opex=("opex", "sum"),
        taxes=("prod_taxes", "sum"),
        ncf=("net_cash_flow", "sum"),
    ).reset_index()

    fig = go.Figure(go.Waterfall(
        x=by_year["year"].astype(str),
        y=by_year["ncf"] / 1e6,
        measure=["relative"] * len(by_year),
        connector=dict(line=dict(color=COLORS["grid"])),
        increasing=dict(marker_color=COLORS["revenue"]),
        decreasing=dict(marker_color=COLORS["opex"]),
        text=[f"${v:.1f}MM" for v in by_year["ncf"] / 1e6],
        textposition="outside",
    ))
    fig.update_layout(**LAYOUT_BASE, height=320, yaxis_title="Annual NCF ($MM)")
    return fig
