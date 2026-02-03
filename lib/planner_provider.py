from __future__ import annotations

import json
import os
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Tuple

import requests

from . import db
from .menu_engine import generate_menu as greedy_generate_menu
from .utils import format_date, from_json, now_ts, sum_by_key, today


class ProviderNotAvailable(Exception):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


def _inventory_map(batches: List[Dict[str, Any]]) -> Dict[int, float]:
    inv: Dict[int, float] = {}
    for batch in batches:
        if not batch.get("item_id"):
            continue
        inv[batch["item_id"]] = inv.get(batch["item_id"], 0) + float(batch["quantity"])
    return inv


def _coverage(recipe_items: List[Dict[str, Any]], inventory: Dict[int, float]) -> Tuple[float, Dict[int, float]]:
    if not recipe_items:
        return 0.0, {}
    covered = 0
    gaps: Dict[int, float] = {}
    for ing in recipe_items:
        need = float(ing["quantity"])
        have = inventory.get(ing["item_id"], 0)
        if have >= need:
            covered += 1
        else:
            gaps[ing["item_id"]] = need - have
    coverage = covered / len(recipe_items)
    return coverage, gaps


class GreedyPlannerProvider:
    id = "greedy"
    name = "Greedy (Offline)"

    def is_available(self) -> tuple[bool, str]:
        return True, ""

    def generate(self, days: int, servings: int, constraints: Dict[str, Any]) -> Dict[str, Any]:
        return greedy_generate_menu(days, servings, constraints)


class HttpPlannerProvider:
    id = "http"
    name = "HTTP Planner (Generic)"

    def __init__(self) -> None:
        self.endpoint = os.getenv("PLANNER_HTTP_ENDPOINT")
        self.headers_json = os.getenv("PLANNER_HTTP_HEADERS_JSON", "")
        timeout = os.getenv("PLANNER_HTTP_TIMEOUT", "20")
        self.timeout = int(timeout) if timeout.isdigit() else 20

    def is_available(self) -> tuple[bool, str]:
        if not self.endpoint:
            return False, "PLANNER_HTTP_ENDPOINT is not configured"
        return True, ""

    def _headers(self) -> Dict[str, str]:
        if not self.headers_json:
            return {"Content-Type": "application/json"}
        try:
            headers = json.loads(self.headers_json)
            headers["Content-Type"] = "application/json"
            return headers
        except json.JSONDecodeError as exc:
            raise ProviderNotAvailable("PROVIDER_CONFIG_ERROR", f"Invalid PLANNER_HTTP_HEADERS_JSON: {exc}") from exc

    def _build_candidates(
        self,
        inventory: Dict[int, float],
        recipe_map: Dict[int, List[Dict[str, Any]]],
        recipes: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        scored: List[Tuple[int, float]] = []
        for recipe in recipes:
            items = recipe_map.get(recipe["recipe_id"], [])
            coverage, gaps = _coverage(items, inventory)
            score = coverage - sum_by_key(
                [{"gap": gap} for gap in gaps.values()],
                "gap",
            ) * 0.05
            scored.append((recipe["recipe_id"], score))
        scored.sort(key=lambda x: x[1], reverse=True)
        selected = {recipe_id for recipe_id, _ in scored[:top_k]}
        candidates = []
        items_lookup = {item["item_id"]: item for item in db.list_items()}
        for recipe in recipes:
            if recipe["recipe_id"] not in selected:
                continue
            ingredients = []
            for ing in recipe_map.get(recipe["recipe_id"], []):
                item = items_lookup.get(ing["item_id"], {})
                ingredients.append(
                    {
                        "item_id": ing["item_id"],
                        "item_name": item.get("name") or str(ing["item_id"]),
                        "quantity": ing["quantity"],
                        "unit": ing["unit"],
                    }
                )
            candidates.append(
                {
                    "recipe_id": recipe["recipe_id"],
                    "name": recipe["name"],
                    "allergens": recipe.get("allergens") or "",
                    "ingredients": ingredients,
                }
            )
        return candidates

    def _build_inventory(self, batches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        inventory = []
        for batch in batches:
            inventory.append(
                {
                    "item_id": batch.get("item_id"),
                    "item_name": batch.get("item_name_snapshot"),
                    "quantity": batch.get("quantity"),
                    "unit": batch.get("unit"),
                    "expire_date": batch.get("expire_date"),
                }
            )
        return inventory

    def _calculate_gap(
        self,
        recipe_ids: List[int],
        recipe_map: Dict[int, List[Dict[str, Any]]],
        inventory: Dict[int, float],
    ) -> Dict[int, float]:
        gap: Dict[int, float] = {}
        for recipe_id in recipe_ids:
            for ing in recipe_map.get(recipe_id, []):
                need = float(ing["quantity"])
                have = inventory.get(ing["item_id"], 0)
                if have < need:
                    gap[ing["item_id"]] = gap.get(ing["item_id"], 0) + (need - have)
        return gap

    def _build_plan_items(
        self,
        menu_id: str,
        recipe_ids: List[int],
        explain_map: Dict[int, List[str]],
        recipes: Dict[int, Dict[str, Any]],
        days: int,
    ) -> List[Dict[str, Any]]:
        plan_items = []
        day_cursor = today()
        meal_types = ["lunch", "dinner"]
        for idx, recipe_id in enumerate(recipe_ids[: max(1, days * 2)]):
            recipe = recipes.get(recipe_id, {})
            plan_items.append(
                {
                    "id": f"mpi_{uuid.uuid4().hex[:8]}",
                    "menu_id": menu_id,
                    "date": format_date(day_cursor),
                    "meal_type": meal_types[idx % len(meal_types)],
                    "recipe_id": recipe_id,
                    "explain": explain_map.get(recipe_id, ["基于外部 planner 推荐", "适配当前库存情况"]),
                    "nutrition": from_json(recipe.get("nutrition_json"), {}),
                }
            )
            if (idx + 1) % len(meal_types) == 0:
                day_cursor = day_cursor + timedelta(days=1)
        return plan_items

    def _build_shopping_items(
        self,
        menu_id: str,
        gap: Dict[int, float],
        items_lookup: Dict[int, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        shopping_items = []
        for item_id, gap_qty in gap.items():
            item = items_lookup.get(item_id)
            if not item:
                continue
            shopping_items.append(
                {
                    "id": f"shop_{uuid.uuid4().hex[:8]}",
                    "menu_id": menu_id,
                    "item_id": item_id,
                    "item_name_snapshot": item["name"],
                    "need_qty": round(gap_qty, 1),
                    "unit": item.get("default_unit") or "unit",
                    "reason": {"gap": gap_qty, "source": "planner_http"},
                    "checked": False,
                }
            )
        return shopping_items

    def generate(self, days: int, servings: int, constraints: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG][HttpPlanner] endpoint =", repr(self.endpoint)) 
        available, reason = self.is_available()
        if not available:
            raise ProviderNotAvailable("PROVIDER_NOT_AVAILABLE", reason)

        recipes = db.list_recipes()
        recipe_map: Dict[int, List[Dict[str, Any]]] = {}
        for ing in db.list_recipe_ingredients():
            recipe_map.setdefault(ing["recipe_id"], []).append(ing)
        batches = db.list_batches({"status": "in_stock"})
        inventory_map = _inventory_map(batches)

        payload = {
            "days": days,
            "servings": servings,
            "constraints": constraints,
            "inventory": self._build_inventory(batches),
            "candidates": self._build_candidates(inventory_map, recipe_map, recipes, top_k=10),
            "top_k": 10,
        }
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        print("[DEBUG][HttpPlanner] status =", response.status_code, "text_head =", response.text[:120])

        if response.status_code >= 400:
            raise ProviderNotAvailable(
            "PROVIDER_RESPONSE_ERROR",
            f"{response.status_code} {response.text}")
        # response.raise_for_status()
        data = response.json()
        selected = data.get("selected")
        if not isinstance(selected, list) or not selected:
            raise ProviderNotAvailable("PROVIDER_RESPONSE_INVALID", "Response missing selected list")

        recipe_lookup = {recipe["recipe_id"]: recipe for recipe in recipes}
        recipe_ids: List[int] = []
        explain_map: Dict[int, List[str]] = {}
        for entry in selected:
            recipe_id = entry.get("recipe_id")
            if recipe_id not in recipe_lookup:
                continue
            recipe_ids.append(recipe_id) 
            explain = entry.get("explain") or []
            if not isinstance(explain, list):
                explain = [str(explain)]
            explain_map[recipe_id] = explain

        if not recipe_ids:
            raise ProviderNotAvailable("PROVIDER_RESPONSE_INVALID", "No valid recipe_id in selected list")

        menu_id = f"menu_{uuid.uuid4().hex[:8]}"
        db.insert_menu_plan(menu_id, days, servings, constraints)

        plan_items = self._build_plan_items(
            menu_id=menu_id,
            recipe_ids=recipe_ids,
            explain_map=explain_map,
            recipes=recipe_lookup,
            days=days,
        )
        db.insert_menu_plan_items(plan_items)

        gap = self._calculate_gap(recipe_ids, recipe_map, inventory_map)
        items_lookup = {item["item_id"]: item for item in db.list_items()}
        shopping_items = self._build_shopping_items(menu_id, gap, items_lookup)
        if shopping_items:
            db.insert_shopping_items(shopping_items)

        return {"menu_id": menu_id, "plan": plan_items, "shopping_gap": shopping_items}


import re

class LocalModelPlannerProvider(HttpPlannerProvider):
    """
    Local LLM planner.
    Reuse HttpPlannerProvider's candidate/inventory building + DB writing pipeline.
    Only replace "call external http planner" with "call local model".
    """
    id = "local"
    name = "Local LLM Planner (Ollama/Local Server)"

    def __init__(self) -> None:
        # Local LLM endpoint (Ollama default)
        self.model = os.getenv("PLANNER_LOCAL_MODEL", "qwen2.5:7b-instruct")
        self.endpoint = os.getenv("PLANNER_LOCAL_ENDPOINT", "http://localhost:11434/api/generate")
        timeout = os.getenv("PLANNER_LOCAL_TIMEOUT", "40")
        self.timeout = int(timeout) if timeout.isdigit() else 40

    def is_available(self) -> tuple[bool, str]:
        # 简单检查：endpoint & model
        if not self.endpoint:
            return False, "PLANNER_LOCAL_ENDPOINT is not configured"
        if not self.model:
            return False, "PLANNER_LOCAL_MODEL is not configured"
        return True, ""

    def _build_prompt(self, payload: Dict[str, Any]) -> str:
        """
        关键：强制模型只输出 JSON。
        payload 里有 inventory + candidates + constraints。
        """
        days = payload.get("days")
        servings = payload.get("servings")
        constraints = payload.get("constraints", {})
        inv = payload.get("inventory", [])
        cands = payload.get("candidates", [])

        # 压缩输入，避免 prompt 太长
        inv_lines = []
        for b in inv[:30]:
            inv_lines.append(
                f"- {b.get('item_name') or b.get('item_name_snapshot') or b.get('item_id')}"
                f" x{b.get('quantity')} {b.get('unit','')}"
                f" exp:{b.get('expire_date')}"
            )

        cand_lines = []
        for r in cands[:40]:
            ing_str = ", ".join(
                [f"{i.get('item_name')}:{i.get('quantity')}{i.get('unit','')}" for i in (r.get("ingredients") or [])[:8]]
            )
            cand_lines.append(f"- recipe_id={r.get('recipe_id')} | {r.get('name')} | ings: {ing_str}")

        allergies = constraints.get("allergies") or constraints.get("avoid_allergens") or []

        return f"""你是智能冰箱的“菜单规划器”。请从候选菜谱里选择适合的菜，目标：
1) 优先消耗临期食材（expire_date 更近）
2) 尽量覆盖现有库存，减少需要额外购买的缺口
3) 避免过敏/忌口：{allergies}
4) 尽量多样，不要重复

需求：{days} 天，servings={servings}，每天建议2餐（lunch/dinner）。
你只能从候选菜谱中选 recipe_id。

【库存批次】
{chr(10).join(inv_lines)}

【候选菜谱】
{chr(10).join(cand_lines)}

【输出格式（必须严格 JSON，不要附加任何解释文字）】
{{
  "selected": [
    {{
      "recipe_id": 123,
      "explain": ["一句话理由1", "一句话理由2"]
    }}
  ]
}}
"""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        模型偶尔会在 JSON 前后夹杂文字，做一个稳健抽取。
        """
        if not text:
            return {}
        # 找到第一个 { 到最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            # 再做一次更激进的：取出最外层 JSON 对象
            m = re.search(r"\{.*\}", text, flags=re.S)
            if not m:
                return {}
            try:
                return json.loads(m.group(0))
            except Exception:
                return {}

    def _call_local_model(self, prompt: str) -> Dict[str, Any]:
        """
        默认使用 Ollama /api/generate。
        你也可以把 endpoint 换成 llama.cpp server 的 completion endpoint（返回字段不同的话这里适配一下）。
        """
        print("[DEBUG][LocalModel] endpoint =", repr(self.endpoint), "model =", repr(self.model))

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }
        resp = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        print("[DEBUG][LocalModel] status =", resp.status_code, "raw_head =", resp.text[:120])

        resp.raise_for_status()
        data = resp.json()
        # Ollama generate: {"response": "..."}
        text = data.get("response", "")
        return self._extract_json(text)

    def generate(self, days: int, servings: int, constraints: Dict[str, Any]) -> Dict[str, Any]:
        available, reason = self.is_available()
        if not available:
            raise ProviderNotAvailable("PROVIDER_NOT_AVAILABLE", reason)

        # ====== 这段复用 HttpPlannerProvider 的数据准备 ======
        recipes = db.list_recipes()
        recipe_map: Dict[int, List[Dict[str, Any]]] = {}
        for ing in db.list_recipe_ingredients():
            recipe_map.setdefault(ing["recipe_id"], []).append(ing)
        batches = db.list_batches({"status": "in_stock"})
        inventory_map = _inventory_map(batches)

        payload = {
            "days": days,
            "servings": servings,
            "constraints": constraints,
            "inventory": self._build_inventory(batches),
            "candidates": self._build_candidates(inventory_map, recipe_map, recipes, top_k=10),
            "top_k": 10,
        }

        # ====== 关键替换：本地模型决策 selected ======
        prompt = self._build_prompt(payload)
        llm_out = self._call_local_model(prompt)

        selected = llm_out.get("selected")
        if not isinstance(selected, list) or not selected:
            raise ProviderNotAvailable("PROVIDER_RESPONSE_INVALID", "Local model missing selected list")

        # ====== 后续：完全照抄你 HttpPlannerProvider 的落库/计划/购物清单逻辑 ======
        recipe_lookup = {recipe["recipe_id"]: recipe for recipe in recipes}
        recipe_ids: List[int] = []
        explain_map: Dict[int, List[str]] = {}

        for entry in selected:
            recipe_id = entry.get("recipe_id")
            if recipe_id not in recipe_lookup:
                continue
            recipe_ids.append(recipe_id)
            explain = entry.get("explain") or []
            if not isinstance(explain, list):
                explain = [str(explain)]
            explain_map[recipe_id] = explain

        if not recipe_ids:
            raise ProviderNotAvailable("PROVIDER_RESPONSE_INVALID", "No valid recipe_id in selected list")

        menu_id = f"menu_{uuid.uuid4().hex[:8]}"
        db.insert_menu_plan(menu_id, days, servings, constraints)

        plan_items = self._build_plan_items(
            menu_id=menu_id,
            recipe_ids=recipe_ids,
            explain_map=explain_map,
            recipes=recipe_lookup,
            days=days,
        )
        db.insert_menu_plan_items(plan_items)

        gap = self._calculate_gap(recipe_ids, recipe_map, inventory_map)
        items_lookup = {item["item_id"]: item for item in db.list_items()}
        shopping_items = self._build_shopping_items(menu_id, gap, items_lookup)
        if shopping_items:
            db.insert_shopping_items(shopping_items)

        return {
            "menu_id": menu_id,
            "plan": plan_items,
            "shopping_gap": shopping_items,
            "llm_raw": llm_out,   # 便于调试
        }


def list_planners() -> Dict[str, object]:
    return {
        GreedyPlannerProvider.id: GreedyPlannerProvider(),
        HttpPlannerProvider.id: HttpPlannerProvider(),
        LocalModelPlannerProvider.id: LocalModelPlannerProvider(),
    }


def get_planner(name: str):
    

    planners = list_planners()
    if name not in planners:
        raise ProviderNotAvailable("PROVIDER_NOT_FOUND", f"Planner '{name}' not registered")
    planner = planners[name]
    print("[DEBUG] get_planner:", name, "->", type(planner).__name__)
    available, reason = planner.is_available()
    if not available:
        raise ProviderNotAvailable("PROVIDER_NOT_AVAILABLE", reason)
    return planner
