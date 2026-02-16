# academics_enhanced.py
from __future__ import annotations

import os
import sqlite3
from typing import Optional

import streamlit as st
import pandas as pd

try:
    from streamlit_folium import st_folium
    import folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False


# -------------------------
# Paths / data sources
# -------------------------
DB_PATH = "gauchoGPT.db"                  # optional
COURSES_CSV = "major_courses_by_quarter.csv"  # your CSV


# -------------------------
# Majors + links
# -------------------------
MAJOR_DEPARTMENTS = {
    "Statistics & Data Science": ["PSTAT"],
    "Computer Science": ["CMPSC"],
    "Economics": ["ECON"],
    "Mathematics": ["MATH"],
    "Biology": ["MCDB", "EEMB"],
    "Psychology": ["PSY"],
    "Chemistry": ["CHEM"],
    "Physics": ["PHYS"],
    "Philosophy": ["PHIL"],
    "English": ["ENGL"],
}

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

BUILDINGS = {
    "Phelps Hall (PHELP)": (34.41239, -119.84862),
    "Harold Frank Hall (HFH)": (34.41434, -119.84246),
    "Chemistry (CHEM)": (34.41165, -119.84586),
    "HSSB": (34.41496, -119.84571),
    "Library": (34.41388, -119.84627),
    "IV Theater": (34.41249, -119.86155),
    "Buchanan Hall": (34.41340, -119.84568),
    "Girvetz Hall": (34.41559, -119.84714),
    "Ellison Hall": (34.41282, -119.84989),
}


# -------------------------
# Loaders
# -------------------------
@st.cache_data(ttl=3600)
def load_courses_from_db(major: str, quarter: str = "Winter 2025") -> Optional[pd.DataFrame]:
    """Load from DB if present (optional feature)."""
    if not os.path.exists(DB_PATH):
        return None

    departments = MAJOR_DEPARTMENTS.get(major, [])
    if not departments:
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        placeholders = ",".join("?" * len(departments))

        query = f"""
            SELECT
                c.course_code,
                c.title,
                c.units,
                c.description,
                c.prerequisites,
                o.instructor,
                o.days,
                o.time,
                o.location,
                o.enrolled,
                o.capacity,
                o.status,
                o.quarter
            FROM courses c
            LEFT JOIN course_offerings o ON c.course_code = o.course_code
            WHERE c.dept IN ({placeholders})
              AND (o.quarter = ? OR o.quarter IS NULL)
            ORDER BY c.course_code
        """

        params = departments + [quarter]
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df if not df.empty else None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None


def load_courses_df() -> Optional[pd.DataFrame]:
    """Load from CSV. Expects columns: major, course_code, title, quarter, units, status, notes."""
    if not os.path.exists(COURSES_CSV):
        return None

    df = pd.read_csv(COURSES_CSV)
    df.columns = [c.strip().lower() for c in df.columns]

    required = ["major", "course_code", "title", "quarter"]
    if any(c not in df.columns for c in required):
        st.error(f"CSV missing required columns: {required}")
        return None

    for col in ["units", "status", "notes"]:
        if col not in df.columns:
            df[col] = ""

    # normalize
    df["major"] = df["major"].astype(str).str.strip()
    df["course_code"] = df["course_code"].astype(str).str.strip()
    df["title"] = df["title"].astype(str).str.strip()
    df["quarter"] = df["quarter"].astype(str).str.strip().str.title()
    df["status"] = df["status"].astype(str).str.strip().str.title()

    return df


# -------------------------
# Helpers
# -------------------------
def get_course_stats(df: pd.DataFrame) -> dict:
    s = df["status"].astype(str).str.lower()
    units_num = pd.to_numeric(df.get("units", pd.Series([None] * len(df))), errors="coerce")
    return {
        "total": len(df),
        "open": (s == "open").sum(),
        "full": (s == "full").sum(),
        "mixed": (s == "mixed").sum(),
        "avg_units": float(units_num.mean()) if units_num.notna().any() else 0.0,
    }


def display_course_card(row: pd.Series, col_container):
    with col_container:
        code = str(row.get("course_code", "")).strip()
        title = str(row.get("title", "")).strip()
        units = str(row.get("units", "")).strip()
        status = str(row.get("status", "")).strip()
        notes = str(row.get("notes", "")).strip()

        status_lower = status.lower()
        if status_lower == "open":
            status_bg = "#ecfdf3"
            status_fg = "#166534"
        elif status_lower == "full":
            status_bg = "#fef2f2"
            status_fg = "#991b1b"
        elif status_lower == "mixed":
            status_bg = "#fffbeb"
            status_fg = "#92400e"
        else:
            status_bg = "#f3f4f6"
            status_fg = "#374151"

        units_label = units if units else "n/a"

        st.markdown(
            f"""
            <div style="border-radius: 12px; overflow: hidden;
                        border: 1px solid rgba(255,255,255,0.08);
                        background: rgba(15,23,42,0.35);
                        margin-bottom: 14px;
                        box-shadow: 0 10px 24px rgba(0,0,0,0.20);">
              <div style="background:#003660; color:#ffffff;
                          padding:10px 12px; font-weight:700;
                          font-size:0.95rem;">
                {code}
              </div>
              <div style="padding:12px 12px; font-size:0.92rem;">
                <div style="font-weight:650; margin-bottom:6px;">{title}</div>

                <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
                  <span style="display:inline-block; padding:6px 10px; border-radius:999px;
                               background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.10);">
                    {units_label} units
                  </span>

                  <span style="display:inline-block; padding:6px 10px; border-radius:999px;
                               background:{status_bg}; color:{status_fg}; font-weight:700;">
                    {status or "Status n/a"}
                  </span>
                </div>

                {f"<div style='opacity:0.85; line-height:1.45;'>{notes}</div>" if notes else ""}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _quarter_season(quarter_ui: str) -> str:
    # "Winter 2025" -> "Winter"
    return quarter_ui.split()[0].strip().title()


def _available_quarters_from_csv(df: pd.DataFrame) -> list[str]:
    # If your CSV only has "Winter", generate nice labels like "Winter 2025" anyway.
    # Keep it simple: use unique quarter values.
    qs = sorted(df["quarter"].dropna().astype(str).str.strip().str.title().unique().tolist())
    return qs


# -------------------------
# Main page
# -------------------------
def academics_page():
    st.header("🎓 Academics — advising, classes & map")
    st.caption("View course data from UCSB, plan schedules, and locate buildings.")

    has_db = os.path.exists(DB_PATH)
    has_csv = os.path.exists(COURSES_CSV)

    if has_db:
        st.success("✅ Using live database with scraped UCSB course data")
    elif has_csv:
        st.info("📄 Using CSV file (you can later upgrade to a live scraper)")
    else:
        st.warning("⚠️ No course data found. Add major_courses_by_quarter.csv or run your scraper.")
        return

    major = st.selectbox("Select a major", list(MAJOR_SHEETS.keys()), index=0, key="acad_major")
    st.markdown("#### 📚 Major planning resources")
    st.link_button("Open official major sheet", MAJOR_SHEETS[major])

    st.divider()

    tab_classes, tab_search, tab_planner, tab_map, tab_analytics = st.tabs(
        ["Classes by quarter", "Course search", "My planner", "Building map", "Analytics"]
    )

    # -------------------------
    # Classes by quarter
    # -------------------------
    with tab_classes:
        st.subheader("Classes by quarter")

        # Load once (for CSV-driven quarter list)
        df_csv = load_courses_df() if has_csv and not has_db else None

        # UI quarter labels (you can edit these)
        quarter_ui = st.selectbox(
            "Quarter",
            ["Winter 2025", "Spring 2025", "Fall 2024"],
            key="acad_quarter",
        )
        quarter_season = _quarter_season(quarter_ui)  # "Winter"

        courses_df = load_courses_from_db(major, quarter_ui) if has_db else df_csv

        if courses_df is None or courses_df.empty:
            st.info(f"No course data available for **{major}** in **{quarter_ui}**.")
        else:
            # Filter major
            if "major" in courses_df.columns:
                courses_df["major"] = courses_df["major"].astype(str).str.strip()
                courses_df = courses_df[courses_df["major"] == major]

            # FIX: quarter matching supports "Winter" (CSV) and "Winter 2025" (future DB/UI)
            if "quarter" in courses_df.columns:
                courses_df["quarter"] = courses_df["quarter"].astype(str).str.strip().str.title()
                courses_df = courses_df[
                    (courses_df["quarter"] == quarter_season) |
                    (courses_df["quarter"] == quarter_ui)
                ]

            if courses_df.empty:
                st.info(f"No classes found for **{major}** in **{quarter_ui}**")
            else:
                stats = get_course_stats(courses_df)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total courses", stats["total"])
                c2.metric("🟢 Open", stats["open"])
                c3.metric("🟡 Mixed", stats["mixed"])
                c4.metric("🔴 Full", stats["full"])

                st.markdown("---")

                with st.expander("🔍 Filter options"):
                    status_filter = st.multiselect(
                        "Status",
                        ["Open", "Mixed", "Full"],
                        default=["Open", "Mixed", "Full"],
                    )

                if status_filter:
                    courses_df = courses_df[courses_df["status"].astype(str).str.title().isin(status_filter)]

                for i in range(0, len(courses_df), 3):
                    cols = st.columns(3, gap="medium")
                    for j in range(3):
                        idx = i + j
                        if idx >= len(courses_df):
                            break
                        display_course_card(courses_df.iloc[idx], cols[j])

    # -------------------------
    # Course search
    # -------------------------
    with tab_search:
        st.subheader("🔍 Search all courses")

        q = st.text_input("Search by course code or title", placeholder="e.g., PSTAT 120A or Probability")

        if not q:
            st.info("Type a search above.")
        else:
            if has_db:
                conn = sqlite3.connect(DB_PATH)
                query = """
                    SELECT course_code, title, units, dept, description
                    FROM courses
                    WHERE course_code LIKE ? OR title LIKE ? OR description LIKE ?
                    LIMIT 50
                """
                pattern = f"%{q}%"
                results = pd.read_sql_query(query, conn, params=[pattern, pattern, pattern])
                conn.close()

                if results.empty:
                    st.info("No results.")
                else:
                    st.success(f"Found {len(results)} courses")
                    st.dataframe(results, use_container_width=True, hide_index=True)
            else:
                df = load_courses_df()
                if df is None or df.empty:
                    st.info("No CSV loaded.")
                else:
                    qq = q.lower().strip()
                    mask = (
                        df["course_code"].astype(str).str.lower().str.contains(qq, na=False)
                        | df["title"].astype(str).str.lower().str.contains(qq, na=False)
                        | df["notes"].astype(str).str.lower().str.contains(qq, na=False)
                    )
                    res = df[mask].copy()
                    if res.empty:
                        st.info("No results.")
                    else:
                        st.success(f"Found {len(res)} rows")
                        st.dataframe(res, use_container_width=True, hide_index=True)

    # -------------------------
    # Planner
    # -------------------------
    with tab_planner:
        st.subheader("📝 Build your quarter schedule")

        if "planned_courses" not in st.session_state:
            st.session_state.planned_courses = []

        with st.form("add_course_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                new_course = st.text_input("Course code", placeholder="PSTAT 120A")
            with col2:
                new_units = st.number_input("Units", min_value=1, max_value=8, value=4)
            with col3:
                st.write("")
                st.write("")
                add_btn = st.form_submit_button("Add course", use_container_width=True)

            if add_btn and new_course:
                st.session_state.planned_courses.append({"Course": new_course, "Units": new_units})
                st.rerun()

        if st.session_state.planned_courses:
            df_plan = pd.DataFrame(st.session_state.planned_courses)
            st.dataframe(df_plan, use_container_width=True, hide_index=True)

            total_units = df_plan["Units"].sum()
            c1, c2 = st.columns(2)
            c1.metric("Total units", int(total_units))

            if total_units < 12:
                c2.warning("⚠️ Below minimum (12 units)")
            elif total_units <= 16:
                c2.success("✅ Typical load")
            else:
                c2.error("🔴 Heavy load (>16 units)")

            if st.button("Clear all", type="secondary"):
                st.session_state.planned_courses = []
                st.rerun()
        else:
            st.info("No courses planned yet.")

    # -------------------------
    # Map
    # -------------------------
    with tab_map:
        st.subheader("🗺️ Campus building locator")

        bname = st.selectbox("Choose a building", list(BUILDINGS.keys()), key="acad_building")
        lat, lon = BUILDINGS[bname]

        if HAS_FOLIUM:
            m = folium.Map(location=[lat, lon], zoom_start=17, control_scale=True)
            folium.Marker([lat, lon], popup=bname, tooltip=bname).add_to(m)
            st_folium(m, width=900, height=500)
        else:
            st.info("Install folium for interactive map: `pip install folium streamlit-folium`")
            st.json({"building": bname, "latitude": lat, "longitude": lon})

    # -------------------------
    # Analytics
    # -------------------------
    with tab_analytics:
        st.subheader("📊 Course analytics")

        if has_db:
            st.info("Analytics from DB can go here (fill rates, etc.).")
        else:
            df = load_courses_df()
            if df is None or df.empty:
                st.info("No data loaded.")
            else:
                st.markdown("#### Status counts (CSV)")
                st.write(df["status"].value_counts())
