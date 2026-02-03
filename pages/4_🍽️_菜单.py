from __future__ import annotations

import streamlit as st

from lib import api, db

st.set_page_config(page_title="菜单", page_icon="🍽️", layout="wide")

st.title("🍽️ 菜单生成")
st.write("基于当前库存与临期批次，快速生成可执行的菜单计划。")

if "last_menu_id" not in st.session_state:
    st.session_state.last_menu_id = None

with st.sidebar:
    st.header("约束条件")
    days = st.selectbox("计划天数", options=[1, 3, 7], index=0)
    servings = st.slider("份数", min_value=1, max_value=6, value=2)
    prefer_expiring = st.toggle("优先消耗临期", value=True)
    diet = st.selectbox("饮食偏好", options=["balanced", "high_protein", "low_fat"], index=0)
    allergens = st.multiselect("排除过敏原", options=["egg", "dairy", "nuts"])
    planner = st.selectbox(
        "菜单生成方式",
        options=["greedy", "http", "local"],
        index=0,
        help="http 需配置 PLANNER_HTTP_ENDPOINT",
    )

constraints = {
    "prefer_expiring": prefer_expiring,
    "diet": diet,
    "allergens_exclude": allergens,
}

if st.button("生成菜单", type="primary"):
    result = api.generate_menu(days, servings, constraints, planner=planner)
    st.session_state.last_menu_id = result["menu_id"]
    meta = result.get("meta", {})
    if meta.get("degraded"):
        st.warning(f"已降级为 {meta.get('planner_used')}：{meta.get('reason')}")
    st.success("已生成菜单，可下滑查看详情。")

if st.session_state.last_menu_id:
    menu = api.get_menu(st.session_state.last_menu_id)
    recipes = {r["recipe_id"]: r for r in db.list_recipes()}
    st.markdown("### 菜单计划")
    for item in menu.get("items", []):
        recipe = recipes.get(item["recipe_id"], {"name": "未知菜谱"})
        with st.expander(f"{item['date']} · {item['meal_type']} · {recipe['name']}"):
            st.write("**推荐理由**")
            for reason in item.get("explain", []):
                st.write(f"- {reason}")
            nutrition = item.get("nutrition") or {}
            if nutrition:
                st.write("**营养信息**")
                st.json(nutrition)
            else:
                st.info("未提供营养信息（MVP）")

    st.page_link("pages/5_🧾_购物清单.py", label="生成/查看购物清单", icon="🧾")
else:
    st.info("点击“生成菜单”即可看到推荐结果。")
