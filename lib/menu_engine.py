from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple

from . import db
from .utils import format_date, from_json, now_ts, sum_by_key, today


def _inventory_map(batches: List[Dict[str, Any]]) -> Dict[int, float]:
    inv: Dict[int, float] = {}
    for batch in batches:
        if not batch.get("item_id"):
            continue
        inv[batch["item_id"]] = inv.get(batch["item_id"], 0) + float(batch["quantity"])
    return inv


def _expiring_bonus(recipe_items: List[Dict[str, Any]], batches: List[Dict[str, Any]]) -> float:
    bonus = 0.0
    for ing in recipe_items:
        for batch in batches:
            if batch.get("item_id") == ing["item_id"] and batch.get("expire_date"):
                days_left = (date.fromisoformat(batch["expire_date"]) - today()).days
                if days_left <= 3:
                    bonus += max(0, 3 - days_left)
    return bonus


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


def generate_menu(days: int, servings: int, constraints: Dict[str, Any]) -> Dict[str, Any]:
    recipes = db.list_recipes()
    recipe_ings = db.list_recipe_ingredients()
    batches = db.list_batches({"status": "in_stock"})
    inventory = _inventory_map(batches)
    allergens_exclude = set(constraints.get("allergens_exclude") or [])
    prefer_expiring = bool(constraints.get("prefer_expiring", True))

    recipe_map: Dict[int, List[Dict[str, Any]]] = {}
    for ing in recipe_ings:
        recipe_map.setdefault(ing["recipe_id"], []).append(ing)

    scored: List[Tuple[int, float, Dict[int, float], List[str]]] = []
    for recipe in recipes:
        allergens = set(filter(None, (recipe.get("allergens") or "").split(",")))
        if allergens_exclude and allergens_exclude.intersection(allergens):
            continue
        recipe_items = recipe_map.get(recipe["recipe_id"], [])
        coverage, gaps = _coverage(recipe_items, inventory)
        bonus = _expiring_bonus(recipe_items, batches) if prefer_expiring else 0.0
        score = coverage + bonus * 0.2 - sum_by_key(
            [
                {"gap": gap}
                for gap in gaps.values()
            ],
            "gap",
        ) * 0.05
        explain = [
            f"覆盖率 {coverage:.0%}，缺口较小" if gaps else "库存覆盖率高",
            "包含临期批次，加速消耗" if bonus > 0 else "使用常备食材",
        ]
        scored.append((recipe["recipe_id"], score, gaps, explain))

    scored.sort(key=lambda x: x[1], reverse=True)

    menu_id = f"menu_{uuid.uuid4().hex[:8]}"
    db.insert_menu_plan(menu_id, days, servings, constraints)

    plan_items = []
    shopping_gap: Dict[int, float] = {}
    used_recipes = set()
    total_slots = max(1, min(days * 2, len(scored)))
    day_cursor = today()
    meal_types = ["lunch", "dinner"]
    idx = 0
    for _ in range(total_slots):
        while idx < len(scored) and scored[idx][0] in used_recipes:
            idx += 1
        if idx >= len(scored):
            break
        recipe_id, _, gaps, explain = scored[idx]
        used_recipes.add(recipe_id)
        date_str = format_date(day_cursor)
        meal_type = meal_types[len(plan_items) % len(meal_types)]
        plan_items.append(
            {
                "id": f"mpi_{uuid.uuid4().hex[:8]}",
                "menu_id": menu_id,
                "date": date_str,
                "meal_type": meal_type,
                "recipe_id": recipe_id,
                "explain": explain,
                "nutrition": from_json(
                    next((r["nutrition_json"] for r in recipes if r["recipe_id"] == recipe_id), "{}"),
                    {},
                ),
            }
        )
        for item_id, gap in gaps.items():
            shopping_gap[item_id] = shopping_gap.get(item_id, 0) + gap
        if len(plan_items) % len(meal_types) == 0:
            day_cursor = day_cursor + timedelta(days=1)
        idx += 1

    db.insert_menu_plan_items(plan_items)

    items = {item["item_id"]: item for item in db.list_items()}
    shopping_items = []
    for item_id, gap in shopping_gap.items():
        item = items.get(item_id)
        if not item:
            continue
        shopping_items.append(
            {
                "id": f"shop_{uuid.uuid4().hex[:8]}",
                "menu_id": menu_id,
                "item_id": item_id,
                "item_name_snapshot": item["name"],
                "need_qty": round(gap, 1),
                "unit": item.get("default_unit") or "unit",
                "reason": {"gap": gap, "source": "menu_engine"},
                "checked": False,
            }
        )

    if shopping_items:
        db.insert_shopping_items(shopping_items)

    return {
        "menu_id": menu_id,
        "plan": plan_items,
        "shopping_gap": shopping_items,
    }
