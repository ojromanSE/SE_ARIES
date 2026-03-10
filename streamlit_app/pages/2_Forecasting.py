"""
Forecasting — Decline Curve Analysis.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.db import init_db, get_db, ACProperty, ACProduct, ACScenario, ACEconomic
from services.decline_curve import run_dca, fit_decline
from components.auth import require_auth
from components.charts import decline_curve_chart
from datetime import date
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Forecasting — SE_ARIES", layout="wide", page_icon="📉")
init_db()
require_auth()

st.title("📉 Decline Curve Analysis")
st.caption("Interactive production forecasting using decline curve methods")

db = get_db()
try:
    # ── Property & scenario selectors ────────────────────────────────────
    col_sel, col_main = st.columns([1, 3])

    with col_sel:
        st.subheader("Select Well")
        props = db.query(ACProperty).filter(ACProperty.is_active == True).order_by(ACProperty.propname).all()
        if not props:
            st.warning("No properties found. Add some in Project Manager.")
            st.stop()

        prop_options = {f"{p.propnum} — {p.propname or 'Unnamed'}": p for p in props}
        chosen_label = st.selectbox("Property", list(prop_options.keys()))
        prop = prop_options[chosen_label]

        # Load production history
        history = db.query(ACProduct).filter(
            ACProduct.propnum == prop.propnum
        ).order_by(ACProduct.prod_date).all()

        hist_df = pd.DataFrame([{
            "prod_date": h.prod_date,
            "oil_rate_bopd": h.oil_rate_bopd,
            "gas_rate_mcfd": h.gas_rate_mcfd,
            "gross_oil_bbl": h.gross_oil_bbl,
            "gross_gas_mcf": h.gross_gas_mcf,
            "gross_water_bbl": h.gross_water_bbl,
        } for h in history]) if history else pd.DataFrame()

        st.divider()
        st.subheader("DCA Parameters")
        st.caption("Adjust decline curve below or auto-fit from history")

        decline_type = st.selectbox("Decline Type", ["EXP", "HYP", "HAR", "MHYP"],
            format_func=lambda x: {"EXP":"Exponential","HYP":"Hyperbolic","HAR":"Harmonic","MHYP":"Mod. Hyperbolic"}[x])

        # Auto-fit button
        if not hist_df.empty and st.button("🔁 Auto-Fit from History", use_container_width=True):
            months = np.arange(len(hist_df))
            rates = hist_df["oil_rate_bopd"].values
            qi_fit, di_fit = fit_decline(months, rates)
            st.session_state["dca_qi"] = float(qi_fit)
            st.session_state["dca_di"] = float(di_fit)
            st.toast(f"Fitted: Qi={qi_fit:.0f} BOPD, Di={di_fit:.3f}/yr", icon="✅")

        default_qi = float(hist_df["oil_rate_bopd"].iloc[-1]) if not hist_df.empty else 100.0
        qi = st.number_input("Qi — Initial Oil Rate (BOPD)", 0.0, 100000.0,
                             st.session_state.get("dca_qi", default_qi), step=10.0)
        di = st.number_input("Di — Nominal Decline (/yr)", 0.0, 5.0,
                             st.session_state.get("dca_di", 0.40), step=0.01, format="%.3f")

        b = 0.0
        dt = None
        if decline_type in ["HYP", "MHYP"]:
            b = st.slider("b — Hyperbolic Factor", 0.0, 2.0, 1.2, 0.05)
        if decline_type == "MHYP":
            dt = st.number_input("Dt — Terminal Decline (/yr)", 0.0, 2.0, 0.08, step=0.01, format="%.3f")

        # Gas parameters
        st.markdown("**Gas**")
        gc1, gc2 = st.columns(2)
        gas_qi = gc1.number_input("Gas Qi (MCFD)", 0.0, 1e7, float(hist_df["gas_rate_mcfd"].iloc[-1]) if not hist_df.empty else 0.0, step=10.0)
        gas_di = gc2.number_input("Gas Di (/yr)", 0.0, 5.0, di, step=0.01, format="%.3f")

        max_life = st.slider("Max Life (years)", 1, 50, 30)
        econ_limit = st.number_input("Economic Limit Rate (BOPD)", 0.0, 100.0, 1.0, step=0.5)

    # ── Run DCA ──────────────────────────────────────────────────────────
    with col_main:
        oil_dca = run_dca(decline_type, qi, di, b, dt, max_months=max_life * 12, min_rate=econ_limit)
        gas_dca = run_dca(decline_type, gas_qi, gas_di, b, dt, max_months=max_life * 12) if gas_qi > 0 else None

        start_date = date.today().replace(day=1) if hist_df.empty else hist_df["prod_date"].iloc[-1]
        from dateutil.relativedelta import relativedelta
        forecast_rows = []
        for m in range(oil_dca.producing_months):
            d = start_date + relativedelta(months=m + 1)
            forecast_rows.append({
                "date": d,
                "oil_rate_bopd": oil_dca.rates_daily[m],
                "gas_rate_mcfd": gas_dca.rates_daily[m] if gas_dca and m < len(gas_dca.rates_daily) else 0.0,
                "cum_oil_mstb": oil_dca.cum_volumes[m] / 1000.0,
                "cum_gas_mmcf": gas_dca.cum_volumes[m] / 1_000_000.0 if gas_dca and m < len(gas_dca.cum_volumes) else 0.0,
            })
        fcst_df = pd.DataFrame(forecast_rows)

        # ── KPIs ──────────────────────────────────────────────────────
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Producing Life", f"{oil_dca.producing_months} mo")
        k2.metric("Oil EUR (MSTB)", f"{oil_dca.eur/1000:.1f}")
        gas_eur = gas_dca.eur / 1_000_000 if gas_dca else 0
        k3.metric("Gas EUR (MMCF)", f"{gas_eur:.1f}")
        k4.metric("Initial Rate (BOPD)", f"{qi:.0f}")
        k5.metric("Final Rate (BOPD)", f"{oil_dca.rates_daily[-1]:.1f}" if len(oil_dca.rates_daily) else "—")

        # ── Decline Curve Chart ────────────────────────────────────────
        st.subheader("Production Forecast")
        fig = decline_curve_chart(fcst_df, hist_df if not hist_df.empty else None)
        st.plotly_chart(fig, use_container_width=True)

        # ── Log scale view ─────────────────────────────────────────────
        with st.expander("📊 Semi-Log View (Rate vs Cumulative)"):
            if not fcst_df.empty:
                log_fig = go.Figure()
                log_fig.add_trace(go.Scatter(
                    x=fcst_df["cum_oil_mstb"], y=fcst_df["oil_rate_bopd"],
                    mode="lines", name="Rate vs Cum Oil",
                    line=dict(color="#10b981", width=2),
                ))
                log_fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9ca3af"),
                    xaxis=dict(title="Cumulative Oil (MSTB)", gridcolor="#1f2937"),
                    yaxis=dict(title="Oil Rate (BOPD)", type="log", gridcolor="#1f2937"),
                    height=300,
                    margin=dict(l=50, r=20, t=20, b=40),
                )
                st.plotly_chart(log_fig, use_container_width=True)

        # ── History table ──────────────────────────────────────────────
        with st.expander("🗂️ Production History"):
            if not hist_df.empty:
                display_hist = hist_df.copy()
                display_hist["prod_date"] = display_hist["prod_date"].astype(str)
                st.dataframe(display_hist.sort_values("prod_date", ascending=False), use_container_width=True, hide_index=True, height=300)
            else:
                st.info("No production history. Upload data in the Data Manager.")

        # ── Forecast table ─────────────────────────────────────────────
        with st.expander("📋 Forecast Table"):
            if not fcst_df.empty:
                disp_fcst = fcst_df.copy()
                disp_fcst["date"] = disp_fcst["date"].astype(str)
                disp_fcst["oil_rate_bopd"] = disp_fcst["oil_rate_bopd"].round(1)
                disp_fcst["gas_rate_mcfd"] = disp_fcst["gas_rate_mcfd"].round(1)
                disp_fcst["cum_oil_mstb"] = disp_fcst["cum_oil_mstb"].round(3)
                st.dataframe(disp_fcst, use_container_width=True, hide_index=True, height=300)

                # Download
                csv = disp_fcst.to_csv(index=False)
                st.download_button("⬇️ Download Forecast CSV", csv, f"{prop.propnum}_forecast.csv", "text/csv")

finally:
    db.close()
