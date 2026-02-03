from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from lib import api


# =========================
# Page config
# =========================
st.set_page_config(page_title="库存", page_icon="📦", layout="wide")

# =========================
# Styling (Apple-ish: grid / rounded / shadow / spacing)
# =========================
st.markdown(
    """
<style>
:root{
  --bg1:#f7f7f8;
  --bg2:#eef0f3;
  --card: rgba(255,255,255,0.78);
  --card2: rgba(255,255,255,0.92);
  --stroke: rgba(15,23,42,0.12);
  --text: rgba(15,23,42,0.92);
  --muted: rgba(15,23,42,0.62);
  --shadow: 0 12px 36px rgba(15,23,42,0.10);
  --shadow2: 0 10px 24px rgba(15,23,42,0.10);
  --radius: 22px;
}

.stApp{
  background: radial-gradient(1100px 560px at 15% 10%, rgba(99,102,241,0.10), transparent 60%),
              radial-gradient(900px 520px at 85% 15%, rgba(56,189,248,0.08), transparent 60%),
              linear-gradient(180deg, var(--bg1), var(--bg2));
  color: var(--text);
}

.block-container{
  padding-top: 1.2rem;
  padding-bottom: 3.2rem;
  max-width: 1200px;
}

h1, h2, h3 { letter-spacing: -0.02em; }

header[data-testid="stHeader"]{ background: transparent; }
div[data-testid="stToolbar"]{ visibility: hidden; height: 0px; }
footer{ visibility: hidden; }

/* --- Hero --- */
.hero{
  border: 1px solid var(--stroke);
  background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(255,255,255,0.78));
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 18px 18px 16px 18px;
  position: relative;
  overflow: hidden;
}
.hero:before{
  content:"";
  position:absolute;
  inset:-80px -80px auto auto;
  width:260px; height:260px;
  background: radial-gradient(circle at 30% 30%, rgba(99,102,241,0.10), transparent 62%);
  transform: rotate(12deg);
}
.hero-title{
  display:flex;
  align-items:center;
  gap:14px;
}
.hero-kicker{
  color: var(--muted);
  font-size: 0.95rem;
  margin-top: 2px;
}
.hero-chip{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.78);
  color: var(--muted);
  font-size: 0.85rem;
}

/* --- Fridge layout --- */
.fridge{
  border-radius: calc(var(--radius) + 6px);
  border: 1px solid var(--stroke);
  background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(255,255,255,0.70));
  box-shadow: var(--shadow);
  overflow: hidden;
}
.fridge-head{
  padding: 14px 16px;
  display:flex;
  align-items:center;
  justify-content: space-between;
  gap: 10px;
  border-bottom: 1px solid rgba(15,23,42,0.08);
}
.fridge-title{
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.fridge-sub{
  color: var(--muted);
  font-size: 0.88rem;
}
.shelf{
  padding: 14px 14px 6px 14px;
}
.shelf + .shelf{
  border-top: 1px dashed rgba(15,23,42,0.10);
}
.shelf-header{
  display:flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}
.shelf-name{
  font-weight: 700;
  font-size: 0.98rem;
}
.shelf-count{
  color: var(--muted);
  font-size: 0.86rem;
}

/* --- Cards --- */
.inv-card{
  border: 1px solid rgba(15,23,42,0.10);
  background: rgba(255,255,255,0.84);
  border-radius: 18px;
  box-shadow: var(--shadow2);
  padding: 12px 12px 10px 12px;
  transition: transform .12s ease, background .12s ease, border-color .12s ease;
  height: 100%;
}
.inv-card:hover{
  transform: translateY(-2px);
  background: rgba(255,255,255,0.95);
  border-color: rgba(15,23,42,0.16);
}
.inv-top{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:10px;
  margin-bottom: 8px;
}
.inv-name{
  font-weight: 750;
  font-size: 0.98rem;
  line-height: 1.15;
}
.inv-meta{
  color: var(--muted);
  font-size: 0.86rem;
  margin-top: 2px;
}
.badge{
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 0.80rem;
  border: 1px solid rgba(15,23,42,0.12);
  background: rgba(15,23,42,0.04);
  color: rgba(15,23,42,0.74);
  white-space: nowrap;
}
.badge-ok{ background: rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.26); }
.badge-soon{ background: rgba(245,158,11,0.12); border-color: rgba(245,158,11,0.26); }
.badge-exp{ background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.26); }
.badge-unk{ background: rgba(148,163,184,0.12); border-color: rgba(148,163,184,0.22); }

.inv-bottom{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  margin-top: 10px;
}
.inv-qty{
  font-size: 0.92rem;
  font-weight: 650;
}
.small-muted{ color: var(--muted); font-size: 0.84rem; }

/* --- Detail panel --- */
.panel{
  border: 1px solid var(--stroke);
  background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(255,255,255,0.74));
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 14px 14px 12px 14px;
}
.panel-title{
  font-weight: 800;
  font-size: 1.0rem;
  margin-bottom: 6px;
}
.panel-sub{
  color: var(--muted);
  font-size: 0.88rem;
  margin-bottom: 10px;
}
hr.soft{
  border: none;
  height: 1px;
  background: rgba(15,23,42,0.10);
  margin: 12px 0;
}

/* Buttons: pill */
div.stButton > button{
  border-radius: 999px !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  background: rgba(255,255,255,0.86) !important;
  color: rgba(15,23,42,0.92) !important;
  padding: 0.55rem 0.9rem !important;
  transition: transform .12s ease, background .12s ease;
}
div.stButton > button:hover{
  background: rgba(255,255,255,0.96) !important;
  transform: translateY(-1px);
}
div.stButton > button[kind="primary"]{
  background: rgba(15,23,42,0.88) !important;
  border-color: rgba(15,23,42,0.88) !important;
  color: rgba(255,255,255,0.96) !important;
}
div.stButton > button[kind="primary"]:hover{
  background: rgba(15,23,42,0.95) !important;
}

/* Inputs */
div[data-baseweb="input"] input,
div[data-baseweb="select"] input{
  border-radius: 14px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Helpers
# =========================
LOCATION_LABELS = {
    "freezer": "冷冻层",
    "fridge": "冷藏层",
    "pantry": "常温层",
}

STATUS_LABELS = {
    "in_stock": "在库",
    "consumed": "已消耗",
    "discarded": "已丢弃",
}

LOCATION_ICONS = {"freezer": "🧊", "fridge": "❄️", "pantry": "🥫"}
SOURCE_LABELS = {"manual": "手动", "vision": "识别", "recipe": "菜单", "import": "导入"}


def _days_left(expire_date: Any) -> Optional[int]:
    if not expire_date or pd.isna(expire_date):
        return None
    try:
        d = date.fromisoformat(str(expire_date))
        return (d - date.today()).days
    except Exception:
        return None


def _freshness_badge(days_left: Optional[int]) -> Tuple[str, str]:
    if days_left is None:
        return ("未知", "badge badge-unk")
    if days_left < 0:
        return (f"已过期 {abs(days_left)}天", "badge badge-exp")
    if days_left <= 3:
        return (f"临期 {days_left}天", "badge badge-soon")
    return (f"新鲜 {days_left}天", "badge badge-ok")


def _sort_key(batch: Dict[str, Any]) -> Tuple[int, int]:
    dl = _days_left(batch.get("expire_date"))
    if dl is None:
        return (10_000, 0)
    return (max(-9999, dl), 0)


def _render_badge(text: str, css_class: str) -> str:
    return f'<span class="{css_class}">⏳ {text}</span>'


# =========================
# State
# =========================
if "selected_batch" not in st.session_state:
    st.session_state.selected_batch = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "冰箱视图"


# =========================
# Hero header
# =========================
st.markdown(
    """
<div class="hero">
  <div class="hero-title">
    <div style="width:44px;height:44px;border-radius:14px;background:rgba(255,255,255,0.92);display:flex;align-items:center;justify-content:center;border:1px solid rgba(15,23,42,0.10);box-shadow:0 10px 26px rgba(15,23,42,0.10);">
      <span style="font-size:22px;">📦</span>
    </div>
    <div>
      <div style="font-size:1.5rem;font-weight:850;line-height:1.05;">库存</div>
      <div class="hero-kicker">像放进冰箱一样浏览你的食材批次：卡片分层、临期提示、详情抽屉。</div>
    </div>
  </div>
  <div style="margin-top:10px;display:flex;gap:10px;flex-wrap:wrap;">
    <span class="hero-chip">🧊 冷冻 / ❄️ 冷藏 / 🥫 常温 分区</span>
    <span class="hero-chip">⏳ 临期优先</span>
    <span class="hero-chip">🗂️ 一键切回表格精细编辑</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# =========================
# Filters + view switch
# =========================
with st.sidebar:
    st.markdown("### 视图与筛选")
    st.session_state.view_mode = st.radio(
        "视图",
        options=["冰箱视图", "表格视图"],
        index=0 if st.session_state.view_mode == "冰箱视图" else 1,
        label_visibility="collapsed",
    )

    location = st.selectbox("位置", options=["", "fridge", "freezer", "pantry"], index=0)
    status = st.selectbox("状态", options=["", "in_stock", "consumed", "discarded"], index=0)
    keyword = st.text_input("搜索关键词", placeholder="比如：牛奶 / 鸡蛋 / 西红柿…")

    st.markdown("---")
    st.caption("提示：在「冰箱视图」点卡片的“查看详情”，右侧会出现可操作面板。")

filters = {"location": location or None, "status": status or None, "keyword": keyword or None}
response = api.list_batches(filters)
batches: List[Dict[str, Any]] = response.get("batches", []) or []

if not batches:
    st.info("没有找到匹配的批次，先去上传识别或调整筛选条件。")
    st.stop()

# =========================
# Prepare dataframe once
# =========================
df = pd.DataFrame(batches)

# quick metrics
in_stock = df[df["status"] == "in_stock"]
expiring_soon = 0
expired = 0
unknown = 0
for _, r in in_stock.iterrows():
    dl = _days_left(r.get("expire_date"))
    if dl is None:
        unknown += 1
    elif dl < 0:
        expired += 1
    elif dl <= 3:
        expiring_soon += 1

m1, m2, m3, m4 = st.columns(4)
m1.metric("在库批次", int(in_stock.shape[0]))
m2.metric("临期(≤3天)", int(expiring_soon))
m3.metric("已过期", int(expired))
m4.metric("到期未知", int(unknown))

st.write("")

# =========================
# Layout: main + detail panel (like a drawer)
# =========================
main_col, detail_col = st.columns([3.2, 2.0], gap="large")

# =========================
# Icebox / Cards view
# =========================
with main_col:
    if st.session_state.view_mode == "冰箱视图":
        st.markdown(
            """
<div class="fridge">
  <div class="fridge-head">
    <div>
      <div class="fridge-title">你的冰箱</div>
      <div class="fridge-sub">按分区展示批次；临期优先排在前面。</div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        groups: Dict[str, List[Dict[str, Any]]] = {"freezer": [], "fridge": [], "pantry": [], "unknown": []}
        for b in batches:
            loc = b.get("location") or "unknown"
            if loc not in groups:
                loc = "unknown"
            groups[loc].append(b)

        for k in groups:
            groups[k].sort(key=_sort_key)

        def shelf_section(loc_key: str, title: str, items: List[Dict[str, Any]]):
            st.markdown(
                f"""
<div class="fridge">
  <div class="shelf">
    <div class="shelf-header">
      <div class="shelf-name">{LOCATION_ICONS.get(loc_key,"🧺")} {title}</div>
      <div class="shelf-count">{len(items)} 个批次</div>
    </div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
            if not items:
                st.caption("这里暂时空着。")
                st.write("")
                return

            cols = st.columns(3, gap="medium")
            for idx, b in enumerate(items):
                c = cols[idx % 3]
                with c:
                    dl = _days_left(b.get("expire_date"))
                    badge_text, badge_cls = _freshness_badge(dl)
                    badge_html = _render_badge(badge_text, badge_cls)
                    name = b.get("item_name_snapshot") or "未命名食材"
                    qty = b.get("quantity")
                    unit = b.get("unit") or ""
                    status_label = STATUS_LABELS.get(b.get("status"), b.get("status") or "-")
                    source_label = SOURCE_LABELS.get(b.get("source_type"), b.get("source_type") or "-")
                    expire = b.get("expire_date") or "—"

                    st.markdown(
                        f"""
<div class="inv-card">
  <div class="inv-top">
    <div style="min-width:0;">
      <div class="inv-name">{name}</div>
      <div class="inv-meta">{status_label} · 来源 {source_label}</div>
    </div>
    <div>{badge_html}</div>
  </div>

  <div class="inv-bottom">
    <div>
      <div class="inv-qty">{float(qty):g} {unit}</div>
      <div class="small-muted">到期日：{expire}</div>
    </div>
    <div class="small-muted">#{b.get("batch_id")}</div>
  </div>
</div>
""",
                        unsafe_allow_html=True,
                    )

                    if st.button("查看详情", key=f"open_{b.get('batch_id')}", use_container_width=True):
                        st.session_state.selected_batch = b.get("batch_id")

            st.write("")

        shelf_section("fridge", "冷藏层", groups["fridge"])
        shelf_section("freezer", "冷冻层", groups["freezer"])
        shelf_section("pantry", "常温层", groups["pantry"])
        shelf_section("unknown", "未归类", groups["unknown"])

    else:
        st.markdown(
            """
<div class="panel">
  <div class="panel-title">批次列表（表格视图）</div>
  <div class="panel-sub">适合批量精确编辑：数量 / 到期日 / 位置。</div>
</div>
""",
            unsafe_allow_html=True,
        )

        display_df = df[
            [
                "batch_id",
                "item_name_snapshot",
                "quantity",
                "unit",
                "expire_date",
                "location",
                "status",
                "source_type",
            ]
        ].copy()
        display_df.rename(
            columns={
                "batch_id": "批次",
                "item_name_snapshot": "食材",
                "quantity": "数量",
                "unit": "单位",
                "expire_date": "到期日",
                "location": "位置",
                "status": "状态",
                "source_type": "来源",
            },
            inplace=True,
        )

        edited = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            disabled=["批次", "食材", "单位", "状态", "来源"],
        )

        if st.button("保存编辑", type="primary"):
            for _, row in edited.iterrows():
                original = df[df["batch_id"] == row["批次"]].iloc[0]
                patch: Dict[str, Any] = {}
                if row["数量"] != original["quantity"]:
                    patch["quantity"] = float(row["数量"])
                if row["到期日"] != original["expire_date"]:
                    patch["expire_date"] = row["到期日"]
                if row["位置"] != original["location"]:
                    patch["location"] = row["位置"]
                if patch:
                    api.update_batch(original["batch_id"], patch)
            st.success("已保存批次更新 ✅")

        st.write("")
        batch_ids = [b["batch_id"] for b in batches]
        options = [None] + batch_ids
        try:
            idx = 0 if st.session_state.selected_batch is None else (1 + batch_ids.index(st.session_state.selected_batch))
        except ValueError:
            idx = 0
        st.session_state.selected_batch = st.selectbox(
            "在右侧面板操作某个批次（可选）",
            options=options,
            index=idx,
            format_func=lambda x: "不选择" if x is None else str(x),
        )

# =========================
# Detail drawer panel
# =========================
with detail_col:
    st.markdown(
        """
<div class="panel">
  <div class="panel-title">详情与操作</div>
  <div class="panel-sub">选中一个批次后，可以在这里消耗 / 丢弃，并查看事件历史。</div>
</div>
""",
        unsafe_allow_html=True,
    )

    selected = st.session_state.selected_batch
    if not selected:
        st.info("在「冰箱视图」点击任意卡片的“查看详情”，或在「表格视图」里选择一个批次。")
        st.stop()

    selected_row = None
    for b in batches:
        if b.get("batch_id") == selected:
            selected_row = b
            break

    if not selected_row:
        st.warning("所选批次不在当前筛选结果中。请调整筛选条件后再试。")
        st.stop()

    name = selected_row.get("item_name_snapshot") or "未命名食材"
    qty = float(selected_row.get("quantity") or 0.0)
    unit = selected_row.get("unit") or ""
    expire = selected_row.get("expire_date")
    dl = _days_left(expire)
    badge_text, badge_cls = _freshness_badge(dl)

    st.markdown(
        f"""
<div class="panel">
  <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start;">
    <div style="min-width:0;">
      <div style="font-size:1.15rem;font-weight:850;line-height:1.1;">{name}</div>
      <div class="panel-sub">批次 #{selected} · {STATUS_LABELS.get(selected_row.get("status"), selected_row.get("status") or "-")}</div>
    </div>
    <div>{_render_badge(badge_text, badge_cls)}</div>
  </div>
  <hr class="soft"/>
  <div style="display:flex;gap:12px;flex-wrap:wrap;">
    <div class="hero-chip">数量：<b style="color:rgba(15,23,42,0.92);">{qty:g} {unit}</b></div>
    <div class="hero-chip">位置：<b style="color:rgba(15,23,42,0.92);">{LOCATION_LABELS.get(selected_row.get("location"), selected_row.get("location") or "未归类")}</b></div>
    <div class="hero-chip">到期：<b style="color:rgba(15,23,42,0.92);">{expire or "—"}</b></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("#### 快捷操作")
    op1, op2 = st.columns(2, gap="medium")

    with op1:
        consume_qty = st.number_input(
            "消耗数量",
            min_value=0.0,
            max_value=max(0.0, qty),
            step=0.5,
            help="会记录一条消耗事件（delta_quantity 为负）。",
        )
        if st.button("确认消耗", type="primary", use_container_width=True):
            api.consume_batch(selected, consume_qty, note="手动消耗（库存页）")
            st.success("已记录消耗事件 ✅")
            st.rerun()

    with op2:
        discard_qty = st.number_input(
            "丢弃数量",
            min_value=0.0,
            max_value=max(0.0, qty),
            step=0.5,
            help="会记录一条丢弃事件（delta_quantity 为负）。",
            key="discard_qty",
        )
        discard_reason = st.text_input("丢弃原因", placeholder="例如：变质 / 口感变差 / 包装破损…")
        if st.button("确认丢弃", use_container_width=True):
            api.discard_batch(selected, discard_qty, reason=discard_reason)
            st.success("已记录丢弃事件 ✅")
            st.rerun()

    st.write("")
    st.markdown("#### 事件历史")

    events = api.list_batch_events(selected).get("events", []) or []
    if events:
        ev_df = pd.DataFrame(events)
        cols = [c for c in ["event_type", "delta_quantity", "note", "created_at"] if c in ev_df.columns]
        ev_df = ev_df[cols].copy()
        ev_df.rename(
            columns={
                "event_type": "事件",
                "delta_quantity": "数量变化",
                "note": "备注",
                "created_at": "时间",
            },
            inplace=True,
        )
        st.dataframe(ev_df, use_container_width=True, hide_index=True)
    else:
        st.info("该批次暂无事件记录。")

    st.write("")
    if st.button("清除选择", use_container_width=True):
        st.session_state.selected_batch = None
        st.rerun()
