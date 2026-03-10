"""
Data Manager — CSV import, production upload, bulk property import.
"""
import streamlit as st
import pandas as pd
import io
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.db import init_db, get_db, ACProperty, ACProduct
from components.auth import require_auth
from datetime import date

st.set_page_config(page_title="Data Manager — SE_ARIES", layout="wide", page_icon="🗄️")
init_db()
require_auth()

st.title("🗄️ Data Manager")
st.caption("Import/export production history and property data")

db = get_db()
try:
    tab_prod, tab_props_import, tab_export = st.tabs([
        "📥 Production History Import",
        "📥 Property Bulk Import",
        "📤 Export Data",
    ])

    # ─────────────────────────────────────────────────────────────────
    # TAB 1: PRODUCTION IMPORT
    # ─────────────────────────────────────────────────────────────────
    with tab_prod:
        st.subheader("Upload Production History (AC_PRODUCT)")

        props = db.query(ACProperty).filter(ACProperty.is_active == True).order_by(ACProperty.propname).all()
        if not props:
            st.warning("Add properties first.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                prop_opts = {f"{p.propnum} — {p.propname or 'Unnamed'}": p.propnum for p in props}
                sel_prop = st.selectbox("Target Property", list(prop_opts.keys()))
                propnum = prop_opts[sel_prop]

                uploaded = st.file_uploader(
                    "Upload CSV",
                    type=["csv"],
                    help="Required columns: date (YYYY-MM-DD), oil_bbl, gas_mcf\nOptional: water_bbl, days_on",
                )

                st.markdown("**Expected CSV format:**")
                sample = pd.DataFrame({
                    "date": ["2023-01-01", "2023-02-01", "2023-03-01"],
                    "oil_bbl": [25000, 22000, 19800],
                    "gas_mcf": [45000, 41000, 37500],
                    "water_bbl": [8000, 9000, 10000],
                    "days_on": [31, 28, 31],
                })
                st.dataframe(sample, hide_index=True, use_container_width=True)
                csv_template = sample.to_csv(index=False)
                st.download_button("⬇️ Download Template", csv_template, "production_template.csv", "text/csv")

            with c2:
                if uploaded:
                    df = pd.read_csv(uploaded)
                    st.subheader("Preview")
                    st.dataframe(df.head(20), use_container_width=True, hide_index=True)

                    if st.button("✅ Import Production Records", type="primary"):
                        imported, errors = 0, []
                        for i, row in df.iterrows():
                            try:
                                prod_date = date.fromisoformat(str(row["date"]).strip())
                                # Try update existing, else insert
                                existing = db.query(ACProduct).filter(
                                    ACProduct.propnum == propnum,
                                    ACProduct.prod_date == prod_date,
                                ).first()

                                oil = float(row.get("oil_bbl", 0) or 0)
                                gas = float(row.get("gas_mcf", 0) or 0)
                                water = float(row.get("water_bbl", 0) or 0)
                                days = float(row.get("days_on", 30) or 30)
                                oil_rate = oil / days if days > 0 else 0
                                gas_rate = gas / days if days > 0 else 0

                                if existing:
                                    existing.gross_oil_bbl = oil
                                    existing.gross_gas_mcf = gas
                                    existing.gross_water_bbl = water
                                    existing.days_on = days
                                    existing.oil_rate_bopd = oil_rate
                                    existing.gas_rate_mcfd = gas_rate
                                    existing.data_source = "CSV_IMPORT"
                                else:
                                    db.add(ACProduct(
                                        propnum=propnum,
                                        prod_date=prod_date,
                                        prod_year=prod_date.year,
                                        prod_month=prod_date.month,
                                        days_on=days,
                                        gross_oil_bbl=oil,
                                        gross_gas_mcf=gas,
                                        gross_water_bbl=water,
                                        net_oil_bbl=oil,
                                        net_gas_mcf=gas,
                                        oil_rate_bopd=oil_rate,
                                        gas_rate_mcfd=gas_rate,
                                        data_source="CSV_IMPORT",
                                    ))
                                imported += 1
                            except Exception as ex:
                                errors.append(f"Row {i+2}: {ex}")

                        db.commit()
                        st.success(f"✅ Imported {imported} records")
                        if errors:
                            st.warning(f"{len(errors)} errors:")
                            for e in errors[:10]:
                                st.caption(e)

        # Current production summary
        st.divider()
        st.subheader("Production Summary by Property")
        from sqlalchemy import func
        summary = db.query(
            ACProduct.propnum,
            func.count(ACProduct.id).label("months"),
            func.sum(ACProduct.gross_oil_bbl).label("total_oil"),
            func.sum(ACProduct.gross_gas_mcf).label("total_gas"),
            func.max(ACProduct.oil_rate_bopd).label("peak_oil"),
        ).group_by(ACProduct.propnum).all()

        if summary:
            sum_df = pd.DataFrame([{
                "PROPNUM": r.propnum,
                "Months": r.months,
                "Total Oil (MSTB)": f"{(r.total_oil or 0)/1000:.1f}",
                "Total Gas (MMCF)": f"{(r.total_gas or 0)/1000:.1f}",
                "Peak Rate (BOPD)": f"{(r.peak_oil or 0):.0f}",
            } for r in summary])
            st.dataframe(sum_df, use_container_width=True, hide_index=True)
        else:
            st.info("No production history imported yet.")

    # ─────────────────────────────────────────────────────────────────
    # TAB 2: PROPERTY BULK IMPORT
    # ─────────────────────────────────────────────────────────────────
    with tab_props_import:
        st.subheader("Bulk Property Import (AC_PROPERTY)")

        st.markdown("**Required column:** `propnum`  |  Optional: `propname, api_num, state, county, basin, field, operator, well_type, wi, nri`")

        sample_props = pd.DataFrame({
            "propnum": ["PB-010", "PB-011"],
            "propname": ["Sample Well 1H", "Sample Well 2H"],
            "api_num": ["42-003-99999-0000", "42-003-88888-0000"],
            "state": ["TX", "TX"],
            "county": ["Midland", "Martin"],
            "basin": ["Permian", "Permian"],
            "field": ["Wolfcamp", "Wolfcamp"],
            "well_type": ["OIL", "OIL"],
            "wi": [1.0, 0.5],
            "nri": [0.825, 0.413],
        })
        st.download_button("⬇️ Download Property Template", sample_props.to_csv(index=False), "property_template.csv", "text/csv")

        prop_upload = st.file_uploader("Upload Properties CSV", type=["csv"], key="prop_upload")
        if prop_upload:
            prop_df = pd.read_csv(prop_upload)
            st.dataframe(prop_df.head(20), use_container_width=True, hide_index=True)

            if st.button("✅ Import Properties", type="primary"):
                created, skipped, errors = 0, 0, []
                for i, row in prop_df.iterrows():
                    try:
                        pn = str(row.get("propnum", "")).strip()
                        if not pn:
                            continue
                        existing = db.query(ACProperty).filter(ACProperty.propnum == pn).first()
                        if existing:
                            skipped += 1
                            continue
                        db.add(ACProperty(
                            propnum=pn,
                            propname=str(row.get("propname", "")) or None,
                            api_num=str(row.get("api_num", "")) or None,
                            state=str(row.get("state", "")) or None,
                            county=str(row.get("county", "")) or None,
                            basin=str(row.get("basin", "")) or None,
                            field=str(row.get("field", "")) or None,
                            operator=str(row.get("operator", "")) or None,
                            well_type=str(row.get("well_type", "OIL")),
                            working_interest=float(row.get("wi", 1.0) or 1.0),
                            net_revenue_interest=float(row.get("nri", 1.0) or 1.0),
                            created_by="CSV_IMPORT",
                        ))
                        created += 1
                    except Exception as ex:
                        errors.append(f"Row {i+2}: {ex}")
                db.commit()
                st.success(f"✅ Created {created}, skipped {skipped} (already exist)")
                if errors:
                    for e in errors[:10]:
                        st.caption(e)

    # ─────────────────────────────────────────────────────────────────
    # TAB 3: EXPORT
    # ─────────────────────────────────────────────────────────────────
    with tab_export:
        st.subheader("Export Data")

        exp_c1, exp_c2 = st.columns(2)

        with exp_c1:
            st.markdown("**Export Properties**")
            props_all = db.query(ACProperty).filter(ACProperty.is_active == True).all()
            if props_all:
                props_export = pd.DataFrame([{
                    "propnum": p.propnum, "propname": p.propname, "api_num": p.api_num,
                    "state": p.state, "county": p.county, "basin": p.basin, "field": p.field,
                    "formation": p.formation, "operator": p.operator, "well_type": p.well_type,
                    "working_interest": p.working_interest, "net_revenue_interest": p.net_revenue_interest,
                    "royalty_interest": p.royalty_interest, "status": p.status,
                } for p in props_all])
                st.dataframe(props_export.head(), use_container_width=True, hide_index=True)
                st.download_button(
                    "⬇️ Export All Properties (CSV)",
                    props_export.to_csv(index=False),
                    "se_aries_properties.csv", "text/csv",
                )

        with exp_c2:
            st.markdown("**Export Production History**")
            sel_prop_export = st.selectbox("Select Property", ["All"] + [p.propnum for p in props_all], key="export_prop")
            prod_q = db.query(ACProduct)
            if sel_prop_export != "All":
                prod_q = prod_q.filter(ACProduct.propnum == sel_prop_export)
            prod_records = prod_q.order_by(ACProduct.propnum, ACProduct.prod_date).all()
            if prod_records:
                prod_export = pd.DataFrame([{
                    "propnum": r.propnum, "date": r.prod_date, "days_on": r.days_on,
                    "oil_bbl": r.gross_oil_bbl, "gas_mcf": r.gross_gas_mcf,
                    "water_bbl": r.gross_water_bbl, "oil_rate_bopd": r.oil_rate_bopd,
                    "gas_rate_mcfd": r.gas_rate_mcfd,
                } for r in prod_records])
                st.caption(f"{len(prod_records)} records")
                st.download_button(
                    "⬇️ Export Production (CSV)",
                    prod_export.to_csv(index=False),
                    f"se_aries_production_{sel_prop_export}.csv", "text/csv",
                )
            else:
                st.info("No production records to export.")

finally:
    db.close()
