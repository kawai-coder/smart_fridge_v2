from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import api, db

st.set_page_config(page_title="购物清单", page_icon="🧾", layout="wide")

st.title("🧾 购物清单")
st.write("基于菜单缺口自动生成补货清单，可勾选已采购项并导出 CSV。")

if "last_menu_id" not in st.session_state:
    st.session_state.last_menu_id = None

menu_ids = [row["menu_id"] for row in db.fetch_all("SELECT menu_id FROM menu_plans ORDER BY generated_at DESC")]
if menu_ids:
    selected_menu = st.selectbox("选择菜单计划", options=menu_ids, index=0)
else:
    selected_menu = None

if selected_menu:
    items = api.get_shopping_list(selected_menu)["items"]
    if items:
        df = pd.DataFrame(items)
        display_df = df[["id", "item_name_snapshot", "need_qty", "unit", "checked"]]
        display_df.rename(
            columns={
                "id": "item_id",
                "item_name_snapshot": "食材",
                "need_qty": "数量",
                "unit": "单位",
                "checked": "已购买",
            },
            inplace=True,
        )
        edited = st.data_editor(display_df, use_container_width=True, num_rows="dynamic")
        if st.button("保存勾选状态"):
            for _, row in edited.iterrows():
                api.update_shopping_item_checked(row["item_id"], bool(row["已购买"]))
            st.success("已更新购物清单状态")

        csv_data = edited.to_csv(index=False).encode("utf-8")
        st.download_button("导出 CSV", csv_data, file_name="shopping_list.csv")
    else:
        st.info("该菜单没有缺口食材，购物清单为空。")
else:
    st.info("请先生成菜单，再查看购物清单。")
