from __future__ import annotations

import os
import textwrap
from typing import Optional, Callable

import pandas as pd
import streamlit as st


def _dedent(s: str) -> str:
    return textwrap.dedent(s).strip("\n")


def housing_page(
    *,
    render_html: Callable[[str], None],
    fallback_listing_uri: Optional[str],
    remote_fallback_url: Optional[str],
    csv_path: str = "housing_listings.csv",
) -> None:
    render_html("""
    <div class="card-soft">
      <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Isla Vista Housing (CSV snapshot)</div>
      <div class="small-muted">
        Filters below help you find fits by price, bedrooms, status, and pet policy.
      </div>
    </div>
    <div class="section-gap"></div>
    """)

    if not os.path.exists(csv_path):
        st.error(f"Missing housing CSV: {csv_path}")
        st.caption("Put your file in the project root or update csv_path in gauchoGPT.py.")
        return

    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]

    # normalize common column names
    if "installment" in df.columns and "price" not in df.columns:
        df["price"] = df["installment"]
    if "price" not in df.columns:
        df["price"] = None

    # best-effort numeric price for slider
    df["price_num"] = (
        df["price"].astype(str)
        .str.replace(r"[^0-9.]", "", regex=True)
        .replace("", pd.NA)
        .astype(float)
    )

    def col_or_empty(name: str) -> pd.Series:
        return df[name] if name in df.columns else pd.Series([""] * len(df))

    df["address"] = col_or_empty("address").astype(str)
    df["beds"] = col_or_empty("beds").astype(str)
    df["baths"] = col_or_empty("baths").astype(str)
    df["status"] = col_or_empty("status").astype(str)
    df["pet_policy"] = col_or_empty("pet_policy").astype(str)
    df["max_residents"] = col_or_empty("max_residents").astype(str)
    df["availability"] = col_or_empty("availability").astype(str)
    df["included_utilities"] = col_or_empty("included_utilities").astype(str)
    df["image_url"] = col_or_empty("image_url").astype(str)
    df["link"] = col_or_empty("link").astype(str)
    df["unit"] = col_or_empty("unit").astype(str)

    # ---------------------------
    # Filters row (matches your screenshot vibe)
    # ---------------------------
    c1, c2, c3, c4 = st.columns([1.3, 1, 1, 1], gap="large")

    price_max_default = float(df["price_num"].dropna().max()) if df["price_num"].notna().any() else 20000.0

    with c1:
        price_max = st.slider("Max monthly installment", 0, int(price_max_default), int(price_max_default))
    with c2:
        bed_opts = ["Any"] + sorted([b for b in df["beds"].unique() if b and b != "nan"])
        beds = st.selectbox("Bedrooms", bed_opts, index=0)
    with c3:
        status_opts = ["Any"] + sorted([s for s in df["status"].unique() if s and s != "nan"])
        status = st.selectbox("Status filter", status_opts, index=0)
    with c4:
        pet_opts = ["Any"] + sorted([p for p in df["pet_policy"].unique() if p and p != "nan"])
        pet = st.selectbox("Pet policy", pet_opts, index=0)

    filtered = df.copy()
    if filtered["price_num"].notna().any():
        filtered = filtered[(filtered["price_num"].isna()) | (filtered["price_num"] <= price_max)]
    if beds != "Any":
        filtered = filtered[filtered["beds"] == beds]
    if status != "Any":
        filtered = filtered[filtered["status"] == status]
    if pet != "Any":
        filtered = filtered[filtered["pet_policy"] == pet]

    st.caption(f"Showing {len(filtered)} of {len(df)} units • Price ≤ ${price_max:,}")

    with st.expander("📊 View table of filtered units"):
        show_cols = [c for c in ["address", "unit", "price", "beds", "baths", "max_residents", "status", "pet_policy", "availability"] if c in filtered.columns]
        st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)

    st.divider()

    # ---------------------------
    # Listing cards
    # ---------------------------
    for _, row in filtered.iterrows():
        address = str(row.get("address", "")).strip()
        unit = str(row.get("unit", "")).strip()
        price = str(row.get("price", "")).strip()
        beds_s = str(row.get("beds", "")).strip()
        baths_s = str(row.get("baths", "")).strip()
        max_res = str(row.get("max_residents", "")).strip()
        pet_s = str(row.get("pet_policy", "")).strip()
        availability = str(row.get("availability", "")).strip()
        status_s = str(row.get("status", "")).strip()
        utils = str(row.get("included_utilities", "")).strip()
        link = str(row.get("link", "")).strip()
        image_url = str(row.get("image_url", "")).strip()

        pills = []
        if beds_s: pills.append(f"{beds_s} bed")
        if baths_s: pills.append(f"{baths_s} bath")
        if max_res: pills.append(f"Up to {max_res} residents")
        if pet_s: pills.append(pet_s)

        # pick an image
        img_src = ""
        if image_url and image_url.lower() != "nan":
            img_src = image_url
        elif fallback_listing_uri:
            img_src = fallback_listing_uri
        elif remote_fallback_url:
            img_src = remote_fallback_url

        pills_html = "".join([f'<span class="pill">{p}</span>' for p in pills])

        render_html(_dedent(f"""
        <div class="listing-card">
          <div class="listing-grid">
            <div class="listing-main">
              <div class="listing-title">{address}</div>
              <div class="listing-sub">{address}{(" - " + unit) if unit else ""}</div>

              <div class="listing-pills">{pills_html}</div>

              <div class="listing-status">
                <span class="ok">{availability}</span>
              </div>

              <div class="listing-price">
                <span class="money">{price}</span>
                {f'<span class="small-muted"> • {status_s}</span>' if status_s else ""}
              </div>

              {f'<div class="small-muted">Included utilities: {utils}</div>' if utils else ""}
              {f'<div style="margin-top:10px;"><a class="link-btn" href="{link}" target="_blank">Open listing</a></div>' if link else ""}
            </div>

            <div class="listing-img">
              {f'<img src="{img_src}" alt="listing" />' if img_src else ""}
            </div>
          </div>
        </div>
        <div class="section-gap"></div>
        """))
