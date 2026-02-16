from __future__ import annotations
from typing import Callable, Optional
import os
import pandas as pd
import streamlit as st

CSV_PATH = "iv_housing_listings.csv"

def housing_page(
    *,
    render_html: Callable[[str], None],
    fallback_listing_uri: Optional[str] = None,
    remote_fallback_url: Optional[str] = None,
):
    render_html("""
    <div class="card-soft">
      <div style="font-size:2.2rem; font-weight:950; letter-spacing:-0.02em;">🏠 Isla Vista Housing (CSV snapshot)</div>
      <div class="small-muted">
        Snapshot from ivproperties.com (2026–27). Filters below help you find fits by price, bedrooms, status, and pet policy.
      </div>
    </div>
    <div class="section-gap"></div>
    """)

    if not os.path.exists(CSV_PATH):
        st.error(f"Missing {CSV_PATH}. Put it next to gauchoGPT.py")
        return

    df = pd.read_csv(CSV_PATH)

    # safety: ensure columns exist
    for col in ["street","unit","price","bedrooms","bathrooms","max_residents","pet_policy","status","utilities","avail_start","avail_end","listing_url","image_url"]:
        if col not in df.columns:
            df[col] = None

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")
    df["status"] = df["status"].fillna("available").astype(str).str.lower().str.strip()
    df["pet_policy"] = df["pet_policy"].fillna("").astype(str)

    # -------- Filters
    c1, c2, c3, c4 = st.columns([1.6, 1, 1, 1])

    with c1:
        max_price = int(df["price"].max()) if df["price"].notna().any() else 12000
        price_limit = st.slider("Max monthly installment", 0, max_price, max_price, step=100)

    with c2:
        beds_choice = st.selectbox("Bedrooms", ["Any", "Studio", "1", "2", "3", "4", "5+"])

    with c3:
        status_choice = st.selectbox("Status filter", ["Any", "available", "processing", "leased"])

    with c4:
        pet_choice = st.selectbox("Pet policy", ["Any", "Pet friendly only", "No pets"])

    filtered = df.copy()
    filtered = filtered[(filtered["price"].isna()) | (filtered["price"] <= price_limit)]

    if beds_choice == "Studio":
        filtered = filtered[(filtered["bedrooms"].fillna(0) == 0)]
    elif beds_choice == "5+":
        filtered = filtered[filtered["bedrooms"] >= 5]
    elif beds_choice != "Any":
        filtered = filtered[filtered["bedrooms"] == int(beds_choice)]

    if status_choice != "Any":
        filtered = filtered[filtered["status"] == status_choice]

    if pet_choice == "Pet friendly only":
        filtered = filtered[filtered["pet_policy"].str.contains("pet", case=False, na=False)]
    elif pet_choice == "No pets":
        filtered = filtered[filtered["pet_policy"].str.contains("no pets", case=False, na=False)]

    render_html(f"""
    <div class="card-soft small-muted">
      Showing <strong>{len(filtered)}</strong> of <strong>{len(df)}</strong> units • Price ≤
      <span class="pill pill-blue">${price_limit:,}</span>
    </div>
    <div class="section-gap"></div>
    """)

    with st.expander("📊 View table of filtered units"):
        st.dataframe(filtered, use_container_width=True)

    # -------- Cards
    for _, r in filtered.iterrows():
        street = str(r["street"] or "").strip()
        unit = str(r["unit"] or "").strip()
        price = r["price"]
        beds = r["bedrooms"]
        baths = r["bathrooms"]
        max_res = r["max_residents"]
        pet = str(r["pet_policy"] or "").strip() or "Pet policy unknown"
        status = str(r["status"] or "").strip()
        utilities = str(r["utilities"] or "").strip()
        a1 = str(r["avail_start"] or "").strip()
        a2 = str(r["avail_end"] or "").strip()

        # status line like screenshot
        if status == "available":
            status_line = f"Available {a1}–{a2} (applications open)".strip()
            status_cls = "status-ok"
        elif status == "processing":
            status_line = "Processing applications"
            status_cls = "status-warn"
        else:
            status_line = "Currently leased"
            status_cls = "status-muted"

        price_txt = f"${int(price):,}/installment" if pd.notna(price) else "Price not listed"
        ppp_txt = ""
        if pd.notna(price) and pd.notna(max_res) and max_res > 0:
            ppp_txt = f"≈ ${int(price/max_res):,} per person"

        render_html(f"""
        <div class="card">
          <div class="listing-title">{street}, Isla Vista, CA</div>
          <div class="listing-sub">{street} - {unit}</div>

          <div class="pills">
            <span class="pill">{'Studio' if (pd.isna(beds) or beds == 0) else f'{int(beds)} bed'}</span>
            <span class="pill">{'?' if pd.isna(baths) else int(baths)} bath</span>
            <span class="pill">Up to {int(max_res) if pd.notna(max_res) else '?'} residents</span>
            <span class="pill pill-gold">{pet}</span>
          </div>

          <div class="{status_cls}" style="margin-top:10px;">{status_line}</div>
          <div class="price-row">{price_txt} <span class="small-muted">{(' · ' + ppp_txt) if ppp_txt else ''}</span></div>
          {f"<div class='small-muted' style='margin-top:6px;'>Included utilities: {utilities}</div>" if utilities else ""}
        </div>
        <div class="section-gap"></div>
        """)

