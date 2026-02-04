from __future__ import annotations

import os

import streamlit as st

from db.seed import seed as seed_db  # ✅ 注意这里

@st.cache_resource
def _bootstrap_db():
    if os.getenv("SMART_FRIDGE_SKIP_SEED") == "1":
        return "skip"
    seed_db()
    return "ok"

_bootstrap_db()
st.markdown(
    """
<style>
:root{
  --s-1: 8px; --s-2: 12px; --s-3: 16px; --s-4: 24px; --s-5: 32px;
  --r-lg: 18px; --r-md: 14px; --r-sm: 10px;
  --surface-1: rgba(255,255,255,.86);
  --border: rgba(16,24,40,.08);
  --text: rgba(17,24,39,.92);
  --muted: rgba(17,24,39,.55);
  --shadow-1: 0 12px 28px rgba(16,24,40,.08);
  --shadow-2: 0 18px 40px rgba(16,24,40,.14);
}
[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 10% 0%, #f3f6ff 0%, #ffffff 40%, #ffffff 100%);
}
.block-container{ padding-top: var(--s-5); max-width: 1100px; }
[data-testid="stHeader"]{ display:none; }
#MainMenu{ visibility:hidden; }
footer{ visibility:hidden; }
.card{
  background: var(--surface-1);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-1);
  border-radius: var(--r-lg);
  padding: var(--s-3);
}
.card-title{ font-weight: 800; font-size: 14px; color: var(--text); }
.muted{ color: var(--muted); font-size: 12px; }
.hero{
  display:flex;
  align-items:center;
  gap:16px;
}
.hero-title{ font-size:36px; font-weight:900; letter-spacing:-.6px; }
.hero-sub{ font-size:14px; color: var(--muted); margin-top:4px; }
.cta-card{ transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1); }
.cta-card:hover{ transform: translateY(-2px); box-shadow: var(--shadow-2); }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="card">
  <div class="hero">
    <div style="width:54px;height:54px;border-radius:16px;background:rgba(255,255,255,.9);display:flex;align-items:center;justify-content:center;border:1px solid rgba(16,24,40,.08);box-shadow:0 10px 22px rgba(16,24,40,.12);">🌱</div>
    <div>
      <div class="hero-title">EcoFlavor AI</div>
      <div class="hero-sub">每一克食材，都不该被辜负。</div>
    </div>
  </div>
  <div class="muted" style="margin-top:10px;">
    你好！我是你的智能冰箱管家。我不只是记录库存，我还能看见食材的“生命值”，并在你疲惫时替你做决定。
  </div>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3, gap="medium")
with col1:
    st.markdown('<div class="card cta-card">', unsafe_allow_html=True)
    st.markdown("**刚买完菜？**")
    st.page_link("pages/3_📷_上传入库.py", label="📷 拍照识别", icon="✨")
    st.markdown("</div>", unsafe_allow_html=True)
with col2:
    st.markdown('<div class="card cta-card">', unsafe_allow_html=True)
    st.markdown("**不知道吃啥？**")
    st.page_link("pages/4_🍽️_菜单.py", label="🆘 AI 帮我想菜单", icon="🍳")
    st.markdown("</div>", unsafe_allow_html=True)
with col3:
    st.markdown('<div class="card cta-card">', unsafe_allow_html=True)
    st.markdown("**准备补货？**")
    st.page_link("pages/5_🧾_购物清单.py", label="🧾 查看缺口", icon="🛒")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: #111827;
            color: white;
            border-radius: 999px;
            height: 3em;
            width: 100%;
            border: none;
        }
        div.stButton > button:hover {
            background-color: #0f172a;
            color: #ecf0f1;
            border: 1px solid white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("😫 我累了 SOS (一键生成今日晚餐)"):
        st.switch_page("pages/4_🍽️_菜单.py")
