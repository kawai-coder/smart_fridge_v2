from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from lib import api, db

st.set_page_config(page_title="购物清单", page_icon="🧾", layout="wide")


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
.pill{
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,.72);
  border: 1px solid rgba(16,24,40,.10);
  font-size: 12px;
  color: rgba(17,24,39,.72);
}
div.stButton > button[kind="primary"]{
  border-radius: 999px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

md_html(
    """
<div style="display:flex;align-items:center;gap:10px;">
  <div style="font-size:34px;font-weight:900;letter-spacing:-.6px;">🧾 购物清单</div>
  <div class="pill">自动补货</div>
</div>
<div class="muted" style="margin-top:4px;">基于菜单缺口自动生成补货清单，可勾选已采购项并导出 CSV。</div>
"""
)

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
        if "reason" not in df.columns:
            df["reason"] = ""

        def _urgency_rank(reason: str) -> int:
            if "紧急" in reason:
                return 0
            if "临期" in reason:
                return 1
            return 2

        df["urgency_rank"] = df["reason"].fillna("").apply(_urgency_rank)
        df["checked_rank"] = df["checked"].astype(int)
        df = df.sort_values(by=["checked_rank", "urgency_rank"], ascending=[True, True])

        total = len(df)
        purchased = int(df["checked"].sum())
        missing_qty = float(df["need_qty"].fillna(0).sum())

        md_html(
            f"""
            <div class="card">
              <div class="card-title">采购进度 <span class="muted">已购买 {purchased}/{total}</span></div>
              <div class="muted" style="margin-bottom:8px;">预计缺口总量：<b>{missing_qty:g}</b></div>
            </div>
            """
        )
        st.progress(purchased / total if total else 0)

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

        b1, b2, b3 = st.columns([1.2, 1.2, 1], gap="small")
        if b1.button("全部标记已购买"):
            for item_id in df["id"].tolist():
                api.update_shopping_item_checked(item_id, True)
            st.success("已全部标记为已购买")
            st.rerun()
        if b2.button("全部取消"):
            for item_id in df["id"].tolist():
                api.update_shopping_item_checked(item_id, False)
            st.success("已全部取消")
            st.rerun()
        if b3.button("保存勾选状态", type="primary"):
            for _, row in edited.iterrows():
                api.update_shopping_item_checked(row["item_id"], bool(row["已购买"]))
            st.success("已更新购物清单状态")

        export_df = edited.copy()
        export_df["exported_at"] = pd.Timestamp.now().isoformat(timespec="seconds")
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button("导出 CSV", csv_data, file_name="shopping_list.csv", type="primary")
    else:
        st.info("该菜单没有缺口食材，购物清单为空。")
else:
    st.info("请先生成菜单，再查看购物清单。")
