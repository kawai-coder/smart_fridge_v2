from __future__ import annotations

import textwrap

import streamlit as st

from lib import api, db

st.set_page_config(page_title="菜单", page_icon="🍽️", layout="wide")


def md_html(html: str) -> None:
    st.markdown(textwrap.dedent(html).strip("\n"), unsafe_allow_html=True)


st.markdown(
    """
<style>
:root{
  --s-1: 8px; --s-2: 12px; --s-3: 16px; --s-4: 24px; --s-5: 32px;
  --r-lg: 18px; --r-md: 14px; --r-sm: 10px;
  --surface-1: rgba(255,255,255,.86);
  --surface-2: rgba(255,255,255,.66);
  --border: rgba(16,24,40,.08);
  --text: rgba(17,24,39,.92);
  --muted: rgba(17,24,39,.55);
  --shadow-1: 0 12px 28px rgba(16,24,40,.08);
  --shadow-2: 0 18px 40px rgba(16,24,40,.14);
}
[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 10% 0%, #f3f6ff 0%, #ffffff 40%, #ffffff 100%);
}
.block-container{ padding-top: var(--s-5); max-width: 1200px; }
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
.card + .card{ margin-top: var(--s-3); }
.card-title{
  font-weight: 800;
  font-size: 14px;
  color: var(--text);
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom: var(--s-2);
}
.muted{ color: var(--muted); font-size: 12px; }
.chip{
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(16,24,40,.10);
  background: rgba(255,255,255,.72);
  font-size: 12px;
  color: rgba(17,24,39,.72);
}
.meal-card{
  border: 1px solid var(--border);
  background: var(--surface-2);
  border-radius: var(--r-lg);
  padding: var(--s-3);
  margin-bottom: var(--s-2);
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1);
}
.meal-card:hover{ transform: translateY(-1px); box-shadow: var(--shadow-2); }
.meal-header{ display:flex; justify-content:space-between; gap:10px; align-items:center; }
.meal-title{ font-weight:800; font-size: 15px; color: var(--text); }
.meal-meta{ font-size:12px; color: var(--muted); margin-top:4px; }
.chips{ display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
details{
  border-top:1px dashed rgba(16,24,40,.12);
  margin-top:10px;
  padding-top:8px;
}
summary{
  cursor:pointer;
  font-weight:700;
  color: var(--text);
}
.skeleton{
  height: 14px;
  background: linear-gradient(90deg, rgba(16,24,40,.06), rgba(16,24,40,.12), rgba(16,24,40,.06));
  border-radius: 999px;
  animation: shimmer 1.2s infinite;
}
.skeleton-line{ width:100%; margin-bottom:8px; }
@keyframes shimmer{
  0%{ background-position: -200px 0; }
  100%{ background-position: 200px 0; }
}
</style>
""",
    unsafe_allow_html=True,
)

md_html(
    """
<div style="display:flex;align-items:center;gap:10px;">
  <div style="font-size:34px;font-weight:900;letter-spacing:-.6px;">🍽️ 菜单生成</div>
  <div class="chip">智能规划</div>
</div>
<div class="muted" style="margin-top:4px;">基于当前库存与临期批次，快速生成可执行的菜单计划。</div>
"""
)

if "last_menu_id" not in st.session_state:
    st.session_state.last_menu_id = None

with st.sidebar:
    md_html('<div class="card"><div class="card-title">计划规模</div>')
    days = st.selectbox("计划天数", options=[1, 3, 7], index=0)
    servings = st.slider("份数", min_value=1, max_value=6, value=2)
    md_html("</div>")

    md_html('<div class="card"><div class="card-title">饮食偏好</div>')
    prefer_expiring = st.toggle("优先消耗临期", value=True)
    diet = st.selectbox("饮食偏好", options=["balanced", "high_protein", "low_fat"], index=0)
    allergens = st.multiselect("排除过敏原", options=["egg", "dairy", "nuts"])
    md_html("</div>")

    md_html('<div class="card"><div class="card-title">Planner Provider</div>')
    planner = st.selectbox(
        "菜单生成方式",
        options=["greedy", "http", "local"],
        index=0,
        help="http 需配置 PLANNER_HTTP_ENDPOINT",
    )
    md_html("</div>")

constraints = {
    "prefer_expiring": prefer_expiring,
    "diet": diet,
    "allergens_exclude": allergens,
}

placeholder = st.empty()
if st.button("生成菜单", type="primary"):
    with placeholder.container():
        md_html(
            """
            <div class="card">
              <div class="card-title">正在生成菜单...</div>
              <div class="skeleton skeleton-line"></div>
              <div class="skeleton skeleton-line" style="width:80%;"></div>
              <div class="skeleton skeleton-line" style="width:60%;"></div>
            </div>
            """
        )
    with st.spinner("正在生成菜单..."):
        result = api.generate_menu(days, servings, constraints, planner=planner)
    st.session_state.last_menu_id = result["menu_id"]
    meta = result.get("meta", {})
    if meta.get("degraded"):
        st.warning(f"已降级为 {meta.get('planner_used')}：{meta.get('reason')}")
    st.success("已生成菜单，可下滑查看详情。")

md_html('<div id="menu-results"></div>')
if st.session_state.last_menu_id:
    menu = api.get_menu(st.session_state.last_menu_id)
    recipes = {r["recipe_id"]: r for r in db.list_recipes()}
    st.markdown("### 菜单计划")
    for item in menu.get("items", []):
        recipe = recipes.get(item["recipe_id"], {"name": "未知菜谱"})
        reasons = item.get("explain", []) or []
        chips = "".join([f"<span class='chip'>{reason}</span>" for reason in reasons])
        nutrition = item.get("nutrition") or {}
        nutrition_html = (
            f"<pre>{nutrition}</pre>" if nutrition else "<div class='muted'>未提供营养信息（MVP）</div>"
        )
        md_html(
            f"""
            <div class="meal-card">
              <div class="meal-header">
                <div>
                  <div class="meal-title">{item['date']} · {item['meal_type']} · {recipe['name']}</div>
                  <div class="meal-meta">建议优先消耗临期食材</div>
                </div>
                <div class="chip">推荐</div>
              </div>
              <div class="chips">{chips}</div>
              <details>
                <summary>查看营养信息</summary>
                {nutrition_html}
              </details>
            </div>
            """
        )

    st.page_link("pages/5_🧾_购物清单.py", label="生成/查看购物清单", icon="🧾")
    st.markdown(
        """
        <script>
          const el = document.getElementById("menu-results");
          if (el) { el.scrollIntoView({ behavior: "smooth", block: "start" }); }
        </script>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("点击“生成菜单”即可看到推荐结果。")
