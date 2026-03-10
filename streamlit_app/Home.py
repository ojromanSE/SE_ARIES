"""
SE_ARIES — Internal Petroleum Economics Platform
Streamlit multi-page app entry point (Home / Dashboard).
"""
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="SE_ARIES — Petroleum Economics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init DB & auth ────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from services.db import init_db, get_db, ACProperty, ACProject, ACScenario, ACEconomic, ACProduct
from components.auth import require_auth, logout

init_db()
require_auth()

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:0.5rem 0 0.25rem'>
        <span style='font-size:1.4rem; font-weight:800; color:#0ea5e9'>⚡ SE_ARIES</span><br>
        <span style='font-size:0.72rem; color:#6b7280'>Petroleum Economics Platform</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.caption(f"👤 {st.session_state.get('full_name', 'User')} · {st.session_state.get('user_role', '').capitalize()}")
    if st.button("Logout", use_container_width=True):
        logout()

# ── Dashboard ─────────────────────────────────────────────────────────────
st.title("⚡ SE_ARIES Dashboard")
st.caption(f"Petroleum Economics & Reserves Platform · {datetime.now().strftime('%B %d, %Y')}")

db = get_db()
try:
    n_props = db.query(ACProperty).filter(ACProperty.is_active == True).count()
    n_projects = db.query(ACProject).filter(ACProject.is_active == True).count()
    n_scenarios = db.query(ACScenario).filter(ACScenario.is_active == True).count()
    n_ran = db.query(ACEconomic).filter(ACEconomic.run_status == "SUCCESS").count()
    n_prod = db.query(ACProduct).count()

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Properties", f"{n_props:,}")
    c2.metric("Projects", f"{n_projects:,}")
    c3.metric("Scenarios", f"{n_scenarios:,}")
    c4.metric("Econ Runs", f"{n_ran:,}")
    c5.metric("Prod. Records", f"{n_prod:,}")

    st.divider()

    # ── Portfolio summary ──────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Portfolio Overview")
        props = db.query(ACProperty).filter(ACProperty.is_active == True).order_by(ACProperty.propname).limit(200).all()
        if props:
            df = pd.DataFrame([{
                "PROPNUM": p.propnum,
                "Name": p.propname or "—",
                "State": p.state or "—",
                "Basin": p.basin or "—",
                "Field": p.field or "—",
                "Type": p.well_type or "—",
                "Status": p.status or "—",
                "WI%": f"{p.working_interest * 100:.1f}%",
                "NRI%": f"{p.net_revenue_interest * 100:.1f}%",
            } for p in props])
            st.dataframe(df, use_container_width=True, height=380, hide_index=True)
        else:
            st.info("No properties yet. Add some in the **Project Manager** page.")

    with col2:
        st.subheader("Economics Summary")
        econs = db.query(ACEconomic).filter(ACEconomic.run_status == "SUCCESS").all()
        if econs:
            total_npv10 = sum(e.npv10 or 0 for e in econs)
            total_oil = sum(e.cum_oil_mstb or 0 for e in econs)
            total_gas = sum(e.cum_gas_mmcf or 0 for e in econs)
            positive = sum(1 for e in econs if (e.npv10 or 0) > 0)

            st.metric("Portfolio NPV10", f"${total_npv10/1e6:,.1f} MM")
            st.metric("Total Proved Oil (MSTB)", f"{total_oil:,.0f}")
            st.metric("Total Proved Gas (MMCF)", f"{total_gas:,.0f}")
            st.metric("Economic Wells", f"{positive} / {len(econs)}")

            st.markdown("---")
            # Basin breakdown
            by_basin: dict[str, list] = {}
            for p in props:
                b = p.basin or "Unknown"
                by_basin.setdefault(b, []).append(p)

            if by_basin:
                st.caption("**By Basin**")
                basin_df = pd.DataFrame([
                    {"Basin": b, "Wells": len(ws)} for b, ws in by_basin.items()
                ]).sort_values("Wells", ascending=False)
                st.dataframe(basin_df, use_container_width=True, hide_index=True, height=200)
        else:
            st.info("Run economics on properties to see the portfolio summary.")

    # ── Quick navigation ───────────────────────────────────────────────────
    st.divider()
    st.subheader("Quick Navigation")
    n1, n2, n3, n4, n5 = st.columns(5)
    with n1:
        st.page_link("pages/1_Project_Manager.py", label="📁 Project Manager", use_container_width=True)
    with n2:
        st.page_link("pages/2_Forecasting.py", label="📉 Forecasting", use_container_width=True)
    with n3:
        st.page_link("pages/3_Economics.py", label="💰 Economics", use_container_width=True)
    with n4:
        st.page_link("pages/4_Data_Manager.py", label="🗄️ Data Manager", use_container_width=True)
    with n5:
        st.page_link("pages/5_Reserves.py", label="📚 Reserves (RMS)", use_container_width=True)

finally:
    db.close()
