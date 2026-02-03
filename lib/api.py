from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List

from . import db
from .utils import add_days, format_date, now_ts, parse_date, today
from .planner_provider import ProviderNotAvailable as PlannerNotAvailable
from .planner_provider import get_planner
from .vision_provider import ProviderNotAvailable, get_provider

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads"


def ensure_initialized() -> None:
    db.init_db()


def upload_image(file) -> Dict[str, str]:
    ensure_initialized()
    image_id = f"img_{uuid.uuid4().hex[:8]}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.name).suffix or ".jpg"
    file_path = UPLOAD_DIR / f"{image_id}{ext}"
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    db.upsert_image(image_id, str(file_path))
    return {"image_id": image_id, "image_path": str(file_path)}


def detect(image_id: str, provider: str = "mock", top_k: int = 12) -> Dict[str, Any]:
    ensure_initialized()
    reason = ""
    used_provider = provider
    degraded = False
    try:
        vision = get_provider(provider)
        detections = vision.detect(image_id=image_id, top_k=top_k)
    except ProviderNotAvailable as exc:
        reason = f"{exc.code}: {exc.reason}"
        degraded = True
        used_provider = "mock"
        vision = get_provider("mock")
        detections = vision.detect(image_id=image_id, top_k=top_k)
    except Exception as exc:  # noqa: BLE001
        reason = f"PROVIDER_ERROR: {exc}"
        degraded = True
        used_provider = "mock"
        vision = get_provider("mock")
        detections = vision.detect(image_id=image_id, top_k=top_k)
    return {
        "detections": detections,
        "meta": {
            "provider_requested": provider,
            "provider_used": used_provider,
            "degraded": degraded,
            "reason": reason,
        },
    }


def bulk_create_batches(source: Dict[str, Any], batches: List[Dict[str, Any]]) -> Dict[str, Any]:
    ensure_initialized()
    created = []
    for batch in batches:
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        payload = {
            "batch_id": batch_id,
            "item_id": batch.get("item_id"),
            "item_name_snapshot": batch.get("item_name") or batch.get("item_name_snapshot"),
            "quantity": float(batch.get("quantity", 1)),
            "unit": batch.get("unit") or "unit",
            "purchase_date": format_date(today()),
            "expire_date": batch.get("expire_date") or batch.get("suggest_expire_date"),
            "location": batch.get("location") or "fridge",
            "status": "in_stock",
            "source_type": source.get("type"),
            "source_ref_id": source.get("image_id"),
            "created_at": now_ts(),
            "updated_at": now_ts(),
        }
        db.insert_batch(payload)
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "batch_id": batch_id,
            "event_type": "create",
            "delta_quantity": payload["quantity"],
            "note": "入库创建",
            "actor": "system",
            "created_at": now_ts(),
        }
        db.insert_event(event)
        created.append(payload)
    return {"created": created}


def list_batches(filters: Dict[str, Any]) -> Dict[str, Any]:
    ensure_initialized()
    return {"batches": db.list_batches(filters)}


def update_batch(batch_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    ensure_initialized()
    db.update_batch(batch_id, patch)
    batch = db.get_batch(batch_id)
    if batch:
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "batch_id": batch_id,
            "event_type": "adjust",
            "delta_quantity": patch.get("quantity"),
            "note": "编辑批次信息",
            "actor": "user",
            "created_at": now_ts(),
        }
        db.insert_event(event)
    return batch or {}


def consume_batch(batch_id: str, delta_quantity: float, note: str = "") -> Dict[str, Any]:
    ensure_initialized()
    batch = db.get_batch(batch_id)
    if not batch:
        return {}
    new_qty = max(0.0, float(batch["quantity"]) - delta_quantity)
    patch = {"quantity": new_qty}
    if new_qty == 0:
        patch["status"] = "consumed"
    db.update_batch(batch_id, patch)
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "batch_id": batch_id,
        "event_type": "consume",
        "delta_quantity": -abs(delta_quantity),
        "note": note or "消耗库存",
        "actor": "user",
        "created_at": now_ts(),
    }
    db.insert_event(event)
    return event


def discard_batch(batch_id: str, delta_quantity: float, reason: str = "") -> Dict[str, Any]:
    ensure_initialized()
    batch = db.get_batch(batch_id)
    if not batch:
        return {}
    new_qty = max(0.0, float(batch["quantity"]) - delta_quantity)
    patch = {"quantity": new_qty}
    if new_qty == 0:
        patch["status"] = "discarded"
    db.update_batch(batch_id, patch)
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "batch_id": batch_id,
        "event_type": "discard",
        "delta_quantity": -abs(delta_quantity),
        "note": reason or "丢弃库存",
        "actor": "user",
        "created_at": now_ts(),
    }
    db.insert_event(event)
    return event


def list_events(limit: int = 10) -> Dict[str, Any]:
    ensure_initialized()
    return {"events": db.list_events(limit)}


def list_batch_events(batch_id: str) -> Dict[str, Any]:
    ensure_initialized()
    return {"events": db.list_batch_events(batch_id)}


def dashboard_summary() -> Dict[str, Any]:
    ensure_initialized()
    batches = db.list_batches({})
    in_stock = [b for b in batches if b["status"] == "in_stock"]
    expiring = 0
    for batch in in_stock:
        if batch.get("expire_date"):
            days_left = (parse_date(batch["expire_date"]) - today()).days
            if days_left <= 3:
                expiring += 1
    recipes = db.list_recipes()
    return {
        "kpi_expiring": expiring,
        "kpi_batches": len(in_stock),
        "kpi_recipes": len(recipes),
    }


def list_expiring(days: int = 3) -> Dict[str, Any]:
    ensure_initialized()
    batches = db.list_batches({"status": "in_stock"})
    upcoming = []
    for batch in batches:
        if batch.get("expire_date"):
            days_left = (parse_date(batch["expire_date"]) - today()).days
            if days_left <= days:
                batch = {**batch, "days_left": days_left}
                upcoming.append(batch)
    upcoming.sort(key=lambda x: x.get("days_left", 999))
    return {"batches": upcoming}


def generate_menu(
    days: int,
    servings: int,
    constraints: Dict[str, Any],
    planner: str = "greedy",
) -> Dict[str, Any]:
    ensure_initialized()
    reason = ""
    used_planner = planner
    degraded = False
    try:
        planner_provider = get_planner(planner)
        result = planner_provider.generate(days, servings, constraints)
    except PlannerNotAvailable as exc:
        reason = f"{exc.code}: {exc.reason}"
        degraded = True
        used_planner = "greedy"
        planner_provider = get_planner("greedy")
        result = planner_provider.generate(days, servings, constraints)
    except Exception as exc:  # noqa: BLE001
        reason = f"PLANNER_ERROR: {exc}"
        degraded = True
        used_planner = "greedy"
        planner_provider = get_planner("greedy")
        result = planner_provider.generate(days, servings, constraints)
    return {
        **result,
        "meta": {
            "planner_requested": planner,
            "planner_used": used_planner,
            "degraded": degraded,
            "reason": reason,
        },
    }


def get_menu(menu_id: str) -> Dict[str, Any]:
    ensure_initialized()
    menu = db.get_menu(menu_id)
    return menu or {}


def get_shopping_list(menu_id: str) -> Dict[str, Any]:
    ensure_initialized()
    return {"items": db.list_shopping_items(menu_id)}


def update_shopping_item_checked(item_id: str, checked: bool) -> Dict[str, Any]:
    ensure_initialized()
    item = db.update_shopping_item_checked(item_id, checked)
    return item or {}
