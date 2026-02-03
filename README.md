# Smart Fridge 智能冰箱 MVP (Streamlit)

一镜到底 Demo：上传冰箱照片 → Mock 识别食材 → 用户确认入库 → 库存管理（编辑/消耗/丢弃） → 自动生成菜单 → 自动生成购物清单。

## 功能亮点
- **离线可跑**：无需外部模型或联网 API。
- **Mock Vision Provider**：基于 `image_id` 的稳定随机规则生成识别结果。
- **SQLite 数据库**：`schema.sql` 自动建表，启动时自动初始化。
- **菜单引擎**：优先临期批次、最小缺口的贪心策略。
- **多页面 Streamlit**：评委打开即可理解流程。

## 目录结构
```
smart-fridge/
  app.py
  pages/
    1_📊_Dashboard.py
    2_📦_库存.py
    3_📷_上传入库.py
    4_🍽️_菜单.py
    5_🧾_购物清单.py
  lib/
    db.py
    schemas.py
    vision_provider.py
    menu_engine.py
    api.py
    utils.py
  db/
    schema.sql
    seed.py
  data/
  assets/
    demo_images/
  requirements.txt
  README.md
```

## 运行方式
1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 初始化数据（可选，应用启动也会自动初始化）
```bash
python db/seed.py
```

3. 启动应用
```bash
streamlit run app.py
```

## Demo 使用指南
- **上传入库页**：上传照片后点击“开始识别”，或使用“生成随机示例检测结果”。
- **库存页**：可编辑数量/到期日/位置；支持消耗与丢弃记录。
- **菜单页**：设置天数、份数、偏好后生成菜单计划。
- **购物清单页**：查看缺口、勾选已购买、导出 CSV。

## HTTP Vision Provider 接入
默认使用 Mock provider；若未配置 endpoint 将自动降级到 mock。

```bash
export VISION_HTTP_ENDPOINT="https://your-vision-endpoint/predict"
export VISION_HTTP_HEADERS_JSON='{"Authorization":"Bearer xxx"}'
export VISION_HTTP_TIMEOUT=20
```

期望响应 JSON 格式（简化示例）：
```json
{
  "detections": [
    {
      "name": "番茄",
      "confidence": 0.92,
      "quantity": 2,
      "unit": "pcs",
      "suggest_expire_date": "2024-08-01",
      "location": "fridge"
    }
  ]
}
```

## HTTP Planner Provider 接入
默认使用 Greedy planner；若未配置 endpoint 将自动降级到 greedy。

```bash
export PLANNER_HTTP_ENDPOINT="https://your-planner-endpoint/plan"
export PLANNER_HTTP_HEADERS_JSON='{"Authorization":"Bearer xxx"}'
export PLANNER_HTTP_TIMEOUT=20
```

期望响应 JSON 格式（简化示例）：
```json
{
  "selected": [
    {"recipe_id": 1, "explain": ["覆盖度高", "优先消耗临期食材"]},
    {"recipe_id": 2, "explain": ["缺口最小", "适合当前份数"]}
  ],
  "notes": "optional"
}
```

## 数据说明
- SQLite DB 默认位于 `data/smart_fridge.db`。
- 所有业务逻辑集中在 `lib/` 目录，页面仅负责 UI。

## 注意事项
- `assets/demo_images/` 可放置演示图片（可空）。
- 营养信息为 MVP 示例，若为空会提示“未提供营养信息（MVP）”。
