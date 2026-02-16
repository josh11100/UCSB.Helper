from __future__ import annotations
import os
import base64
import textwrap
from typing import Optional, Dict, Any

import streamlit as st

from ui_components import topbar_html, hero_html, home_row_html
from housing_page import housing_page

# ---------------- Page Config ----------------
st.set_page_config(page_title="gauchoGPT", page_icon="🧢", layout="wide")

# ---------------- Helpers ----------------
def render_html(html: str):
    st.markdown(textwrap.dedent(html), unsafe_allow_html=True)

def img_to_data_uri(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    ext = path.split(".")[-1]
    with open(path, "rb") as f:
        return f"data:image/{ext};base64,{base64.b64encode(f.read()).decode()}"

def inject_css():
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        render_html(f"<style>{f.read()}</style>")

# ---------------- UI INIT ----------------
inject_css()
render_html(topbar_html())

# ---------------- NAV STATE ----------------
NAV = ["🏁 Home", "🏠 Housing"]
st.session_state.setdefault("nav", "🏁 Home")

# Sidebar
st.sidebar.title("gauchoGPT")
for item in NAV:
    if st.sidebar.button(item, use_container_width=True):
        st.session_state.nav = item
        st.rerun()

# ---------------- HOME ----------------
def home_page():
    render_html(hero_html())

    thumb = img_to_data_uri("assets/home_thumb.jpg")

    def row(title, desc, page):
        render_html(home_row_html(title, desc, thumb))
        _, btn = st.columns([1, .25])
        with btn:
            if st.button(f"Open {title.split()[1]}", key=title):
                st.session_state.nav = page
                st.rerun()

    row("🏠 Housing", "Browse Isla Vista listings with filters.", "🏠 Housing")

# ---------------- ROUTER ----------------
PAGES: Dict[str, Any] = {
    "🏁 Home": home_page,
    "🏠 Housing": lambda: housing_page(render_html),
}

PAGES[st.session_state.nav]()
