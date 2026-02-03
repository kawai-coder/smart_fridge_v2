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

    left, right = st.columns([2.2, 1], gap="large")

    with left:
        st.markdown("<div class='card'><div class='card-title'>🥗 食材生命体征 <span class='muted'>按临期聚类 · 可拖拽 · 可点击</span></div>", unsafe_allow_html=True)
        html = """
        <div id="bubble-wrap" style="width:100%; height:360px; border-radius:18px; background:rgba(255,255,255,.66); border:1px solid rgba(16,24,40,.08); position:relative; overflow:hidden;"></div>

        <style>
        :root{ --r-lg:18px; --r-md:14px; --r-sm:10px; --shadow-1:0 12px 28px rgba(16,24,40,.08); --shadow-2:0 18px 40px rgba(16,24,40,.14); --border: rgba(16,24,40,.08); }
        .tip {
            position:absolute; pointer-events:none; opacity:0;
            background: rgba(0,0,0,.78); color:#fff; padding:10px 12px;
            border-radius:12px; font-size:12px; line-height:1.35;
            transform: translate(-50%, -110%);
            transition: opacity .12s ease;
            white-space: nowrap;
        }
        .drawer {
            position:absolute; top:14px; right:14px; width:260px;
            background: rgba(255,255,255,.92);
            border: 1px solid var(--border);
            border-radius: var(--r-lg);
            box-shadow: var(--shadow-2);
            padding: 12px 12px;
            opacity:0; transform: translateY(6px);
            transition: all .18s cubic-bezier(.2,.8,.2,1);
            font-family: ui-sans-serif, system-ui;
        }
        .drawer.show { opacity:1; transform: translateY(0); }
        .drawer .title { font-weight:700; font-size:14px; margin-bottom:6px; }
        .drawer .meta { color:#666; font-size:12px; }
        .drawer .actions { margin-top:10px; display:flex; gap:8px; flex-wrap:wrap; }
        .btn {
            border:1px solid rgba(16,24,40,.10);
            background: rgba(255,255,255,.70);
            border-radius: 12px;
            padding:6px 10px;
            font-size:12px;
            cursor:pointer;
            transition: transform .15s cubic-bezier(.2,.8,.2,1), background .15s ease;
        }
        .btn:hover { background: rgba(255,255,255,.92); transform: translateY(-1px); }
        </style>

        <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
        <script>
        const data = __DATA_JSON__;

        const wrap = document.getElementById("bubble-wrap");

        // 用可变尺寸（关键：不要 const W = ... || 900 固死）
        let W = wrap.getBoundingClientRect().width || 900;
        let H = wrap.getBoundingClientRect().height || 360;

        const tip = document.createElement("div");
        tip.className = "tip";
        wrap.appendChild(tip);

        const drawer = document.createElement("div");
        drawer.className = "drawer";
        drawer.innerHTML = `
            <div class="title">点击一个泡泡</div>
            <div class="meta">查看保质期/数量/建议操作</div>
            <div class="actions"></div>
        `;
        wrap.appendChild(drawer);

        function lifeToColor(life){
            const hue = Math.max(0, Math.min(120, life * 1.2));
            return `hsl(${hue}, 85%, 78%)`;
        }
        function lifeToStroke(life){
            const hue = Math.max(0, Math.min(120, life * 1.2));
            return `hsl(${hue}, 85%, 42%)`;
        }

        // ====== SVG：用 viewBox + width:100%，避免固定像素宽导致留白 ======
        const svg = d3.select(wrap).append("svg")
            .style("width", "100%")
            .style("height", H + "px")
            .attr("viewBox", `0 0 ${W} ${H}`)
            .attr("preserveAspectRatio", "xMidYMid meet");

        const bg = svg.append("g").attr("class","bg");
        bg.lower();

        const g = svg.append("g");

        // ====== 1) 聚类分桶规则（按 days 分 3 组）======
        function groupFromDays(days){
            if (days <= 2) return 0;   // 紧急
            if (days <= 5) return 1;   // 临期
            return 2;                  // 新鲜
        }

        // ====== 2) 节点初始化 + group ======
        const nodes = data.map(d => Object.assign(d, {
            r: d.r || 34,
            group: groupFromDays(+d.days || 0),
            x: W/2 + (Math.random()-0.5)*40,
            y: H/2 + (Math.random()-0.5)*40
        }));

        // ====== 3) 三列布局：动态计算 centers + 背景（可重算）======
        const margin = 16;
        const gap = 14; // 三列之间的间隔（让分区更“卡片化”）

        function computeCenters() {
            W = wrap.getBoundingClientRect().width || W;
            H = wrap.getBoundingClientRect().height || H;

            const colW = (W - margin * 2 - gap * 2) / 3;

            const centers = [
            { title: "🔥 紧急（≤2天）",  x: margin + colW * 0.5,              y: H/2 },
            { title: "⏳ 临期（3–5天）", x: margin + (colW + gap) + colW*0.5,  y: H/2 },
            { title: "✅ 新鲜（>5天）",  x: margin + 2*(colW+gap) + colW*0.5,  y: H/2 }
            ];
            return { centers, colW };
        }

        function renderBackground() {
            const { centers, colW } = computeCenters();

            // 更新 SVG 坐标系，确保铺满当前真实宽度
            svg.attr("viewBox", `0 0 ${W} ${H}`);
            svg.style("height", H + "px");

            // 背景 rect
            bg.selectAll("rect")
            .data(centers)
            .join("rect")
            .attr("x", (d, i) => margin + i * (colW + gap))
            .attr("y", 10)
            .attr("width", colW)
            .attr("height", H - 20)
            .attr("rx", 18)
            .attr("fill", (d, i) => [
                "rgba(255,99,71,0.12)",   // 紧急：红
                "rgba(255,193,7,0.12)",   // 临期：黄
                "rgba(76,175,80,0.12)"    // 新鲜：绿
            ][i]);

            // 标题 text
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
            return centers;
        }

        let centers = renderBackground();

        let selectedId = null;

        // ====== 节点渲染 ======
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
            tip.innerHTML = `
                <b>${d.name}</b><br/>
                生命值：${d.life}%<br/>
                剩余：${d.days} 天
            `;
            })
            .on("mouseleave", () => {
            tip.style.opacity = 0;
            })
            .on("click", (event, d) => {
            selectedId = d.id;
            node.select("circle").attr("stroke-width", x => x.id===selectedId ? 4 : 1.2);

            drawer.classList.add("show");
            drawer.querySelector(".title").textContent = d.name;
            drawer.querySelector(".meta").innerHTML = `
                生命值：<b>${d.life}%</b> | 剩余 <b>${d.days}</b> 天<br/>
                数量：<b>${(Number.isFinite(+d.qty) ? (+d.qty).toFixed(1) : d.qty)}</b> ${d.unit || ""}<br/>
                到期日：${d.expire_date || "未知"}
            `;

            const actions = drawer.querySelector(".actions");
            actions.innerHTML = "";
            const mk = (label, onClick) => {
                const btn = document.createElement("button");
                btn.className = "btn";
                btn.textContent = label;
                btn.onclick = onClick;
                actions.appendChild(btn);
            };

            mk("📋 复制食材名", () => navigator.clipboard.writeText(d.name));
            mk("⭐ 设为优先消耗", () => alert("MVP：已标记（你可后续接 API 写入事件）"));
            mk("✅ 关闭", () => drawer.classList.remove("show"));
            });

        node.append("circle")
            .attr("r", d => d.r)
            .attr("fill", d => lifeToColor(d.life))
            .attr("stroke", d => lifeToStroke(d.life))
            .attr("stroke-width", 1.2)
            .attr("filter","drop-shadow(0px 4px 6px rgba(0,0,0,.10))");

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

        // ====== 5) 核心：forceX 按 group 吸到各自列中心 + 防重叠 ======
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

        // ====== 关键：监听容器 resize，重算三列并让仿真重新吸过去 ======
        const ro = new ResizeObserver(() => {
            centers = renderBackground();
            sim.force("x", d3.forceX(d => centers[d.group].x).strength(0.18));
            sim.force("y", d3.forceY(d => centers[d.group].y).strength(0.08));
            sim.alpha(0.9).restart();
        });
        ro.observe(wrap);

        // 首帧再补一枪（防止初次宽度读到 0）
        requestAnimationFrame(() => {
            centers = renderBackground();
            sim.force("x", d3.forceX(d => centers[d.group].x).strength(0.18));
            sim.force("y", d3.forceY(d => centers[d.group].y).strength(0.08));
            sim.alpha(0.9).restart();
        });
        </script>
        """
        components.html(html.replace("__DATA_JSON__", data_json), height=380)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        # 右侧行动面板：今日优先消耗（Top 6）
        urgent = sorted(nodes, key=lambda x: x["days"])[:6]
        st.markdown("<div class='card'><div class='card-title'>📌 今日优先消耗 <span class='muted'>Top 6</span></div>", unsafe_allow_html=True)

        for u in urgent:
            if u["days"] <= 2:
                badge = "red"
                tag = "紧急"
            elif u["days"] <= 5:
                badge = "yellow"
                tag = "临期"
            else:
                badge = "green"
                tag = "新鲜"
            md_html(f"""
            <div class="row">
              <div>
                <div style="font-weight:800;color:rgba(17,24,39,.92);">{u["name"]}</div>
                <div class="muted">剩余 {u["days"]} 天 · {fmt_qty(u["qty"], u["unit"])}</div>
              </div>
              <div class="badge {badge}">{tag}</div>
            </div>
            """)

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='muted'>建议：先处理紧急/临期 → 再做菜单组合。</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    
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
