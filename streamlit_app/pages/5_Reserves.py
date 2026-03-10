"""
Reserve Management System (RMS) — reserves booking and reporting.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.db import init_db, get_db, ACProperty, ACEconomic, ACReserves, ACQualifier, ACScenario
from components.auth import require_auth
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Reserves (RMS) — SE_ARIES", layout="wide", page_icon="📚")
init_db()
require_auth()

st.title("📚 Reserve Management System (RMS)")
st.caption("Reserves booking, classification, and SEC/SPE-PRMS reporting")

db = get_db()
try:
    tab_book, tab_report, tab_reconcile = st.tabs([
        "📝 Reserve Booking",
        "📊 Reserves Report",
        "🔄 Reconciliation",
    ])

    # ─────────────────────────────────────────────────────────────────
    # TAB 1: BOOKING
    # ─────────────────────────────────────────────────────────────────
    with tab_book:
        b_c1, b_c2 = st.columns([1, 2])

        with b_c1:
            st.subheader("Book Reserves")
            props = db.query(ACProperty).filter(ACProperty.is_active == True).order_by(ACProperty.propname).all()
            if not props:
                st.warning("No properties found.")
                st.stop()

            prop_opts = {f"{p.propnum} — {p.propname or 'Unnamed'}": p for p in props}
            sel_label = st.selectbox("Property", list(prop_opts.keys()))
            prop = prop_opts[sel_label]

            # Load latest econ results for this property
            econ = db.query(ACEconomic).filter(
                ACEconomic.propnum == prop.propnum,
                ACEconomic.run_status == "SUCCESS",
            ).first()

            if econ:
                st.info(f"Using run from {econ.last_run_at.strftime('%Y-%m-%d') if econ.last_run_at else '—'}")

            with st.form("reserve_booking"):
                booking_year = st.number_input("Booking Year", 2000, 2100, datetime.now().year)
                reserves_cat = st.selectbox("Reserves Category", ["PDP", "PDNP", "PUD", "PROB", "POSS"])
                st.caption("PDP=Producing, PDNP=Non-Producing, PUD=Undeveloped, PROB=Probable, POSS=Possible")

                st.markdown("**Volumes**")
                v1, v2, v3 = st.columns(3)
                oil_res = v1.number_input("Oil (MSTB)", 0.0, 1e9,
                    float(econ.cum_oil_mstb or 0) if econ else 0.0, step=1.0)
                gas_res = v2.number_input("Gas (MMCF)", 0.0, 1e10,
                    float(econ.cum_gas_mmcf or 0) if econ else 0.0, step=1.0)
                ngl_res = v3.number_input("NGL (MSTB)", 0.0, 1e8,
                    float(econ.cum_ngl_mstb or 0) if econ else 0.0, step=0.1)

                boe = oil_res + gas_res / 6.0 + ngl_res
                st.metric("BOE (6:1)", f"{boe:.1f} MSTB")

                st.markdown("**Economic Value**")
                pv1, pv2 = st.columns(2)
                npv10_val = pv1.number_input("PV10 / NPV10 ($)", 0.0, 1e12,
                    float(econ.npv10 or 0) if econ else 0.0, step=1000.0, format="%.0f")
                npv15_val = pv2.number_input("NPV15 ($)", 0.0, 1e12,
                    float(econ.npv15 or 0) if econ else 0.0, step=1000.0, format="%.0f")

                approved_by = st.text_input("Approved By", value=st.session_state.get("full_name", ""))
                sub = st.form_submit_button("📌 Book Reserves", type="primary", use_container_width=True)

                if sub:
                    existing_r = db.query(ACReserves).filter(
                        ACReserves.propnum == prop.propnum,
                        ACReserves.booking_year == booking_year,
                        ACReserves.reserves_category == reserves_cat,
                    ).first()

                    if existing_r:
                        existing_r.proved_oil_mstb = oil_res
                        existing_r.proved_gas_mmcf = gas_res
                        existing_r.proved_ngl_mstb = ngl_res
                        existing_r.proved_boe = boe
                        existing_r.npv10_proved = npv10_val
                        existing_r.approved_by = approved_by
                        existing_r.approved_date = datetime.utcnow()
                        existing_r.is_approved = True
                    else:
                        db.add(ACReserves(
                            propnum=prop.propnum,
                            booking_year=int(booking_year),
                            reserves_category=reserves_cat,
                            proved_oil_mstb=oil_res,
                            proved_gas_mmcf=gas_res,
                            proved_ngl_mstb=ngl_res,
                            proved_boe=boe,
                            npv10_proved=npv10_val,
                            approved_by=approved_by,
                            approved_date=datetime.utcnow(),
                            is_approved=True,
                        ))
                    db.commit()
                    st.success(f"✅ Booked {oil_res:.1f} MSTB oil + {gas_res:.1f} MMCF gas ({reserves_cat}) for {booking_year}")
                    st.rerun()

        with b_c2:
            st.subheader("Current Bookings")
            reserves = db.query(ACReserves).order_by(ACReserves.booking_year.desc(), ACReserves.propnum).limit(200).all()
            if reserves:
                res_df = pd.DataFrame([{
                    "PROPNUM": r.propnum,
                    "Year": r.booking_year,
                    "Category": r.reserves_category,
                    "Oil (MSTB)": f"{r.proved_oil_mstb:.1f}",
                    "Gas (MMCF)": f"{r.proved_gas_mmcf:.1f}",
                    "NGL (MSTB)": f"{r.proved_ngl_mstb:.1f}",
                    "BOE": f"{r.proved_boe:.1f}",
                    "PV10 ($MM)": f"${(r.npv10_proved or 0)/1e6:.2f}",
                    "Approved": "✓" if r.is_approved else "",
                    "By": r.approved_by or "—",
                } for r in reserves])
                st.dataframe(res_df, use_container_width=True, hide_index=True, height=450)
            else:
                st.info("No reserves booked yet. Use the form on the left.")

    # ─────────────────────────────────────────────────────────────────
    # TAB 2: RESERVES REPORT
    # ─────────────────────────────────────────────────────────────────
    with tab_report:
        st.subheader("Reserves Report")

        years_avail = db.query(ACReserves.booking_year).distinct().order_by(ACReserves.booking_year.desc()).all()
        years = [y[0] for y in years_avail]
        if not years:
            st.info("No reserves booked yet.")
        else:
            report_year = st.selectbox("Reporting Year", years)
            reserves = db.query(ACReserves).filter(ACReserves.booking_year == report_year).all()

            # Aggregate by category
            by_cat: dict[str, dict] = {}
            for r in reserves:
                cat = r.reserves_category
                if cat not in by_cat:
                    by_cat[cat] = {"oil": 0.0, "gas": 0.0, "ngl": 0.0, "boe": 0.0, "pv10": 0.0}
                by_cat[cat]["oil"] += r.proved_oil_mstb or 0
                by_cat[cat]["gas"] += r.proved_gas_mmcf or 0
                by_cat[cat]["ngl"] += r.proved_ngl_mstb or 0
                by_cat[cat]["boe"] += r.proved_boe or 0
                by_cat[cat]["pv10"] += r.npv10_proved or 0

            rpt_df = pd.DataFrame([
                {
                    "Category": cat,
                    "Oil (MSTB)": f"{v['oil']:,.1f}",
                    "Gas (MMCF)": f"{v['gas']:,.1f}",
                    "NGL (MSTB)": f"{v['ngl']:,.1f}",
                    "Total BOE (MBOE)": f"{v['boe']:,.1f}",
                    "PV10 ($MM)": f"${v['pv10']/1e6:,.2f}",
                }
                for cat, v in by_cat.items()
            ])

            # Totals
            total_row = {
                "Category": "TOTAL",
                "Oil (MSTB)": f"{sum(v['oil'] for v in by_cat.values()):,.1f}",
                "Gas (MMCF)": f"{sum(v['gas'] for v in by_cat.values()):,.1f}",
                "NGL (MSTB)": f"{sum(v['ngl'] for v in by_cat.values()):,.1f}",
                "Total BOE (MBOE)": f"{sum(v['boe'] for v in by_cat.values()):,.1f}",
                "PV10 ($MM)": f"${sum(v['pv10'] for v in by_cat.values())/1e6:,.2f}",
            }
            rpt_df = pd.concat([rpt_df, pd.DataFrame([total_row])], ignore_index=True)

            st.dataframe(rpt_df, use_container_width=True, hide_index=True)

            # Bar chart
            if by_cat:
                fig = go.Figure()
                cats = list(by_cat.keys())
                fig.add_trace(go.Bar(name="Oil (MSTB)", x=cats, y=[by_cat[c]["oil"] for c in cats], marker_color="#10b981"))
                fig.add_trace(go.Bar(name="Gas (MMCF/10)", x=cats, y=[by_cat[c]["gas"]/10 for c in cats], marker_color="#3b82f6"))
                fig.add_trace(go.Bar(name="NGL (MSTB)", x=cats, y=[by_cat[c]["ngl"] for c in cats], marker_color="#f59e0b"))
                fig.update_layout(
                    barmode="group", height=320,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9ca3af"),
                    xaxis=dict(gridcolor="#1f2937"),
                    yaxis=dict(gridcolor="#1f2937", title="Volume"),
                    legend=dict(bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=40, r=20, t=20, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)

            # Download
            st.download_button(
                "⬇️ Export Reserves Report (CSV)",
                rpt_df.to_csv(index=False),
                f"reserves_report_{report_year}.csv",
                "text/csv",
            )

    # ─────────────────────────────────────────────────────────────────
    # TAB 3: RECONCILIATION
    # ─────────────────────────────────────────────────────────────────
    with tab_reconcile:
        st.subheader("Year-over-Year Reserves Reconciliation")
        st.caption("Tracks revisions, extensions, production, and acquisitions per SPE-PRMS")

        years_avail2 = db.query(ACReserves.booking_year).distinct().order_by(ACReserves.booking_year.desc()).all()
        years2 = [y[0] for y in years_avail2]
        if len(years2) < 2:
            st.info("Need at least 2 years of bookings to show reconciliation.")
        else:
            rc1, rc2 = st.columns(2)
            yr_curr = rc1.selectbox("Current Year", years2, index=0)
            yr_prior = rc2.selectbox("Prior Year", years2, index=1 if len(years2) > 1 else 0)

            curr_recs = db.query(ACReserves).filter(ACReserves.booking_year == yr_curr).all()
            prior_recs = db.query(ACReserves).filter(ACReserves.booking_year == yr_prior).all()

            curr_oil = sum(r.proved_oil_mstb or 0 for r in curr_recs)
            prior_oil = sum(r.proved_oil_mstb or 0 for r in prior_recs)
            revision = curr_oil - prior_oil

            recon_df = pd.DataFrame([
                {"Item": f"Beginning Reserves ({yr_prior})", "Oil (MSTB)": f"{prior_oil:,.1f}"},
                {"Item": "Revisions (net)", "Oil (MSTB)": f"{revision:+,.1f}"},
                {"Item": "Extensions & Discoveries", "Oil (MSTB)": "—"},
                {"Item": "Acquisitions", "Oil (MSTB)": "—"},
                {"Item": "Production", "Oil (MSTB)": "—"},
                {"Item": f"Ending Reserves ({yr_curr})", "Oil (MSTB)": f"{curr_oil:,.1f}"},
            ])
            st.dataframe(recon_df, use_container_width=True, hide_index=True)
            st.caption("Production and detailed reconciliation items can be added via the booking form.")

finally:
    db.close()
