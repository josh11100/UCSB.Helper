import streamlit as st
from pages.housing_page import housing_page

st.set_page_config(layout="wide", page_title="GauchoGPT")

st.sidebar.title("GauchoGPT")
page = st.sidebar.radio("Navigate", ["Housing"])

if page == "Housing":
    housing_page()
