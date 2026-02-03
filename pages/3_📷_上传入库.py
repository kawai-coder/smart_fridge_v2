from __future__ import annotations

import textwrap
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

from lib import api


def md_html(html: str) -> None:
    """Render HTML with Streamlit markdown (dedent to avoid code blocks)."""
    st.markdown(textwrap.dedent(html).strip("\n"), unsafe_allow_html=True)


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="上传入库", page_icon="📷", layout="wide")

# ----------------------------
# Design system (match Dashboard)
# ----------------------------
st.markdown(
    """
<style>
:root{
  /* spacing scale */
  --s-1: 8px;
  --s-2: 12px;
  --s-3: 16px;
  --s-4: 24px;
  --s-5: 32px;

  /* radius scale */
  --r-lg: 18px;
  --r-md: 14px;
  --r-sm: 10px;

  /* surfaces & borders */
  --bg-0: #ffffff;
  --surface-1: rgba(255,255,255,.86);
  --surface-2: rgba(255,255,255,.66);
  --border: rgba(16,24,40,.08);
  --border-soft: rgba(16,24,40,.06);

  /* typography */
  --text: rgba(17,24,39,.92);
  --text-2: rgba(17,24,39,.72);
  --muted: rgba(17,24,39,.55);

  /* shadows */
  --shadow-1: 0 12px 28px rgba(16,24,40,.08);
  --shadow-2: 0 18px 40px rgba(16,24,40,.14);
}

[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 10% 0%, #f3f6ff 0%, #ffffff 40%, #ffffff 100%);
}
.block-container{
  padding-top: var(--s-5);
  padding-bottom: calc(var(--s-5) + var(--s-2));
  max-width: 1200px;
}

/* Hide Streamlit chrome */
[data-testid="stHeader"]{ display:none; }
#MainMenu{ visibility:hidden; }
footer{ visibility:hidden; }

/* Typography */
h1, h2, h3{ color: var(--text); letter-spacing: -0.2px; }
h3{ margin-top: var(--s-4); margin-bottom: var(--s-2); font-size: 18px; font-weight: 800; }

/* Card system */
.card{
  background: var(--surface-1);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-1);
  border-radius: var(--r-lg);
  padding: var(--s-3);
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1);
}
.card:hover{ transform: translateY(-2px); box-shadow: var(--shadow-2); }
.card-tight{ padding: var(--s-2); }

.card-title{
  font-weight: 900;
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
  color: var(--text-2);
}
.chip-dot{
  width:8px;
  height:8px;
  border-radius:999px;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34,197,94,.15);
}
.chip-warn .chip-dot{
  background:#f59e0b;
  box-shadow: 0 0 0 3px rgba(245,158,11,.18);
}
.badge{
  font-size:12px;
  padding: 2px 10px;
  border-radius:999px;
  border: 1px solid rgba(16,24,40,.10);
  background: rgba(255,255,255,.65);
}
.badge.red{ border-color: rgba(239,68,68,.35); background: rgba(239,68,68,.10); color:#b91c1c; }
.badge.yellow{ border-color: rgba(245,158,11,.35); background: rgba(245,158,11,.12); color:#92400e; }
.badge.green{ border-color: rgba(34,197,94,.35); background: rgba(34,197,94,.12); color:#166534; }

/* Subtle divider */
.hr{
  height:1px;
  background: rgba(16,24,40,.08);
  margin: 12px 0;
}

/* Make file uploader feel more "product" */
[data-testid="stFileUploaderDropzone"]{
  border-radius: var(--r-lg);
  border: 1px dashed rgba(16,24,40,.18);
  background: rgba(255,255,255,.70);
}
[data-testid="stFileUploaderDropzone"] > div{
  padding: 18px 16px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# Session state
# ----------------------------
if "last_image_id" not in st.session_state:
    st.session_state.last_image_id = None
if "last_detections" not in st.session_state:
    st.session_state.last_detections = []
if "last_meta" not in st.session_state:
    st.session_state.last_meta = {}
if "last_preview_bytes" not in st.session_state:
    st.session_state.last_preview_bytes = None
if "last_preview_name" not in st.session_state:
    st.session_state.last_preview_name = None


# ----------------------------
# Helpers
# ----------------------------
def _provider_status(provider_id: str) -> Tuple[bool, str]:
    """Best-effort provider availability check."""
    try:
        from lib.vision_provider import list_providers  # lazy import

        p = list_providers().get(provider_id)
        if not p:
            return False, "未注册"
        ok, reason = p.is_available()
        return ok, (reason or "可用")
    except Exception as exc:  # noqa: BLE001
        return False, f"不可用：{exc}"


def _meta_line(meta: Dict[str, Any]) -> str:
    if not meta:
        return ""
    return (
        f"requested={meta.get('provider_requested')}  "
        f"used={meta.get('provider_used')}  "
        f"degraded={meta.get('degraded')}  "
        f"reason={meta.get('reason') or '-'}"
    )


def _summary_from_detections(dets: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not dets:
        return {"count": 0, "total_qty": 0.0, "earliest": None}
    total_qty = 0.0
    earliest = None
    for d in dets:
        try:
            total_qty += float(d.get("quantity", 0) or 0)
        except Exception:
            pass
        ed = d.get("suggest_expire_date") or d.get("expire_date")
        if ed:
            if earliest is None or str(ed) < str(earliest):
                earliest = ed
    return {"count": len(dets), "total_qty": round(total_qty, 1), "earliest": earliest}


def _reset_workflow() -> None:
    st.session_state.last_image_id = None
    st.session_state.last_detections = []
    st.session_state.last_meta = {}
    st.session_state.last_preview_bytes = None
    st.session_state.last_preview_name = None


# ----------------------------
# Header
# ----------------------------
h1, h2 = st.columns([3, 2], vertical_alignment="center")
with h1:
    md_html(
        """
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="font-size:34px;font-weight:900;letter-spacing:-.6px;">上传照片入库</div>
          <div class="chip"><span class="chip-dot"></span>Live</div>
        </div>
        <div class="muted" style="margin-top:4px;">
          上传冰箱照片 → 自动识别食材 → 你确认/修改 → 一键批量入库。
        </div>
        """
    )
with h2:
    a, b = st.columns(2)
    with a:
        st.page_link("pages/2_📦_库存.py", label="📦 库存", icon="📦")
    with b:
        st.page_link("pages/4_🍽️_菜单.py", label="🍽️ 生成菜单", icon="🍽️")


# ----------------------------
# Top controls
# ----------------------------
top_left, top_right = st.columns([2.2, 1], gap="large")

with top_left:
    md_html('<div class="card"><div class="card-title">⚙️ 识别配置 <span class="muted">选择识别引擎与输入方式</span></div>')
    provider = st.selectbox(
        "识别引擎",
        ["mock", "hf_owlvit", "http"],
        index=0,
        key="vision_provider",
        help="mock 离线演示；hf_owlvit 本地模型（需 transformers + PIL）；http 需配置 VISION_HTTP_ENDPOINT。",
    )
    ok, reason = _provider_status(provider)
    dot = (
        '<span class="chip-dot"></span>'
        if ok
        else '<span class="chip-dot" style="background:#f59e0b;box-shadow:0 0 0 3px rgba(245,158,11,.18);"></span>'
    )
    chip_cls = "chip" if ok else "chip chip-warn"
    md_html(
        f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">
          <div class="{chip_cls}">{dot} 引擎状态：{('可用' if ok else '不可用')}</div>
          <div class="chip">说明：{reason}</div>
        </div>
        <div class="hr"></div>
        </div>
        """
    )

with top_right:
    md_html('<div class="card"><div class="card-title">🧭 操作指引 <span class="muted">三步完成入库</span></div>')
    step_done_1 = bool(st.session_state.last_preview_bytes)
    step_done_2 = bool(st.session_state.last_detections)

    def _badge(done: bool, text: str) -> str:
        cls = "badge green" if done else "badge"
        return f'<span class="{cls}">{text}</span>'

    md_html(
        f"""
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="font-weight:800;color:rgba(17,24,39,.92);">1) 上传/选择示例</div>
            {_badge(step_done_1, '已完成' if step_done_1 else '待完成')}
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="font-weight:800;color:rgba(17,24,39,.92);">2) 开始识别</div>
            {_badge(step_done_2, '已完成' if step_done_2 else '待完成')}
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="font-weight:800;color:rgba(17,24,39,.92);">3) 修改并确认入库</div>
            <span class="badge">待完成</span>
          </div>
        </div>
        <div class="hr"></div>
        <div class="muted">常见坑：如果本地模型/HTTP 不可用，会自动降级到 mock 以保证流程可演示。</div>
        </div>
        """
    )


# ----------------------------
# Upload & Demo area
# ----------------------------
main_left, main_right = st.columns([2.2, 1], gap="large")

with main_left:
    md_html('<div class="card"><div class="card-title">📤 上传图片 <span class="muted">支持 PNG / JPG / JPEG</span></div>')
    uploaded = st.file_uploader("上传冰箱照片", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

    btn1, btn2, btn3 = st.columns([1.1, 1.1, 1], gap="small")
    use_demo = btn1.button("使用示例图片")
    random_demo = btn2.button("生成随机示例检测结果")
    reset = btn3.button("重置")

    if reset:
        _reset_workflow()
        st.toast("已重置当前流程", icon="🧹")

    demo_dir = Path(__file__).resolve().parents[1] / "assets" / "demo_images"
    demo_images = list(demo_dir.glob("*.*")) if demo_dir.exists() else []

    # Upload flow
    if uploaded is not None:
        st.session_state.last_preview_bytes = uploaded.getvalue()
        st.session_state.last_preview_name = uploaded.name
        upload_result = api.upload_image(uploaded)
        st.session_state.last_image_id = upload_result["image_id"]

    # Demo image flow
    if use_demo:
        if demo_images:
            demo_path = demo_images[0]
            st.session_state.last_preview_bytes = demo_path.read_bytes()
            st.session_state.last_preview_name = demo_path.name

            buf = BytesIO(st.session_state.last_preview_bytes)
            buf.name = demo_path.name
            upload_result = api.upload_image(buf)
            st.session_state.last_image_id = upload_result["image_id"]

            st.toast("已加载示例图片", icon="🧪")
        else:
            st.warning("未找到示例图片，可直接上传或使用随机检测结果。")

    # Random detections (no real image)
    if random_demo:
        result = api.detect("demo_random", provider="mock")
        st.session_state.last_image_id = "demo_random"
        st.session_state.last_detections = result["detections"]
        st.session_state.last_meta = result.get("meta", {})
        st.toast("已生成随机示例检测结果", icon="🎲")

    # Preview
    if st.session_state.last_preview_bytes:
        st.image(
            st.session_state.last_preview_bytes,
            caption=st.session_state.last_preview_name or "预览",
            use_column_width=True,
        )

        start_detect = st.button("✨ 开始识别", type="primary")
        if start_detect:
            with st.spinner("识别中…"):
                result = api.detect(st.session_state.last_image_id, provider=provider)
            st.session_state.last_detections = result["detections"]
            st.session_state.last_meta = result.get("meta", {})
            if st.session_state.last_meta.get("degraded"):
                st.warning(
                    f"已降级为 {st.session_state.last_meta.get('provider_used')}：{st.session_state.last_meta.get('reason')}"
                )
            st.success("识别完成，可下方编辑确认入库。")

        if st.session_state.last_meta:
            st.caption(_meta_line(st.session_state.last_meta))

    else:
        md_html(
            """
            <div class="muted" style="margin-top:6px;">
              你可以拖拽一张冰箱照片到上方区域；或点击“使用示例图片/随机示例”快速演示。
            </div>
            """
        )

    md_html("</div>")

    # Detection results editor
    if st.session_state.last_detections:
        md_html(
            '<div class="card" style="margin-top:16px;"><div class="card-title">🧾 识别结果（可编辑） <span class="muted">修改后再确认入库</span></div>'
        )
        det_df = pd.DataFrame(st.session_state.last_detections)

        keep_cols = [
            "item_id",
            "item_name",
            "confidence",
            "quantity",
            "unit",
            "suggest_expire_date",
            "location",
        ]
        for col in keep_cols:
            if col not in det_df.columns:
                det_df[col] = None

        display_df = det_df[keep_cols].copy()
        display_df.rename(
            columns={
                "item_id": "item_id",
                "item_name": "食材",
                "confidence": "置信度",
                "quantity": "数量",
                "unit": "单位",
                "suggest_expire_date": "到期日",
                "location": "位置",
            },
            inplace=True,
        )

        try:
            display_df["置信度"] = display_df["置信度"].apply(
                lambda x: round(float(x), 2) if x is not None else None
            )
        except Exception:
            pass

        edited_df = st.data_editor(
            display_df,
            num_rows="dynamic",
            disabled=["item_id", "置信度"],
        )
        md_html("</div>")

with main_right:
    md_html('<div class="card"><div class="card-title">📌 入库摘要 <span class="muted">确认前最后检查</span></div>')
    summ = _summary_from_detections(st.session_state.last_detections)
    md_html(
        f"""
        <div style="display:grid;gap:10px;">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div class="muted">识别条目</div>
            <div style="font-weight:900;font-size:18px;color:rgba(17,24,39,.92);">{summ['count']}</div>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div class="muted">数量合计（估算）</div>
            <div style="font-weight:900;font-size:18px;color:rgba(17,24,39,.92);">{summ['total_qty']}</div>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div class="muted">最早到期</div>
            <div style="font-weight:800;color:rgba(17,24,39,.92);">{summ['earliest'] or '-'}</div>
          </div>
        </div>
        <div class="hr"></div>
        """
    )

    confirm_disabled = not bool(st.session_state.last_detections)
    confirm = st.button(
        "✅ 确认入库", type="primary", disabled=confirm_disabled
    )
    if confirm:
        batches: List[Dict[str, Any]] = []
        for _, row in edited_df.iterrows():
            batches.append(
                {
                    "item_id": row.get("item_id"),
                    "item_name": row.get("食材"),
                    "quantity": row.get("数量"),
                    "unit": row.get("单位"),
                    "expire_date": row.get("到期日"),
                    "location": row.get("位置"),
                }
            )
        api.bulk_create_batches(
            source={"type": "image", "image_id": st.session_state.last_image_id},
            batches=batches,
        )
        st.success("已成功入库！")
        st.toast("库存已更新", icon="📦")
        st.page_link("pages/2_📦_库存.py", label="前往库存查看", icon="📦")
        _reset_workflow()

    md_html(
        """
        <div style="margin-top:10px;" class="muted">
          入库会创建批次（batch）并写入事件流（event）用于后续追溯。
        </div>
        </div>
        """
    )

# Bottom hint
if not st.session_state.last_preview_bytes and not st.session_state.last_detections:
    st.info("上传图片后点击“开始识别”，或使用示例检测结果进行演示。")
