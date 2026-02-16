from __future__ import annotations
from typing import Optional

def topbar_html() -> str:
    return """
    <div class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <span class="brand-dot"></span>
          <span>gauchoGPT</span>
          <small>UCSB Student Helper</small>
        </div>
        <div class="topbar-right">Home • Housing • Academics • Professors • Aid & Jobs • Q&A</div>
      </div>
    </div>
    """

def hero_html() -> str:
    return """
    <div class="hero">
      <div class="hero-title">UCSB tools, in one place.</div>
      <div class="hero-sub">
        Find housing, plan classes, check professors, and navigate aid & jobs — built for speed and clarity.
      </div>
    </div>
    <div class="section-gap"></div>
    """

def home_row_html(title: str, desc: str, thumb_uri: Optional[str] = None) -> str:
    thumb_html = f'<div class="home-thumb"><img src="{thumb_uri}" alt="thumb" /></div>' if thumb_uri else ""
    return f"""
    <div class="card">
      <div class="home-row">
        <div class="home-left">
          {thumb_html}
          <div>
            <div class="home-title">{title}</div>
            <div class="small-muted home-desc">{desc}</div>
          </div>
        </div>
      </div>
    </div>
    """
