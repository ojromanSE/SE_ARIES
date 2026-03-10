"""
Project Manager — manage properties, projects, and scenarios.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.db import (
    get_db, init_db, ACProperty, ACProject, ACScenario,
    project_property, Base
)
from datetime import datetime, date

st.set_page_config(page_title="Project Manager — SE_ARIES", layout="wide", page_icon="📁")
init_db()

st.title("📁 Project Manager")
st.caption("Manage properties, projects, and economic scenarios")

db = get_db()

try:
    tab_props, tab_projects, tab_scenarios = st.tabs(["🏭 Properties", "📂 Projects", "🎯 Scenarios"])

    # ─────────────────────────────────────────────────────────────────
    # TAB 1: PROPERTIES
    # ─────────────────────────────────────────────────────────────────
    with tab_props:
        col_list, col_form = st.columns([3, 2])

        with col_list:
            st.subheader("Property List (AC_PROPERTY)")

            # Filters
            fc1, fc2, fc3 = st.columns(3)
            search = fc1.text_input("Search", placeholder="PROPNUM, name, API, field...")
            wt_filter = fc2.selectbox("Well Type", ["All", "OIL", "GAS", "BOTH"])
            st_filter = fc3.text_input("State", placeholder="TX")

            props_q = db.query(ACProperty).filter(ACProperty.is_active == True)
            if search:
                props_q = props_q.filter(
                    (ACProperty.propnum.ilike(f"%{search}%")) |
                    (ACProperty.propname.ilike(f"%{search}%")) |
                    (ACProperty.api_num.ilike(f"%{search}%")) |
                    (ACProperty.field.ilike(f"%{search}%"))
                )
            if wt_filter != "All":
                props_q = props_q.filter(ACProperty.well_type == wt_filter)
            if st_filter:
                props_q = props_q.filter(ACProperty.state.ilike(f"%{st_filter}%"))

            props = props_q.order_by(ACProperty.propname).all()

            df = pd.DataFrame([{
                "PROPNUM": p.propnum,
                "Name": p.propname or "—",
                "API #": p.api_num or "—",
                "State": p.state or "—",
                "Basin": p.basin or "—",
                "Field": p.field or "—",
                "Type": p.well_type,
                "Status": p.status,
                "WI%": f"{p.working_interest*100:.1f}%",
                "NRI%": f"{p.net_revenue_interest*100:.1f}%",
            } for p in props])

            st.caption(f"{len(props)} properties")
            if not df.empty:
                selected = st.dataframe(
                    df, use_container_width=True, height=420, hide_index=True,
                    on_select="rerun", selection_mode="single-row",
                )
                sel_idx = selected.selection.rows
                if sel_idx:
                    st.session_state["pm_selected_propnum"] = props[sel_idx[0]].propnum
            else:
                st.info("No properties found.")

        with col_form:
            st.subheader("Add / Edit Property")

            # Load for editing if selected
            edit_prop = None
            sel_propnum = st.session_state.get("pm_selected_propnum")
            if sel_propnum:
                edit_prop = db.query(ACProperty).filter(ACProperty.propnum == sel_propnum).first()

            with st.form("prop_form"):
                propnum = st.text_input("PROPNUM *", value=edit_prop.propnum if edit_prop else "", max_chars=20, help="Unique property number")
                propname = st.text_input("Name", value=edit_prop.propname or "" if edit_prop else "")
                api_num = st.text_input("API #", value=edit_prop.api_num or "" if edit_prop else "", placeholder="42-XXX-XXXXX-0000")

                c1, c2 = st.columns(2)
                state = c1.text_input("State", value=edit_prop.state or "" if edit_prop else "", max_chars=10)
                county = c2.text_input("County", value=edit_prop.county or "" if edit_prop else "")
                basin = c1.text_input("Basin", value=edit_prop.basin or "" if edit_prop else "")
                field = c2.text_input("Field", value=edit_prop.field or "" if edit_prop else "")
                operator = st.text_input("Operator", value=edit_prop.operator or "" if edit_prop else "")

                c3, c4 = st.columns(2)
                well_type = c3.selectbox("Well Type", ["OIL", "GAS", "BOTH"],
                    index=["OIL", "GAS", "BOTH"].index(edit_prop.well_type) if edit_prop and edit_prop.well_type in ["OIL","GAS","BOTH"] else 0)
                entity_type = c4.selectbox("Entity Type", ["WELL", "GROUP", "AREA"],
                    index=["WELL","GROUP","AREA"].index(edit_prop.entity_type) if edit_prop and edit_prop.entity_type in ["WELL","GROUP","AREA"] else 0)
                status = c3.selectbox("Status", ["ACTIVE", "INACTIVE", "ABANDONED"],
                    index=["ACTIVE","INACTIVE","ABANDONED"].index(edit_prop.status) if edit_prop and edit_prop.status in ["ACTIVE","INACTIVE","ABANDONED"] else 0)

                c5, c6, c7 = st.columns(3)
                wi = c5.number_input("WI (fraction)", 0.0, 1.0, float(edit_prop.working_interest) if edit_prop else 1.0, step=0.001, format="%.4f")
                nri = c6.number_input("NRI (fraction)", 0.0, 1.0, float(edit_prop.net_revenue_interest) if edit_prop else 1.0, step=0.001, format="%.4f")
                royalty = c7.number_input("Royalty", 0.0, 1.0, float(edit_prop.royalty_interest) if edit_prop else 0.0, step=0.001, format="%.4f")

                first_prod = st.date_input("First Production Date",
                    value=edit_prop.first_prod_date.date() if edit_prop and edit_prop.first_prod_date else None)
                notes = st.text_area("Notes", value=edit_prop.notes or "" if edit_prop else "", height=60)

                submitted = st.form_submit_button("💾 Save Property", use_container_width=True)
                if submitted:
                    if not propnum.strip():
                        st.error("PROPNUM is required")
                    else:
                        existing = db.query(ACProperty).filter(ACProperty.propnum == propnum.strip()).first()
                        if existing and not edit_prop:
                            st.error(f"PROPNUM '{propnum}' already exists")
                        else:
                            if not existing:
                                p = ACProperty(propnum=propnum.strip())
                                db.add(p)
                            else:
                                p = existing
                            p.propname = propname
                            p.api_num = api_num
                            p.state = state
                            p.county = county
                            p.basin = basin
                            p.field = field
                            p.operator = operator
                            p.well_type = well_type
                            p.entity_type = entity_type
                            p.status = status
                            p.working_interest = wi
                            p.net_revenue_interest = nri
                            p.royalty_interest = royalty
                            p.first_prod_date = datetime.combine(first_prod, datetime.min.time()) if first_prod else None
                            p.notes = notes
                            db.commit()
                            st.success(f"✅ Saved {propnum}")
                            st.session_state.pop("pm_selected_propnum", None)
                            st.rerun()

            if edit_prop:
                if st.button("🗑️ Delete Property", type="secondary", use_container_width=True):
                    edit_prop.is_active = False
                    db.commit()
                    st.session_state.pop("pm_selected_propnum", None)
                    st.rerun()
                if st.button("✖ Clear Selection", use_container_width=True):
                    st.session_state.pop("pm_selected_propnum", None)
                    st.rerun()

    # ─────────────────────────────────────────────────────────────────
    # TAB 2: PROJECTS
    # ─────────────────────────────────────────────────────────────────
    with tab_projects:
        pc1, pc2 = st.columns([2, 2])

        with pc1:
            st.subheader("Projects (AC_PROJECT)")
            projects = db.query(ACProject).filter(ACProject.is_active == True).order_by(ACProject.project_name).all()

            if projects:
                proj_df = pd.DataFrame([{
                    "ID": p.id,
                    "Name": p.project_name,
                    "Code": p.project_code or "—",
                    "Type": p.project_type,
                    "Disc. Rate": f"{p.default_discount_rate:.1f}%",
                    "Created": p.created_at.strftime("%Y-%m-%d") if p.created_at else "—",
                } for p in projects])
                sel = st.dataframe(proj_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
                sel_rows = sel.selection.rows
                if sel_rows:
                    st.session_state["pm_selected_project_id"] = projects[sel_rows[0]].id
            else:
                st.info("No projects yet.")

        with pc2:
            st.subheader("New Project")
            with st.form("project_form"):
                pname = st.text_input("Project Name *")
                pcode = st.text_input("Project Code", max_chars=20)
                pdesc = st.text_area("Description", height=60)
                c1, c2 = st.columns(2)
                ptype = c1.selectbox("Type", ["WORKING", "BUDGET", "ACQUISITION"])
                pdisc = c2.number_input("Default Discount Rate (%)", 0.0, 50.0, 10.0, step=0.5)
                sub = st.form_submit_button("➕ Create Project", use_container_width=True)
                if sub:
                    if not pname.strip():
                        st.error("Project name required")
                    else:
                        proj = ACProject(
                            project_name=pname.strip(),
                            project_code=pcode or None,
                            description=pdesc or None,
                            project_type=ptype,
                            default_discount_rate=pdisc,
                        )
                        db.add(proj)
                        db.commit()
                        st.success(f"✅ Created project '{pname}'")
                        st.rerun()

        # Assign properties to selected project
        sel_proj_id = st.session_state.get("pm_selected_project_id")
        if sel_proj_id:
            sel_proj = db.query(ACProject).filter(ACProject.id == sel_proj_id).first()
            if sel_proj:
                st.divider()
                st.subheader(f"Properties in '{sel_proj.project_name}'")
                from sqlalchemy import select as sa_select
                assigned = db.execute(
                    sa_select(project_property.c.propnum).where(project_property.c.project_id == sel_proj_id)
                ).fetchall()
                assigned_set = {r[0] for r in assigned}
                all_props = db.query(ACProperty).filter(ACProperty.is_active == True).order_by(ACProperty.propname).all()

                cp1, cp2 = st.columns(2)
                with cp1:
                    st.caption("**Assigned**")
                    assigned_props = [p for p in all_props if p.propnum in assigned_set]
                    if assigned_props:
                        for p in assigned_props:
                            c_a, c_b = st.columns([4, 1])
                            c_a.write(f"`{p.propnum}` {p.propname or ''}")
                            if c_b.button("✖", key=f"rem_{p.propnum}"):
                                db.execute(project_property.delete().where(
                                    (project_property.c.project_id == sel_proj_id) &
                                    (project_property.c.propnum == p.propnum)
                                ))
                                db.commit()
                                st.rerun()
                    else:
                        st.caption("No properties assigned.")

                with cp2:
                    st.caption("**Add Property**")
                    avail = [p for p in all_props if p.propnum not in assigned_set]
                    if avail:
                        to_add = st.selectbox("Select", ["— Choose —"] + [f"{p.propnum} — {p.propname or ''}" for p in avail], key="add_prop_sel")
                        if st.button("➕ Add", use_container_width=True):
                            if to_add != "— Choose —":
                                add_propnum = to_add.split(" — ")[0]
                                db.execute(project_property.insert().values(project_id=sel_proj_id, propnum=add_propnum))
                                db.commit()
                                st.rerun()
                    else:
                        st.caption("All properties assigned.")

    # ─────────────────────────────────────────────────────────────────
    # TAB 3: SCENARIOS
    # ─────────────────────────────────────────────────────────────────
    with tab_scenarios:
        projects = db.query(ACProject).filter(ACProject.is_active == True).order_by(ACProject.project_name).all()
        if not projects:
            st.info("Create a project first.")
        else:
            sc1, sc2 = st.columns([2, 2])

            with sc1:
                st.subheader("Scenarios (AC_SCENARIO)")
                selected_project_for_scen = st.selectbox(
                    "Project", projects, format_func=lambda p: p.project_name, key="scen_proj_sel"
                )
                scens = db.query(ACScenario).filter(
                    ACScenario.project_id == selected_project_for_scen.id,
                    ACScenario.is_active == True,
                ).order_by(ACScenario.scenario_name).all()

                if scens:
                    scen_df = pd.DataFrame([{
                        "ID": s.id,
                        "Scenario": s.scenario_name,
                        "Oil $/BBL": f"${s.oil_price:.2f}" if s.oil_price else "—",
                        "Gas $/MCF": f"${s.gas_price:.2f}" if s.gas_price else "—",
                        "Disc. %": f"{s.discount_rate:.1f}%",
                        "Base?": "✓" if s.is_base_case else "",
                    } for s in scens])
                    st.dataframe(scen_df, use_container_width=True, hide_index=True, height=300)
                else:
                    st.info("No scenarios for this project.")

            with sc2:
                st.subheader("New Scenario")
                with st.form("scen_form"):
                    sname = st.text_input("Scenario Name *", placeholder="Base Case")
                    scode = st.text_input("Code", max_chars=10, placeholder="BASE")
                    sdesc = st.text_area("Description", height=50)

                    st.markdown("**Price Deck**")
                    sc_c1, sc_c2, sc_c3 = st.columns(3)
                    oil_px = sc_c1.number_input("Oil ($/BBL)", 0.0, 500.0, 70.0, step=1.0)
                    gas_px = sc_c2.number_input("Gas ($/MCF)", 0.0, 50.0, 3.0, step=0.10)
                    ngl_px = sc_c3.number_input("NGL ($/BBL)", 0.0, 500.0, 28.0, step=1.0)

                    st.markdown("**Economic Parameters**")
                    ec_c1, ec_c2, ec_c3 = st.columns(3)
                    disc = ec_c1.number_input("Discount Rate (%)", 0.0, 50.0, 10.0, step=0.5)
                    tax = ec_c2.number_input("Severance Tax (%)", 0.0, 30.0, 5.0, step=0.5)
                    adv = ec_c3.number_input("Ad Valorem (%)", 0.0, 10.0, 2.0, step=0.1)

                    chance = st.slider("Chance of Success (XINVWT)", 0.0, 1.0, 1.0, 0.05)
                    is_base = st.checkbox("Mark as Base Case")
                    econ_start = st.date_input("Econ Start Date", value=date.today().replace(day=1))

                    sub = st.form_submit_button("➕ Create Scenario", use_container_width=True)
                    if sub:
                        if not sname.strip():
                            st.error("Scenario name required")
                        else:
                            scen = ACScenario(
                                project_id=selected_project_for_scen.id,
                                scenario_name=sname.strip(),
                                scenario_code=scode or None,
                                description=sdesc or None,
                                oil_price=oil_px,
                                gas_price=gas_px,
                                ngl_price=ngl_px,
                                discount_rate=disc,
                                tax_rate=tax / 100,
                                ad_valorem_rate=adv / 100,
                                chance_of_success=chance,
                                is_base_case=is_base,
                                econ_start_date=datetime.combine(econ_start, datetime.min.time()),
                            )
                            db.add(scen)
                            db.commit()
                            st.success(f"✅ Created scenario '{sname}'")
                            st.rerun()

finally:
    db.close()
