from __future__ import annotations

import os
import sqlite3
import textwrap
from typing import Optional

import streamlit as st
import pandas as pd

DB_PATH = "gauchoGPT.db"
COURSES_CSV = "major_courses_by_quarter.csv"

MAJOR_SHEETS = {
    "Statistics & Data Science": "https://www.pstat.ucsb.edu/undergraduate/majors-minors/stats-and-data-science-major",
    "Computer Science": "https://cs.ucsb.edu/education/undergraduate/current-students",
    "Economics": "https://econ.ucsb.edu/programs/undergraduate/majors",
    "Mathematics": "https://www.math.ucsb.edu/undergraduate/proposed-courses-study-plans",
    "Biology": "https://ucsbcatalog.coursedog.com/programs/BSBIOSC",
    "Psychology": "https://psych.ucsb.edu/undergraduate/major-requirements",
    "Chemistry": "https://undergrad.chem.ucsb.edu/academic-programs/chemistry-bs",
    "Physics": "https://www.physics.ucsb.edu/academics/undergraduate/majors",
    "Philosophy": "https://www.philosophy.ucsb.edu/undergraduate/undergraduate-major-philosophy",
    "English": "https://www.english.ucsb.edu/undergraduate/for-majors/requirements/",
}


def _dedent(s: str) -> str:
    return textwrap.dedent(s).strip("\n")


def load_courses_df() -> Optional[pd.DataFrame]:
    if not os.path.exists(COURSES_CSV):
        return None

    df = pd.read_csv(COURSES_CSV)
    df.columns = [c.strip().lower() for c in df.columns]

    required = ["major", "course_code", "title", "quarter"]
    if any(c not in df.columns for c in required):
        return None

    if "units" not in df.columns:
        df["units"] = None
    if "status" not in df.columns:
        df["status"] = ""
    if "notes" not in df.columns:
        df["notes"] = ""

    df["major"] = df["major"].astype(str).str.strip()
    df["quarter"] = df["quarter"].astype(str).str.strip().str.title()
    df["course_code"] = df["course_code"].astype(str).str.strip()
    df["title"] = df["title"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip().str.title()

    return df


def get_course_stats(df: pd.DataFrame) -> dict:
    return {
        "total": len(df),
        "open": (df["status"].str.lower() == "open").sum(),
        "full": (df["status"].str.lower() == "full").sum(),
        "mixed": (df["status"].str.lower() == "mixed").sum(),
    }


def display_course_card(row) -> None:
    code = str(row.get("course_code", "")).strip()
    title = str(row.get("title", "")).strip()
    units = str(row.get("units", "")).strip()
    status = str(row.get("status", "")).strip()
    notes = str(row.get("notes", "")).strip()

    status_lower = status.lower()
    if status_lower == "open":
        status_bg = "#ecfdf3"
        status_cls = "ok"
    elif status_lower == "full":
        status_bg = "#fef2f2"
        status_cls = "err"
    elif status_lower == "mixed":
        status_bg = "#fffbeb"
        status_cls = "warn"
    else:
        status_bg = "#f3f4f6"
        status_cls = "muted"

    st.markdown(
        _dedent(f"""
        <div style="border-radius: 14px; overflow: hidden;
                    border: 1px solid rgba(255,255,255,0.10); margin-bottom: 14px;
                    box-shadow: 0 8px 22px rgba(0,0,0,0.25); background: rgba(10,14,22,0.65);">
          <div style="background:#003660; color:#ffffff;
                      padding:10px 14px; font-weight:800;
                      font-size:1.0rem;">
            {code}
          </div>
          <div style="padding:12px 14px;">
            <div style="font-weight:800; margin-bottom:8px; font-size:0.95rem;">{title}</div>
            <div style="margin-bottom:10px;">
              <span class="pill">{units} units</span>
              <span class="pill" style="background:{status_bg};">
                <span class="{status_cls}">{status or "Status n/a"}</span>
              </span>
            </div>
            {f'<div class="small-muted" style="line-height:1.55;">{notes}</div>' if notes else ""}
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def academics_page():
    st.header("🎓 Academics — advising & classes")
    st.caption("CSV-based course snapshot (or DB if you later add one).")

    df = load_courses_df()
    if df is None or df.empty:
        st.warning(f"⚠️ No course data found. Expected: {COURSES_CSV}")
        return

    major = st.selectbox("Select a major", sorted(df["major"].unique()))
    st.markdown("#### 📚 Major planning resources")
    if major in MAJOR_SHEETS:
        st.link_button("Open official major sheet", MAJOR_SHEETS[major])

    st.divider()

    tab_classes, tab_search, tab_planner = st.tabs(["Classes by quarter", "Course search", "My planner"])

    with tab_classes:
        quarter = st.selectbox("Quarter", sorted(df["quarter"].unique()))
        sub = df[(df["major"] == major) & (df["quarter"] == quarter)].copy()

        if sub.empty:
            st.info(f"No classes found for **{major}** in **{quarter}**")
            return

        stats = get_course_stats(sub)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", stats["total"])
        c2.metric("🟢 Open", stats["open"])
        c3.metric("🟡 Mixed", stats["mixed"])
        c4.metric("🔴 Full", stats["full"])

        with st.expander("🔍 Filter options"):
            status_filter = st.multiselect("Status", ["Open", "Mixed", "Full"], default=["Open", "Mixed", "Full"])
            if status_filter:
                sub = sub[sub["status"].isin(status_filter)]

        # 3 cards per row
        for i in range(0, len(sub), 3):
            cols = st.columns(3, gap="large")
            for j in range(3):
                idx = i + j
                if idx >= len(sub):
                    break
                with cols[j]:
                    display_course_card(sub.iloc[idx])

    with tab_search:
        q = st.text_input("Search by course code or title", placeholder="e.g., PSTAT 120A or Probability")
        if q:
            ql = q.lower().strip()
            hits = df[(df["course_code"].str.lower().str.contains(ql)) | (df["title"].str.lower().str.contains(ql))]
            st.caption(f"Found {len(hits)} matches")
            st.dataframe(hits[["major", "course_code", "title", "quarter", "units", "status"]], use_container_width=True, hide_index=True)

    with tab_planner:
        st.info("Planner stub — you can paste your planner logic here next.")
