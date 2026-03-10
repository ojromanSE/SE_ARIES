"""
Economics — Full economic simulator (NPV, IRR, cash flow).
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.db import init_db, get_db, ACProperty, ACScenario, ACEconomic, ACProductForecast
from services.economics import EconInputs, run_economics
from components.auth import require_auth
from components.charts import decline_curve_chart, cash_flow_chart, waterfall_chart, sensitivity_tornado
from datetime import datetime, date
from sqlalchemy import delete

st.set_page_config(page_title="Economics — SE_ARIES", layout="wide", page_icon="💰")
init_db()
require_auth()

st.title("💰 Economic Simulator")
st.caption("Keyword-driven economic model — NPV, IRR, cash flow, reserves (mirrors ARIES AC_ECONOMIC)")

db = get_db()
try:
    # ── Selectors ────────────────────────────────────────────────────────
    sel_col, main_col = st.columns([1, 3])

    with sel_col:
        st.subheader("Property & Scenario")

        props = db.query(ACProperty).filter(ACProperty.is_active == True).order_by(ACProperty.propname).all()
        if not props:
            st.warning("Add properties in Project Manager first.")
            st.stop()

        prop_opts = {f"{p.propnum} — {p.propname or 'Unnamed'}": p for p in props}
        chosen_prop_label = st.selectbox("Property", list(prop_opts.keys()), key="econ_prop")
        prop = prop_opts[chosen_prop_label]

        # Load scenarios
        scenarios = db.query(ACScenario).filter(ACScenario.is_active == True).order_by(ACScenario.scenario_name).all()
        if not scenarios:
            st.warning("Create a scenario in Project Manager first.")
            st.stop()

        scen_opts = {s.scenario_name: s for s in scenarios}
        chosen_scen_label = st.selectbox("Scenario", list(scen_opts.keys()), key="econ_scen")
        scenario = scen_opts[chosen_scen_label]

        # Load existing econ inputs for this prop/scenario
        existing_econ = db.query(ACEconomic).filter(
            ACEconomic.propnum == prop.propnum,
            ACEconomic.scenario_id == scenario.id,
        ).first()

        e = existing_econ  # shorthand

        st.divider()
        st.subheader("Decline Curve")

        # Oil DCA
        st.markdown("**🛢️ Oil**")
        oil_type = st.selectbox("Type", ["EXP", "HYP", "HAR", "MHYP"],
            index=["EXP","HYP","HAR","MHYP"].index(e.oil_decline_type) if e and e.oil_decline_type in ["EXP","HYP","HAR","MHYP"] else 0,
            key="oil_type")
        oil_qi = st.number_input("Qi (BOPD)", 0.0, 1e6, float(e.oil_initial_rate or 0) if e else 0.0, step=10.0, key="oil_qi")
        oil_di = st.number_input("Di (/yr)", 0.0, 5.0, float(e.oil_decline_rate or 0.3) if e else 0.3, step=0.01, format="%.3f", key="oil_di")
        oil_b = 0.0
        oil_dt = None
        if oil_type in ["HYP", "MHYP"]:
            oil_b = st.slider("b factor", 0.0, 2.0, float(e.oil_b_factor or 1.2) if e else 1.2, 0.05, key="oil_b")
        if oil_type == "MHYP":
            oil_dt = st.number_input("Terminal Di (/yr)", 0.0, 2.0, float(e.oil_terminal_decline or 0.08) if e else 0.08, step=0.01, format="%.3f", key="oil_dt")

        # Gas DCA
        st.markdown("**⛽ Gas**")
        gc1, gc2 = st.columns(2)
        gas_qi = gc1.number_input("Gas Qi (MCFD)", 0.0, 1e8, float(e.gas_initial_rate or 0) if e else 0.0, step=10.0, key="gas_qi")
        gas_di = gc2.number_input("Gas Di (/yr)", 0.0, 5.0, float(e.gas_decline_rate or oil_di) if e else 0.3, step=0.01, format="%.3f", key="gas_di")
        gas_b = float(e.gas_b_factor or 0) if e else 0.0

        # Gas handling (SHRINK / BTU keywords)
        st.markdown("**Gas Handling**")
        hc1, hc2, hc3 = st.columns(3)
        shrinkage = hc1.number_input("Shrinkage", 0.0, 1.0, float(e.shrinkage or 1.0) if e else 1.0, step=0.01, format="%.3f", key="shrink", help="SHRINK keyword")
        btu = hc2.number_input("BTU Factor", 0.5, 2.0, float(e.btu_factor or 1.0) if e else 1.0, step=0.01, format="%.3f", key="btu", help="BTU keyword")
        ngl_yield = hc3.number_input("NGL Yield (BBL/MMCF)", 0.0, 1000.0, float(e.ngl_yield or 0) if e else 0.0, step=1.0, key="ngl_yld")

        st.divider()
        st.subheader("Costs (OPEX/CAPEX)")
        fx1, fx2 = st.columns(2)
        fixed_opex = fx1.number_input("Fixed OPEX ($/mo)", 0.0, 1e7, float(e.fixed_opex or 0) if e else 0.0, step=100.0, key="fix_opex")
        var_oil = fx2.number_input("Var. Oil ($/BBL)", 0.0, 100.0, float(e.variable_oil_opex or 0) if e else 0.0, step=0.50, key="var_oil")
        var_gas = fx1.number_input("Var. Gas ($/MCF)", 0.0, 5.0, float(e.variable_gas_opex or 0) if e else 0.0, step=0.01, key="var_gas")
        overhead = fx2.number_input("Overhead ($/mo)", 0.0, 1e6, float(e.overhead or 0) if e else 0.0, step=100.0, key="ovhd")

        cx1, cx2 = st.columns(2)
        capex = cx1.number_input("CAPEX ($)", 0.0, 1e9, float(e.capex or 0) if e else 0.0, step=10000.0, format="%.0f", key="capex_in")
        abandon = cx2.number_input("P&A Cost ($)", 0.0, 1e7, float(e.abandonment_cost or 0) if e else 0.0, step=1000.0, format="%.0f", key="abandon")

        st.divider()
        st.subheader("Economic Limit (LOSS)")
        el1, el2 = st.columns(2)
        econ_limit_type = el1.selectbox("Limit Type", ["NET_REVENUE", "OIL_RATE", "GAS_RATE"],
            key="econ_lim_type", help="LOSS keyword")
        econ_limit_val = el2.number_input("Limit Value", 0.0, 1e6, float(e.economic_limit_value or 0) if e else 0.0, key="econ_lim_val")
        max_life_yr = st.slider("Max Life (LIFE keyword, years)", 1, 50, 30, key="max_life")

        run_btn = st.button("▶️ Run Economics", type="primary", use_container_width=True)

    # ── Run simulation ────────────────────────────────────────────────────
    with main_col:
        if run_btn:
            # Build inputs
            econ_start = scenario.econ_start_date.date() if scenario.econ_start_date else date.today().replace(day=1)

            inp = EconInputs(
                propnum=prop.propnum,
                econ_start_date=econ_start,
                oil_price=scenario.oil_price or 70.0,
                gas_price=scenario.gas_price or 3.0,
                ngl_price_pct=float(e.ngl_price_pct or 0.4) if e else 0.4,
                discount_rate=scenario.discount_rate / 100,
                tax_rate=scenario.tax_rate,
                ad_valorem_rate=scenario.ad_valorem_rate,
                chance_of_success=scenario.chance_of_success,
                apply_economic_limit=scenario.apply_economic_limit,
                oil_price_escalation=scenario.oil_price_escalation,
                gas_price_escalation=scenario.gas_price_escalation,
                working_interest=prop.working_interest,
                net_revenue_interest=prop.net_revenue_interest,
                oil_decline_type=oil_type,
                oil_qi=oil_qi,
                oil_di=oil_di,
                oil_b=oil_b,
                oil_dt=oil_dt,
                gas_decline_type="EXP",
                gas_qi=gas_qi,
                gas_di=gas_di,
                gas_b=gas_b,
                shrinkage=shrinkage,
                btu_factor=btu,
                ngl_yield=ngl_yield,
                oil_price_diff=float(e.oil_price_diff or 0) if e else 0.0,
                gas_price_diff=float(e.gas_price_diff or 0) if e else 0.0,
                fixed_opex=fixed_opex,
                variable_oil_opex=var_oil,
                variable_gas_opex=var_gas,
                overhead=overhead,
                initial_capex=capex,
                abandonment_cost=abandon,
                econ_limit_type=econ_limit_type,
                econ_limit_value=econ_limit_val,
                max_life_months=max_life_yr * 12,
            )

            with st.spinner("Running economic simulation..."):
                result = run_economics(inp)

            # Save inputs & results to DB
            if not existing_econ:
                db_econ = ACEconomic(propnum=prop.propnum, scenario_id=scenario.id)
                db.add(db_econ)
            else:
                db_econ = existing_econ

            db_econ.oil_decline_type = oil_type
            db_econ.oil_initial_rate = oil_qi
            db_econ.oil_decline_rate = oil_di
            db_econ.oil_b_factor = oil_b
            db_econ.oil_terminal_decline = oil_dt
            db_econ.gas_initial_rate = gas_qi
            db_econ.gas_decline_rate = gas_di
            db_econ.shrinkage = shrinkage
            db_econ.btu_factor = btu
            db_econ.ngl_yield = ngl_yield
            db_econ.fixed_opex = fixed_opex
            db_econ.variable_oil_opex = var_oil
            db_econ.variable_gas_opex = var_gas
            db_econ.overhead = overhead
            db_econ.capex = capex
            db_econ.abandonment_cost = abandon
            db_econ.economic_limit_type = econ_limit_type
            db_econ.economic_limit_value = econ_limit_val
            db_econ.max_life_months = max_life_yr * 12
            db_econ.npv10 = result.npv10
            db_econ.npv15 = result.npv15
            db_econ.irr = result.irr
            db_econ.payout_months = result.payout_months
            db_econ.total_capex = result.total_capex
            db_econ.total_opex = result.total_opex
            db_econ.total_revenue = result.total_revenue
            db_econ.cum_oil_mstb = result.cum_oil_mstb
            db_econ.cum_gas_mmcf = result.cum_gas_mmcf
            db_econ.cum_ngl_mstb = result.cum_ngl_mstb
            db_econ.last_run_at = datetime.utcnow()
            db_econ.run_status = "SUCCESS"

            # Persist monthly forecast
            db.execute(delete(ACProductForecast).where(
                (ACProductForecast.propnum == prop.propnum) &
                (ACProductForecast.scenario_id == scenario.id)
            ))
            for _, row in result.monthly_df.iterrows():
                db.add(ACProductForecast(
                    propnum=prop.propnum,
                    scenario_id=scenario.id,
                    forecast_date=row["date"],
                    forecast_year=row["date"].year,
                    forecast_month=row["date"].month,
                    gross_oil_bbl=row["gross_oil_bbl"],
                    gross_gas_mcf=row["gross_gas_mcf"],
                    oil_revenue=row["oil_revenue"],
                    gas_revenue=row["gas_revenue"],
                    ngl_revenue=row["ngl_revenue"],
                    total_revenue=row["total_revenue"],
                    opex=row["opex"],
                    taxes=row["prod_taxes"],
                    net_cash_flow=row["net_cash_flow"],
                    cum_cash_flow=row["cum_cash_flow"],
                    discounted_ncf=row["discounted_ncf_10"],
                    oil_rate_bopd=row["oil_rate_bopd"],
                    gas_rate_mcfd=row["gas_rate_mcfd"],
                    cum_oil_mstb=row["cum_oil_mstb"],
                    cum_gas_mmcf=row["cum_gas_mmcf"],
                ))
            db.commit()

            st.session_state["econ_result"] = result
            st.session_state["econ_prop_label"] = chosen_prop_label

        # ── Show results ───────────────────────────────────────────────
        result = st.session_state.get("econ_result")
        if result is None and existing_econ and existing_econ.run_status == "SUCCESS":
            # Show last-run results from DB
            st.info(f"Showing last run — {existing_econ.last_run_at.strftime('%Y-%m-%d %H:%M') if existing_econ.last_run_at else 'unknown'}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("NPV10", f"${(existing_econ.npv10 or 0)/1e6:.2f} MM",
                      delta="positive" if (existing_econ.npv10 or 0) > 0 else "negative")
            m2.metric("IRR", f"{existing_econ.irr:.1f}%" if existing_econ.irr else "N/A")
            m3.metric("Payout", f"{existing_econ.payout_months:.0f} mo" if existing_econ.payout_months else "N/A")
            m4.metric("Cum. Oil (MSTB)", f"{existing_econ.cum_oil_mstb:.1f}" if existing_econ.cum_oil_mstb else "—")
            st.caption("Click ▶️ Run Economics to regenerate.")

        elif result:
            df = result.monthly_df
            df["date"] = pd.to_datetime(df["date"])

            # ── KPI Cards ──────────────────────────────────────────────
            k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
            npv_color = "normal" if result.npv10 >= 0 else "inverse"
            k1.metric("NPV10 ($MM)", f"${result.npv10/1e6:.2f}", delta=f"${result.npv10/1e6:.2f} MM" if result.npv10 >= 0 else None)
            k2.metric("NPV15 ($MM)", f"${result.npv15/1e6:.2f}")
            k3.metric("IRR", f"{result.irr:.1f}%" if result.irr else "N/A")
            k4.metric("Payout", f"{result.payout_months:.0f} mo" if result.payout_months else "N/A")
            k5.metric("Oil EUR (MSTB)", f"{result.cum_oil_mstb:.1f}")
            k6.metric("Gas EUR (MMCF)", f"{result.cum_gas_mmcf:.1f}")
            k7.metric("Revenue ($MM)", f"${result.total_revenue/1e6:.1f}")
            k8.metric("OPEX ($MM)", f"${result.total_opex/1e6:.1f}")

            st.divider()

            # ── Charts ──────────────────────────────────────────────────
            chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs([
                "📉 Decline Curve", "💵 Cash Flow", "📊 Annual Waterfall", "🌪️ Sensitivity"
            ])

            with chart_tab1:
                fcst_for_chart = df.rename(columns={"date": "date"})[["date","oil_rate_bopd","gas_rate_mcfd","cum_oil_mstb","cum_gas_mmcf"]]
                st.plotly_chart(decline_curve_chart(fcst_for_chart), use_container_width=True)

            with chart_tab2:
                st.plotly_chart(cash_flow_chart(df), use_container_width=True)

            with chart_tab3:
                st.plotly_chart(waterfall_chart(df), use_container_width=True)

            with chart_tab4:
                st.subheader("Sensitivity Analysis — NPV10")
                base_npv = result.npv10
                # Run quick sensitivities by varying oil price ±20%, OPEX ±25%
                from services.economics import EconInputs as EI, run_economics as run_e
                base_inp_dict = dict(
                    propnum=prop.propnum, econ_start_date=econ_start,
                    oil_price=scenario.oil_price or 70.0, gas_price=scenario.gas_price or 3.0,
                    discount_rate=scenario.discount_rate / 100, tax_rate=scenario.tax_rate,
                    ad_valorem_rate=scenario.ad_valorem_rate, working_interest=prop.working_interest,
                    net_revenue_interest=prop.net_revenue_interest,
                    oil_decline_type=oil_type, oil_qi=oil_qi, oil_di=oil_di, oil_b=oil_b, oil_dt=oil_dt,
                    gas_qi=gas_qi, gas_di=gas_di, shrinkage=shrinkage, btu_factor=btu, ngl_yield=ngl_yield,
                    fixed_opex=fixed_opex, variable_oil_opex=var_oil, initial_capex=capex,
                    abandonment_cost=abandon, econ_limit_type=econ_limit_type,
                    econ_limit_value=econ_limit_val, max_life_months=max_life_yr * 12,
                )

                def npv_for(**overrides):
                    inp2 = EI(**{**base_inp_dict, **overrides})
                    return run_e(inp2).npv10

                with st.spinner("Computing sensitivities..."):
                    sensitivities = {
                        "Oil Price ±20%": (npv_for(oil_price=(scenario.oil_price or 70)*0.8), npv_for(oil_price=(scenario.oil_price or 70)*1.2)),
                        "Gas Price ±20%": (npv_for(gas_price=(scenario.gas_price or 3)*0.8), npv_for(gas_price=(scenario.gas_price or 3)*1.2)),
                        "OPEX ±25%": (npv_for(fixed_opex=fixed_opex*1.25, variable_oil_opex=var_oil*1.25), npv_for(fixed_opex=fixed_opex*0.75, variable_oil_opex=var_oil*0.75)),
                        "Qi ±20%": (npv_for(oil_qi=oil_qi*0.8), npv_for(oil_qi=oil_qi*1.2)),
                        "Discount ±3%": (npv_for(discount_rate=max(0.01, scenario.discount_rate/100-0.03)), npv_for(discount_rate=scenario.discount_rate/100+0.03)),
                    }
                st.plotly_chart(sensitivity_tornado(base_npv, sensitivities), use_container_width=True)

            # ── Monthly table ─────────────────────────────────────────
            with st.expander("📋 Monthly Cash Flow Detail"):
                disp = df[["date","oil_rate_bopd","gas_rate_mcfd","total_revenue","opex","prod_taxes","net_cash_flow","cum_cash_flow","discounted_ncf_10","cum_oil_mstb","cum_gas_mmcf"]].copy()
                disp.columns = ["Date","Oil BOPD","Gas MCFD","Revenue","OPEX","Taxes","NCF","Cum NCF","Disc NCF","Cum Oil MSTB","Cum Gas MMCF"]
                disp["Date"] = disp["Date"].dt.strftime("%Y-%m")
                for col in ["Revenue","OPEX","Taxes","NCF","Cum NCF","Disc NCF"]:
                    disp[col] = disp[col].apply(lambda x: f"${x:,.0f}")
                st.dataframe(disp, use_container_width=True, hide_index=True, height=400)

                # Export
                export = result.monthly_df.copy()
                export["date"] = export["date"].astype(str)
                st.download_button(
                    "⬇️ Export to Excel",
                    data=_df_to_excel(export),
                    file_name=f"{prop.propnum}_{scenario.scenario_name}_cashflow.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        else:
            st.info("Configure inputs on the left and click **▶️ Run Economics** to generate the forecast.")

finally:
    db.close()


def _df_to_excel(df: pd.DataFrame) -> bytes:
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cash Flow")
    return buf.getvalue()
