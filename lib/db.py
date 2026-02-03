from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .utils import DATETIME_FMT, from_json, now_ts, to_json

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "smart_fridge.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema_sql)


def fetch_all(query: str, params: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def fetch_one(query: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def execute(query: str, params: Iterable[Any] = ()) -> None:
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()


def execute_many(query: str, params_list: Iterable[Iterable[Any]]) -> None:
    with get_connection() as conn:
        conn.executemany(query, params_list)
        conn.commit()


def upsert_image(image_id: str, file_path: str) -> None:
    execute(
        "INSERT OR REPLACE INTO images(image_id, file_path, uploaded_at) VALUES (?, ?, ?)",
        (image_id, file_path, now_ts()),
    )


def get_image(image_id: str) -> Optional[Dict[str, Any]]:
    return fetch_one("SELECT * FROM images WHERE image_id = ?", (image_id,))


def list_items() -> List[Dict[str, Any]]:
    return fetch_all("SELECT * FROM items ORDER BY name")


def get_item_by_name(name: str) -> Optional[Dict[str, Any]]:
    return fetch_one("SELECT * FROM items WHERE name = ?", (name,))


def insert_items(items: List[Dict[str, Any]]) -> None:
    execute_many(
        "INSERT INTO items(name, category, default_unit, shelf_life_days_default) VALUES (?, ?, ?, ?)",
        [
            (
                item["name"],
                item.get("category"),
                item.get("default_unit", "unit"),
                item.get("shelf_life_days_default"),
            )
            for item in items
        ],
    )


def insert_recipes(recipes: List[Dict[str, Any]]) -> None:
    execute_many(
        "INSERT INTO recipes(name, tags, allergens, steps, nutrition_json) VALUES (?, ?, ?, ?, ?)",
        [
            (
                recipe["name"],
                recipe.get("tags"),
                recipe.get("allergens"),
                recipe.get("steps"),
                to_json(recipe.get("nutrition") or {}),
            )
            for recipe in recipes
        ],
    )


def insert_recipe_ingredients(ingredients: List[Dict[str, Any]]) -> None:
    execute_many(
        "INSERT INTO recipe_ingredients(recipe_id, item_id, quantity, unit, optional) VALUES (?, ?, ?, ?, ?)",
        [
            (
                ing["recipe_id"],
                ing["item_id"],
                ing["quantity"],
                ing["unit"],
                1 if ing.get("optional") else 0,
            )
            for ing in ingredients
        ],
    )


def list_recipes() -> List[Dict[str, Any]]:
    return fetch_all("SELECT * FROM recipes ORDER BY recipe_id")


def list_recipe_ingredients() -> List[Dict[str, Any]]:
    return fetch_all("SELECT * FROM recipe_ingredients")


def insert_batch(batch: Dict[str, Any]) -> None:
    execute(
        """
        INSERT INTO inventory_batches(
            batch_id, item_id, item_name_snapshot, quantity, unit, purchase_date,
            expire_date, location, status, source_type, source_ref_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            batch["batch_id"],
            batch.get("item_id"),
            batch["item_name_snapshot"],
            batch["quantity"],
            batch["unit"],
            batch.get("purchase_date"),
            batch.get("expire_date"),
            batch.get("location"),
            batch.get("status", "in_stock"),
            batch.get("source_type"),
            batch.get("source_ref_id"),
            batch.get("created_at"),
            batch.get("updated_at"),
        ),
    )


def update_batch(batch_id: str, patch: Dict[str, Any]) -> None:
    fields = []
    values: List[Any] = []
    for key, value in patch.items():
        fields.append(f"{key} = ?")
        values.append(value)
    fields.append("updated_at = ?")
    values.append(now_ts())
    values.append(batch_id)
    query = f"UPDATE inventory_batches SET {', '.join(fields)} WHERE batch_id = ?"
    execute(query, values)


def list_batches(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    conditions = ["1=1"]
    values: List[Any] = []
    if filters.get("location"):
        conditions.append("location = ?")
        values.append(filters["location"])
    if filters.get("status"):
        conditions.append("status = ?")
        values.append(filters["status"])
    if filters.get("keyword"):
        conditions.append("item_name_snapshot LIKE ?")
        values.append(f"%{filters['keyword']}%")
    query = (
        "SELECT * FROM inventory_batches "
        f"WHERE {' AND '.join(conditions)} ORDER BY expire_date IS NULL, expire_date"
    )
    return fetch_all(query, values)


def get_batch(batch_id: str) -> Optional[Dict[str, Any]]:
    return fetch_one("SELECT * FROM inventory_batches WHERE batch_id = ?", (batch_id,))


def insert_event(event: Dict[str, Any]) -> None:
    execute(
        "INSERT INTO inventory_events(event_id, batch_id, event_type, delta_quantity, note, actor, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            event["event_id"],
            event["batch_id"],
            event["event_type"],
            event.get("delta_quantity"),
            event.get("note"),
            event.get("actor"),
            event["created_at"],
        ),
    )


def list_events(limit: int = 10) -> List[Dict[str, Any]]:
    return fetch_all(
        "SELECT * FROM inventory_events ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )


def list_batch_events(batch_id: str) -> List[Dict[str, Any]]:
    return fetch_all(
        "SELECT * FROM inventory_events WHERE batch_id = ? ORDER BY created_at DESC",
        (batch_id,),
    )


def list_expiring(days: int) -> List[Dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM inventory_batches
        WHERE status = 'in_stock' AND expire_date IS NOT NULL
        ORDER BY expire_date
        """
    )


def insert_menu_plan(menu_id: str, days: int, servings: int, constraints: Dict[str, Any]) -> None:
    execute(
        "INSERT INTO menu_plans(menu_id, days, servings, constraints_json, generated_at) VALUES (?, ?, ?, ?, ?)",
        (menu_id, days, servings, to_json(constraints), now_ts()),
    )


def insert_menu_plan_items(items: List[Dict[str, Any]]) -> None:
    execute_many(
        "INSERT INTO menu_plan_items(id, menu_id, date, meal_type, recipe_id, explain_json, nutrition_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                item["id"],
                item["menu_id"],
                item["date"],
                item["meal_type"],
                item["recipe_id"],
                to_json(item.get("explain") or []),
                to_json(item.get("nutrition") or {}),
            )
            for item in items
        ],
    )


def insert_shopping_items(items: List[Dict[str, Any]]) -> None:
    execute_many(
        "INSERT INTO shopping_list_items(id, menu_id, item_id, item_name_snapshot, need_qty, unit, reason_json, checked) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                item["id"],
                item["menu_id"],
                item.get("item_id"),
                item["item_name_snapshot"],
                item["need_qty"],
                item["unit"],
                to_json(item.get("reason") or {}),
                1 if item.get("checked") else 0,
            )
            for item in items
        ],
    )


def get_menu(menu_id: str) -> Optional[Dict[str, Any]]:
    plan = fetch_one("SELECT * FROM menu_plans WHERE menu_id = ?", (menu_id,))
    if not plan:
        return None
    plan["constraints"] = from_json(plan.get("constraints_json"), {})
    plan_items = fetch_all(
        "SELECT * FROM menu_plan_items WHERE menu_id = ? ORDER BY date, meal_type",
        (menu_id,),
    )
    for item in plan_items:
        item["explain"] = from_json(item.get("explain_json"), [])
        item["nutrition"] = from_json(item.get("nutrition_json"), {})
    plan["items"] = plan_items
    return plan


def list_shopping_items(menu_id: str) -> List[Dict[str, Any]]:
    items = fetch_all(
        "SELECT * FROM shopping_list_items WHERE menu_id = ? ORDER BY checked, item_name_snapshot",
        (menu_id,),
    )
    for item in items:
        item["checked"] = bool(item.get("checked"))
        item["reason"] = from_json(item.get("reason_json"), {})
    return items


def update_shopping_item_checked(item_id: str, checked: bool) -> Optional[Dict[str, Any]]:
    execute("UPDATE shopping_list_items SET checked = ? WHERE id = ?", (1 if checked else 0, item_id))
    return fetch_one("SELECT * FROM shopping_list_items WHERE id = ?", (item_id,))


def count_rows(table: str) -> int:
    row = fetch_one(f"SELECT COUNT(*) as count FROM {table}")
    return int(row["count"]) if row else 0
