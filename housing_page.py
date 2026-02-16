from __future__ import annotations
import pandas as pd
import streamlit as st
from typing import Callable

CSV = "iv_housing_listings.csv"

def housing_page(render_html: Callable[[str], None]):

    render_html("""
    <div class="card-soft">
        <div class="listing-title">Isla Vista Housing (CSV snapshot)</div>
        <div class="small-muted">Filter listings by price, bedrooms, status and pets.</div>
    </div>
    <div class="section-gap"></div>
    """)

    df = pd.read_csv(CSV)

    # ---------- Filters ----------
    c1, c2, c3 = st.columns(3)

    with c1:
        max_price = int(df.price.max())
        price_limit = st.slider("Max monthly installment", 0, max_price, max_price)

    with c2:
        beds = st.selectbox("Bedrooms", ["Any", 1,2,3,4,5])

    with c3:
        status = st.selectbox("Status", ["Any","available","leased","processing"])

    # ---------- Apply ----------
    filtered = df[df.price <= price_limit]

    if beds != "Any":
        filtered = filtered[filtered.bedrooms == beds]

    if status != "Any":
        filtered = filtered[filtered.status == status]

    render_html(f"""
    <div class="card-soft small-muted">
        Showing <b>{len(filtered)}</b> of <b>{len(df)}</b> units • Price ≤ ${price_limit:,}
    </div>
    <div class="section-gap"></div>
    """)

    # ---------- Cards ----------
    for _, r in filtered.iterrows():

        price = f"${int(r.price):,}/installment"
        ppp = f"≈ ${int(r.price/r.max_residents):,} per person" if r.max_residents else ""

        render_html(f"""
        <div class="card listing">
            <div class="listing-title">{r.street}, Isla Vista, CA</div>
            <div class="listing-sub">{r.street} - {r.unit}</div>

            <div class="pills">
                <span class="pill">{int(r.bedrooms)} bed</span>
                <span class="pill">{int(r.bathrooms)} bath</span>
                <span class="pill">Up to {int(r.max_residents)} residents</span>
                <span class="pill pill-gold">{r.pet_policy}</span>
            </div>

            <div class="status-ok">{r.status}</div>
            <div class="price-row">{price} <span class="small-muted">{ppp}</span></div>
        </div>
        <div class="section-gap"></div>
        """)
