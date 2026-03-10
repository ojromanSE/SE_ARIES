"""Shared sidebar state helpers."""
import streamlit as st
from services.db import get_db, ACProject, ACScenario, ACProperty


def render_sidebar_selectors():
    """
    Renders Project / Scenario / Property selectors in the sidebar.
    Returns (selected_project, selected_scenario, selected_propnum).
    """
    db = get_db()
    try:
        projects = db.query(ACProject).filter(ACProject.is_active == True).order_by(ACProject.project_name).all()

        st.sidebar.markdown("---")
        st.sidebar.subheader("Active Context")

        # Project selector
        proj_names = ["— Select Project —"] + [p.project_name for p in projects]
        proj_idx = st.sidebar.selectbox("Project", range(len(proj_names)), format_func=lambda i: proj_names[i], key="sb_project_idx")
        selected_project = projects[proj_idx - 1] if proj_idx > 0 else None

        # Scenario selector
        selected_scenario = None
        if selected_project:
            scenarios = db.query(ACScenario).filter(
                ACScenario.project_id == selected_project.id,
                ACScenario.is_active == True,
            ).order_by(ACScenario.scenario_name).all()

            if scenarios:
                scen_names = [s.scenario_name for s in scenarios]
                scen_idx = st.sidebar.selectbox("Scenario", range(len(scen_names)), format_func=lambda i: scen_names[i], key="sb_scenario_idx")
                selected_scenario = scenarios[scen_idx]
                st.sidebar.caption(f"Oil: ${selected_scenario.oil_price:.0f}/BBL | Gas: ${selected_scenario.gas_price:.2f}/MCF | Disc: {selected_scenario.discount_rate:.0f}%")
            else:
                st.sidebar.info("No scenarios — create one in Project Manager")

        # Property selector
        selected_propnum = None
        if selected_project:
            props = db.query(ACProperty).filter(ACProperty.is_active == True).order_by(ACProperty.propname).all()
            if props:
                prop_options = {f"{p.propnum} — {p.propname or 'Unnamed'}": p.propnum for p in props}
                chosen = st.sidebar.selectbox("Property", ["— Select —"] + list(prop_options.keys()), key="sb_property")
                if chosen != "— Select —":
                    selected_propnum = prop_options[chosen]

        st.sidebar.markdown("---")
        return selected_project, selected_scenario, selected_propnum

    finally:
        db.close()
