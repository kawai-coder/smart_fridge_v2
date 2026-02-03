from __future__ import annotations

import streamlit as st

from db.seed import seed
from lib import db 

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
st.title("🌱 EcoFlavor AI")
st.markdown("### *“每一克食材，都不该被辜负”*")

st.write(
    """
    你好！我是你的智能冰箱管家。
    我不只是记录库存，我还能看见食材的“生命值”，并在你疲惫时替你做决定。
    """
)

# 使用 Columns 布局优化入口按钮，增加 emoji 和动词
col1, col2, col3 = st.columns(3)
with col1:
    st.info("**刚买完菜？**")
    st.page_link("pages/3_📷_上传入库.py", label="📷 拍照识别", icon="✨")
with col2:
    st.warning("**不知道吃啥？**")
    st.page_link("pages/4_🍽️_菜单.py", label="🆘 AI 帮我想菜单", icon="🍳")
with col3:
    st.success("**准备补货？**")
    st.page_link("pages/5_🧾_购物清单.py", label="🧾 查看缺口", icon="🛒")

# 这里的 "SOS" 概念对应截图中底部的黑色按钮
st.divider()
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    # 模拟那个黑色的 "我累了 SOS" 按钮
    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: #2c3e50;
            color: white;
            border-radius: 20px;
            height: 3em;
            width: 100%;
            border: none;
        }
        div.stButton > button:hover {
            background-color: #34495e;
            color: #ecf0f1;
            border: 1px solid white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("😫 我累了 SOS (一键生成今日晚餐)"):
        st.switch_page("pages/4_🍽️_菜单.py")
