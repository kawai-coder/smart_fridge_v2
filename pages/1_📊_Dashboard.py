from __future__ import annotations

import pandas as pd
import streamlit as st
import json
import math
import streamlit.components.v1 as components
import random
import textwrap

from lib import api

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")


def md_html(html: str) -> None:
    """Render HTML with Streamlit markdown.

    Streamlit markdown treats lines indented by >=4 spaces as a code block.
    Many HTML snippets in Python triple-quoted strings inherit indentation,
    so we dedent to avoid being rendered as a code block (with a copy button).
    """
    st.markdown(textwrap.dedent(html).strip("\n"), unsafe_allow_html=True)
st.markdown("""
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

/* Headings rhythm (grid + spacing) */
h1, h2, h3{
  color: var(--text);
  letter-spacing: -0.2px;
}
h3{
  margin-top: var(--s-4);
  margin-bottom: var(--s-2);
  font-size: 18px;
  font-weight: 800;
}

/* Card system */
.card{
  background: var(--surface-1);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-1);
  border-radius: var(--r-lg);
  padding: var(--s-3);
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1);
}
.card:hover{
  transform: translateY(-2px);
  box-shadow: var(--shadow-2);
}
.card:active{
  transform: translateY(0px);
}
.card-tight{ padding: var(--s-2); }

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
  color: var(--text-2);
}
.chip-dot{
  width:8px;
  height:8px;
  border-radius:999px;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34,197,94,.15);
}

/* KPI */
.kpi{ display:flex; align-items:flex-end; justify-content:space-between; }
.kpi .label{ font-size:12px; color: rgba(17,24,39,.58); }
.kpi .value{ font-size:28px; font-weight:900; letter-spacing:-.6px; color: var(--text); }
.kpi .hint{ font-size:12px; color: rgba(17,24,39,.50); margin-top: 2px; }

/* List row (Top 6) */
.row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding: var(--s-2);
  border-radius: var(--r-lg);
  border: 1px solid var(--border-soft);
  background: var(--surface-2);
  margin-bottom: var(--s-1);
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1);
}
.row:hover{
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(16,24,40,.10);
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

/* Timeline */
.timeline-item{
  padding: var(--s-2);
  border-radius: var(--r-lg);
  border: 1px solid var(--border-soft);
  background: var(--surface-2);
  margin-bottom: var(--s-1);
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1);
}
.timeline-item:hover{
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(16,24,40,.10);
}
.timeline-top{ display:flex; justify-content:space-between; gap:12px; }
.timeline-title{ font-weight:800; font-size:13px; color: var(--text); }
.timeline-meta{ font-size:12px; color: rgba(17,24,39,.52); margin-top:2px; }
</style>
""", unsafe_allow_html=True)

summary = api.dashboard_summary()
kpi_expiring = summary.get("kpi_expiring", 0)
kpi_batches  = summary.get("kpi_batches", 0)
kpi_recipes  = summary.get("kpi_recipes", 0)

# 你可以做个“健康分”示意：临期占比越低越好（MVP）
health = 100
if kpi_batches:
    health = max(0, min(100, int(100 - (kpi_expiring / kpi_batches) * 120)))

# Header
c1, c2 = st.columns([3,2], vertical_alignment="center")
with c1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="font-size:34px;font-weight:900;letter-spacing:-.6px;">冰箱全局概览</div>
      <div class="chip"><span class="chip-dot"></span>Live</div>
    </div>
    <div class="muted" style="margin-top:4px;">快速了解库存健康度、临期风险与下一步该做什么。</div>
    """, unsafe_allow_html=True)

with c2:
    # 主操作（你也可以改成 st.switch_page）
    a, b = st.columns(2)
    with a: st.page_link("pages/3_📷_上传入库.py", label="📷 上传入库", icon="📷")
    with b: st.page_link("pages/4_🍽️_菜单.py", label="🍽️ 生成菜单", icon="🍽️")

# KPI cards
k1, k2, k3, k4 = st.columns(4)
def kpi_card(col, label, value, hint=""):
    col.markdown(f"""
    <div class="card card-tight">
      <div class="kpi">
        <div>
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="hint">{hint}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

kpi_card(k1, "即将过期批次", kpi_expiring, "建议优先消耗")
kpi_card(k2, "在库批次数", kpi_batches, "库存规模")
kpi_card(k3, "今日可做菜", kpi_recipes, "一键生成菜单")
kpi_card(k4, "健康分", health, "临期占比越低越好")



st.markdown("### 🥗 食材生命体征 (Live)")

# 获取数据 (复用你现有的逻辑，但我们取更多数据来展示效果)
# 注意：这里假设 inventory 包含 item_name_snapshot, days_left, unit, quantity
expiring_data = api.list_expiring(days=10)["batches"] 

def life_from_days(days_left: int) -> int:
    # 你可以换成更科学的映射：比如按“剩余/保质期总天数”
    # 这里先做一个黑客松可用的：0~10天线性映射到 0~100
    return max(0, min(100, int(days_left * 10)))


def fmt_qty(qty, unit: str = "") -> str:
    """统一数量展示（避免 1.2999999999 这种浮点噪声）"""
    try:
        q = float(qty)
        s = f"{q:.1f}"
    except Exception:
        s = str(qty)
    unit = (unit or "").strip()
    return (s + (f" {unit}" if unit else "")).strip()

if expiring_data:
    # 准备 HTML 字符串

    nodes = []
    for b in expiring_data[:30]:  # 可多展示点，D3会自己排开
        days = int(b.get("days_left", 0) or 0)
        name = b.get("item_name_snapshot", "未知")
        qty = float(b.get("quantity", 1) or 1)

        life = life_from_days(days)

        # 半径：你可以用 qty 或 “临期程度” 来决定
        # 这里用 qty 做一点变化，视觉更丰富
        r = max(26, min(60, 26 + math.sqrt(qty) * 10))

        nodes.append({
            "id": str(b.get("batch_id", name)),
            "name": name,
            "days": days,
            "life": life,
            "qty": qty,
            "unit": b.get("unit", ""),
            "expire_date": b.get("expire_date", ""),
            "r" : r, 
        })

    data_json = json.dumps(nodes, ensure_ascii=False)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    core_left, core_right = st.columns([3.2, 1.4], gap="large")

    with core_left:
        st.markdown(
            "<div class='card'><div class='card-title'>🥗 食材生命体征 <span class='muted'>聚类 / 自由漂浮 · 三向联动</span></div>",
            unsafe_allow_html=True,
        )
        html = """
        <div id="life-root" class="life-shell">
          <div class="life-header">
            <div class="life-title">
              <div class="life-title-main">食材生命体征</div>
              <div class="life-title-sub">气泡 · 列表 · 详情三向联动</div>
            </div>
            <div class="segmented" role="tablist" aria-label="layout mode">
              <button class="seg-btn" data-mode="cluster">聚类</button>
              <button class="seg-btn" data-mode="float">自由漂浮</button>
            </div>
          </div>
          <div class="life-body">
            <div class="life-canvas">
              <div id="bubble-wrap"></div>
            </div>
            <div class="life-panel">
              <div class="panel-search">
                <input id="life-search" placeholder="搜索食材..." />
              </div>
              <div class="panel-filters">
                <button class="chip-btn" data-filter="all">全部</button>
                <button class="chip-btn" data-filter="urgent">紧急</button>
                <button class="chip-btn" data-filter="soon">临期</button>
                <button class="chip-btn" data-filter="fresh">新鲜</button>
              </div>
              <div id="life-list" class="life-list"></div>
              <div id="life-detail" class="life-detail">
                <div class="detail-title">点击一个泡泡</div>
                <div class="detail-meta">查看保质期/数量/建议操作</div>
                <div class="detail-actions">
                  <button class="btn ghost" data-action="copy">📋 复制食材名</button>
                  <button class="btn ghost" data-action="pin">⭐ 标记优先消耗</button>
                  <button class="btn primary" data-action="menu">🍽️ 建议做菜</button>
                </div>
                <div class="detail-hint muted">提示：请在顶部导航进入菜单页。</div>
              </div>
            </div>
          </div>
        </div>

        <style>
        :root{
          --r-lg:18px; --r-md:14px; --r-sm:10px;
          --shadow-1:0 12px 28px rgba(16,24,40,.08);
          --shadow-2:0 18px 40px rgba(16,24,40,.14);
          --border: rgba(16,24,40,.08);
          --text: rgba(17,24,39,.92);
          --text-2: rgba(17,24,39,.72);
          --muted: rgba(17,24,39,.55);
        }
        .life-shell{
          display:flex;
          flex-direction:column;
          gap:12px;
          font-family: ui-sans-serif, system-ui;
        }
        .life-header{
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap:12px;
        }
        .life-title-main{ font-weight:800; font-size:15px; color:var(--text); }
        .life-title-sub{ font-size:12px; color:var(--muted); margin-top:2px; }
        .segmented{
          display:inline-flex;
          background: rgba(255,255,255,.7);
          border:1px solid var(--border);
          border-radius:999px;
          padding:3px;
          gap:4px;
        }
        .seg-btn{
          border:none;
          padding:6px 12px;
          border-radius:999px;
          font-size:12px;
          color:var(--text-2);
          background:transparent;
          cursor:pointer;
          transition: all .18s ease;
        }
        .seg-btn.active{
          background: #111827;
          color: #fff;
          box-shadow: 0 8px 18px rgba(17,24,39,.18);
        }
        .life-body{
          display:grid;
          grid-template-columns: 2.1fr 1fr;
          gap:14px;
        }
        #bubble-wrap{
          width:100%;
          height: var(--bubbleH);
          border-radius:18px;
          background:rgba(255,255,255,.66);
          border:1px solid rgba(16,24,40,.08);
          position:relative;
          overflow:hidden;
        }
        .life-panel{
          display:flex;
          flex-direction:column;
          gap:10px;
          height: var(--bubbleH);
          min-height: 0;
        }
        .panel-search input{
          width:100%;
          padding:10px 12px;
          border-radius:12px;
          border:1px solid var(--border);
          background: rgba(255,255,255,.8);
          font-size:12px;
        }
        .panel-filters{ display:flex; gap:8px; flex-wrap:wrap; }
        .chip-btn{
          border:1px solid var(--border);
          background:rgba(255,255,255,.78);
          padding:4px 10px;
          border-radius:999px;
          font-size:12px;
          color:var(--text-2);
          cursor:pointer;
          transition: all .16s ease;
        }
        .chip-btn.active{
          background:#111827;
          color:#fff;
          border-color:#111827;
        }
        .life-list{
          flex:1;
          overflow:auto;
          min-height: 0;
          max-height: none;
          display:flex;
          flex-direction:column;
          gap:8px;
          padding-right:4px;
        }
        .list-item{
          border:1px solid var(--border);
          background:rgba(255,255,255,.75);
          border-radius:14px;
          padding:10px 12px;
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap:10px;
          cursor:pointer;
          transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
          position:relative;
        }
        .list-item:hover{
          transform: translateY(-1px);
          box-shadow: 0 10px 22px rgba(16,24,40,.12);
        }
        .list-item.selected{
          border-color: rgba(17,24,39,.4);
          background: rgba(17,24,39,.06);
        }
        .list-item:before{
          content:"";
          position:absolute;
          left:0;
          top:10px;
          bottom:10px;
          width:3px;
          border-radius:999px;
          background: rgba(17,24,39,.15);
        }
        .list-item.selected:before{ background:#111827; }
        .list-title{ font-weight:800; font-size:13px; color:var(--text); }
        .list-sub{ font-size:12px; color:var(--muted); margin-top:2px; }
        .list-badge{
          font-size:11px;
          padding:2px 8px;
          border-radius:999px;
          border:1px solid rgba(16,24,40,.10);
          background: rgba(255,255,255,.65);
        }
        .badge-red{ border-color: rgba(239,68,68,.35); background: rgba(239,68,68,.12); color:#b91c1c; }
        .badge-yellow{ border-color: rgba(245,158,11,.35); background: rgba(245,158,11,.12); color:#92400e; }
        .badge-green{ border-color: rgba(34,197,94,.35); background: rgba(34,197,94,.12); color:#166534; }
        .pin-mark{
          display:inline-flex;
          align-items:center;
          gap:4px;
          font-size:11px;
          color:#111827;
        }
        .life-detail{
          border:1px solid var(--border);
          background: rgba(255,255,255,.92);
          border-radius:16px;
          box-shadow: var(--shadow-1);
          padding:12px;
          display:flex;
          flex-direction:column;
          gap:8px;
          transition: all .18s ease;
        }
        .detail-title{ font-weight:800; font-size:14px; color:var(--text); }
        .detail-meta{ font-size:12px; color:var(--muted); line-height:1.5; }
        .detail-actions{ display:flex; gap:8px; flex-wrap:wrap; }
        .detail-hint{ font-size:12px; color:var(--muted); }
        .btn{
          border:1px solid rgba(16,24,40,.12);
          border-radius:12px;
          padding:6px 10px;
          font-size:12px;
          cursor:pointer;
          transition: transform .15s cubic-bezier(.2,.8,.2,1), background .15s ease;
        }
        .btn:hover{ transform: translateY(-1px); }
        .btn.ghost{ background: rgba(255,255,255,.7); color:var(--text); }
        .btn.primary{ background:#111827; color:#fff; border-color:#111827; }
        .tip{
          position:absolute; pointer-events:none; opacity:0;
          background: rgba(0,0,0,.78); color:#fff; padding:10px 12px;
          border-radius:12px; font-size:12px; line-height:1.35;
          transform: translate(-50%, -110%);
          transition: opacity .12s ease;
          white-space: nowrap;
        }
        </style>

        <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
        <script>
        const data = __DATA_JSON__;
        const wrap = document.getElementById("bubble-wrap");
        const listEl = document.getElementById("life-list");
        const detailEl = document.getElementById("life-detail");
        const searchEl = document.getElementById("life-search");
        const filterButtons = document.querySelectorAll(".chip-btn");
        const modeButtons = document.querySelectorAll(".seg-btn");

        let W = wrap.getBoundingClientRect().width || 900;
        let H = wrap.getBoundingClientRect().height || 520;
        let selectedId = null;
        let activeFilter = "all";
        const pinnedIds = new Set();

        const tip = document.createElement("div");
        tip.className = "tip";
        wrap.appendChild(tip);

        function groupFromDays(days){
          if (days <= 2) return 0;
          if (days <= 5) return 1;
          return 2;
        }
        function tagFromDays(days){
          if (days <= 2) return {label:"紧急", cls:"badge-red"};
          if (days <= 5) return {label:"临期", cls:"badge-yellow"};
          return {label:"新鲜", cls:"badge-green"};
        }
        function lifeToColor(life){
          const hue = Math.max(0, Math.min(120, life * 1.2));
          return `hsl(${hue}, 85%, 78%)`;
        }
        function lifeToStroke(life){
          const hue = Math.max(0, Math.min(120, life * 1.2));
          return `hsl(${hue}, 85%, 42%)`;
        }

        const nodes = data.map(d => Object.assign(d, {
          r: d.r || 34,
          group: groupFromDays(+d.days || 0),
          x: W/2 + (Math.random()-0.5)*40,
          y: H/2 + (Math.random()-0.5)*40
        }));

        const svg = d3.select(wrap).append("svg")
          .style("width", "100%")
          .style("height", H + "px")
          .attr("viewBox", `0 0 ${W} ${H}`)
          .attr("preserveAspectRatio", "xMidYMid meet");

        const bg = svg.append("g").attr("class","bg");
        bg.style("transition", "opacity .3s ease");
        const g = svg.append("g");

        const margin = 16;
        const gap = 14;
        let centers = [];
        let floatCenter = { x: W/2, y: H/2 };
        let currentMode = localStorage.getItem("life_mode") || "cluster";

        function computeCenters() {
          W = wrap.getBoundingClientRect().width || W;
          H = wrap.getBoundingClientRect().height || H;
          const colW = (W - margin * 2 - gap * 2) / 3;
          const colCenters = [
            { title: "🔥 紧急（≤2天）",  x: margin + colW * 0.5,              y: H/2 },
            { title: "⏳ 临期（3–5天）", x: margin + (colW + gap) + colW*0.5,  y: H/2 },
            { title: "✅ 新鲜（>5天）",  x: margin + 2*(colW+gap) + colW*0.5,  y: H/2 }
          ];
          return { colCenters, colW };
        }

        function renderBackground() {
          const { colCenters, colW } = computeCenters();
          centers = colCenters;
          svg.attr("viewBox", `0 0 ${W} ${H}`);
          svg.style("height", H + "px");

          bg.selectAll("rect")
            .data(centers)
            .join("rect")
            .attr("x", (d, i) => margin + i * (colW + gap))
            .attr("y", 10)
            .attr("width", colW)
            .attr("height", H - 20)
            .attr("rx", 18)
            .attr("fill", (d, i) => [
              "rgba(255,99,71,0.12)",
              "rgba(255,193,7,0.12)",
              "rgba(76,175,80,0.12)"
            ][i]);

          bg.selectAll("text")
            .data(centers)
            .join("text")
            .attr("x", d => d.x)
            .attr("y", 32)
            .attr("text-anchor","middle")
            .style("font-weight", 700)
            .style("font-size", "12px")
            .style("fill", "#444")
            .text(d => d.title);
          bg.lower();
        }

        renderBackground();

        const node = g.selectAll("g.node")
          .data(nodes, d => d.id)
          .join("g")
          .attr("class","node")
          .style("cursor","pointer")
          .call(
            d3.drag()
              .on("start", (event, d) => {
                if (!event.active) sim.alphaTarget(0.25).restart();
                d.fx = d.x; d.fy = d.y;
              })
              .on("drag", (event, d) => {
                d.fx = event.x; d.fy = event.y;
              })
              .on("end", (event, d) => {
                if (!event.active) sim.alphaTarget(0);
                d.fx = null; d.fy = null;
              })
          )
          .on("mousemove", (event, d) => {
            tip.style.left = event.offsetX + "px";
            tip.style.top  = event.offsetY + "px";
            tip.style.opacity = 1;
            tip.innerHTML = `<b>${d.name}</b><br/>生命值：${d.life}%<br/>剩余：${d.days} 天`;
          })
          .on("mouseleave", () => { tip.style.opacity = 0; })
          .on("click", (event, d) => selectNode(d.id, true));

        node.append("circle")
          .attr("r", d => d.r)
          .attr("fill", d => lifeToColor(d.life))
          .attr("stroke", d => lifeToStroke(d.life))
          .attr("stroke-width", 1.2)
          .attr("filter","drop-shadow(0px 4px 6px rgba(0,0,0,.10))");

        node.append("circle")
          .attr("class", "pin-dot")
          .attr("r", 5)
          .attr("cx", d => d.r - 6)
          .attr("cy", d => -d.r + 6)
          .attr("fill", "#111827")
          .attr("opacity", 0);

        node.append("text")
          .attr("text-anchor","middle")
          .attr("dy","-0.2em")
          .style("font-weight",700)
          .style("font-size","12px")
          .text(d => d.name.length>6 ? d.name.slice(0,6)+"…" : d.name);

        node.append("text")
          .attr("text-anchor","middle")
          .attr("dy","1.2em")
          .style("font-size","11px")
          .style("fill","#555")
          .text(d => `生命值 ${d.life}%`);

        const sim = d3.forceSimulation(nodes)
          .force("x", d3.forceX(d => centers[d.group].x).strength(0.18))
          .force("y", d3.forceY(d => centers[d.group].y).strength(0.08))
          .force("charge", d3.forceManyBody().strength(-10))
          .force("collide", d3.forceCollide().radius(d => d.r + 6).iterations(2))
          .alpha(1)
          .alphaDecay(0.06)
          .on("tick", () => {
            nodes.forEach(d => {
              d.x = Math.max(d.r, Math.min(W - d.r, d.x));
              d.y = Math.max(d.r, Math.min(H - d.r, d.y));
            });
            node.attr("transform", d => `translate(${d.x},${d.y})`);
          });

        function applyMode(mode) {
          currentMode = mode;
          localStorage.setItem("life_mode", mode);
          modeButtons.forEach(btn => btn.classList.toggle("active", btn.dataset.mode === mode));
          if (mode === "cluster") {
            bg.style("opacity", 1);
            sim.force("x", d3.forceX(d => centers[d.group].x).strength(0.18));
            sim.force("y", d3.forceY(d => centers[d.group].y).strength(0.08));
            sim.force("charge", d3.forceManyBody().strength(-10));
          } else {
            bg.style("opacity", 0);
            sim.force("x", d3.forceX(() => floatCenter.x).strength(0.05));
            sim.force("y", d3.forceY(() => floatCenter.y).strength(0.05));
            sim.force("charge", d3.forceManyBody().strength(-6));
          }
          sim.alpha(0.8).restart();
        }

        function updatePins() {
          node.select(".pin-dot").attr("opacity", d => (pinnedIds.has(d.id) ? 1 : 0));
        }

        function updateSelection() {
          node.select("circle").attr("stroke-width", d => (d.id === selectedId ? 3.5 : 1.2));
          const items = listEl.querySelectorAll(".list-item");
          items.forEach(item => item.classList.toggle("selected", item.dataset.id === selectedId));
        }

        function renderList() {
          const keyword = (searchEl.value || "").trim().toLowerCase();
          const filtered = nodes.filter(d => {
            if (keyword && !d.name.toLowerCase().includes(keyword)) return false;
            if (activeFilter === "urgent") return d.days <= 2;
            if (activeFilter === "soon") return d.days > 2 && d.days <= 5;
            if (activeFilter === "fresh") return d.days > 5;
            return true;
          });
          listEl.innerHTML = "";
          filtered
            .sort((a, b) => a.days - b.days)
            .forEach(d => {
              const tag = tagFromDays(d.days);
              const row = document.createElement("div");
              row.className = "list-item";
              row.dataset.id = d.id;
              row.innerHTML = `
                <div>
                  <div class="list-title">${d.name}</div>
                  <div class="list-sub">剩余 ${d.days} 天 · ${Number.isFinite(+d.qty) ? (+d.qty).toFixed(1) : d.qty} ${d.unit || ""}</div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
                  <span class="list-badge ${tag.cls}">${tag.label}</span>
                  ${pinnedIds.has(d.id) ? '<span class="pin-mark">📌 优先</span>' : ""}
                </div>
              `;
              row.addEventListener("click", () => {
                selectNode(d.id, true);
                pulseNode(d.id);
              });
              listEl.appendChild(row);
            });
          updateSelection();
        }

        function pulseNode(id) {
          const target = node.filter(d => d.id === id);
          target.select("circle")
            .transition().duration(120)
            .attr("r", d => d.r * 1.08)
            .transition().duration(160)
            .attr("r", d => d.r);
        }

        function selectNode(id, scrollList = false) {
          const d = nodes.find(n => n.id === id);
          if (!d) return;
          selectedId = id;
          updateSelection();
          detailEl.querySelector(".detail-title").textContent = d.name;
          detailEl.querySelector(".detail-meta").innerHTML = `
            生命值：<b>${d.life}%</b> | 剩余 <b>${d.days}</b> 天<br/>
            数量：<b>${Number.isFinite(+d.qty) ? (+d.qty).toFixed(1) : d.qty}</b> ${d.unit || ""}<br/>
            到期日：${d.expire_date || "未知"}
          `;
          if (scrollList) {
            const row = listEl.querySelector(`[data-id="${id}"]`);
            if (row) row.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        }

        detailEl.addEventListener("click", (event) => {
          const action = event.target?.dataset?.action;
          if (!action || !selectedId) return;
          const d = nodes.find(n => n.id === selectedId);
          if (!d) return;
          if (action === "copy") {
            navigator.clipboard.writeText(d.name);
          }
          if (action === "pin") {
            if (pinnedIds.has(d.id)) {
              pinnedIds.delete(d.id);
            } else {
              pinnedIds.add(d.id);
            }
            renderList();
            updatePins();
          }
          if (action === "menu") {
            const hint = detailEl.querySelector(".detail-hint");
            if (hint) hint.textContent = "请在顶部导航进入菜单页（菜单页）。";
          }
        });

        filterButtons.forEach(btn => {
          btn.addEventListener("click", () => {
            activeFilter = btn.dataset.filter;
            filterButtons.forEach(b => b.classList.toggle("active", b === btn));
            renderList();
          });
        });
        searchEl.addEventListener("input", renderList);
        modeButtons.forEach(btn => btn.addEventListener("click", () => applyMode(btn.dataset.mode)));

        function handleResize() {
          renderBackground();
          floatCenter = { x: W / 2, y: H / 2 };
          if (currentMode === "cluster") {
            sim.force("x", d3.forceX(d => centers[d.group].x).strength(0.18));
            sim.force("y", d3.forceY(d => centers[d.group].y).strength(0.08));
          } else {
            sim.force("x", d3.forceX(() => floatCenter.x).strength(0.05));
            sim.force("y", d3.forceY(() => floatCenter.y).strength(0.05));
          }
          sim.alpha(0.8).restart();
        }

        const ro = new ResizeObserver(handleResize);
        ro.observe(wrap);

        setInterval(() => {
          if (currentMode === "float") {
            floatCenter = {
              x: W / 2 + (Math.random() - 0.5) * 40,
              y: H / 2 + (Math.random() - 0.5) * 30,
            };
            sim.alpha(0.6).restart();
          }
        }, 1200);

        requestAnimationFrame(() => {
          handleResize();
          renderList();
          applyMode(currentMode);
          filterButtons[0].classList.add("active");
        });
        </script>
        """
        components.html(
            html.replace("__DATA_JSON__", data_json).replace(
                "</style>", "\n:root{ --bubbleH: clamp(440px, 55vh, 640px); }\n</style>"
            ),
            height=700,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with core_right:
        md_html(
            """
            <div class="card">
              <div class="card-title">⚡ 今日建议 <span class="muted">快捷操作</span></div>
              <div class="muted" style="margin-bottom:12px;">
                聚焦临期食材，建议先生成菜单或快速补货。
              </div>
              <div style="display:grid;gap:8px;">
                <a href="/pages/4_🍽️_菜单.py">🍽️ 生成菜单</a>
                <a href="/pages/5_🧾_购物清单.py">🧾 查看购物清单</a>
                <a href="/pages/2_📦_库存.py">📦 查看库存</a>
              </div>
            </div>
            """
        )

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    
else:
    st.balloons() # 如果库存非常健康，给点奖励
    st.success("冰箱现在空空如也，或者所有食材都非常新鲜！") 

st.markdown("### 最近事件流")
events = api.list_events(limit=10)["events"]
if events:
    ev_df = pd.DataFrame(events)
    ev_df = ev_df[["event_type", "batch_id", "delta_quantity", "note", "created_at"]]
    ev_df.rename(
        columns={
            "event_type": "事件",
            "batch_id": "批次",
            "delta_quantity": "数量变化",
            "note": "备注",
            "created_at": "时间",
        },
        inplace=True,
    )
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><div class='card-title'>🕒 最近动态 <span class='muted'>最近 8 条</span></div>", unsafe_allow_html=True)

    events = api.list_events(limit=8)["events"]
    if events:
        for e in events:
            et = e.get("event_type","")
            note = e.get("note","")
            t = e.get("created_at","")
            dq = e.get("delta_quantity","")
            bid = e.get("batch_id","")
            md_html(f"""
            <div class="timeline-item">
              <div class="timeline-top">
                <div class="timeline-title">{et} <span class="muted">· {bid}</span></div>
                <div class="muted">{t}</div>
              </div>
              <div class="timeline-meta">数量变化：{dq} · {note}</div>
            </div>
            """)
    else:
        st.info("还没有事件记录，先去上传识别一些食材吧。")

st.markdown("</div>", unsafe_allow_html=True)
