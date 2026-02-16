from typing import Optional

def topbar_html():
    return """
    <div class="topbar">
        <b>gauchoGPT</b> UCSB Student Helper
    </div>
    """

def hero_html():
    return """
    <div class="hero">
        <div class="hero-title">UCSB tools, in one place.</div>
        <div class="hero-sub">Find housing fast.</div>
    </div>
    <div class="section-gap"></div>
    """

def home_row_html(title: str, desc: str, thumb: Optional[str]):
    img = f'<img src="{thumb}" class="home-thumb">' if thumb else ""
    return f"""
    <div class="card home-row">
        {img}
        <div>
            <div class="home-title">{title}</div>
            <div class="small-muted">{desc}</div>
        </div>
    </div>
    """

