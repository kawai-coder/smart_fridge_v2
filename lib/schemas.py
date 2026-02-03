from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Item:
    item_id: int
    name: str
    category: Optional[str]
    default_unit: str
    shelf_life_days_default: Optional[int]


@dataclass
class InventoryBatch:
    batch_id: str
    item_id: Optional[int]
    item_name_snapshot: str
    quantity: float
    unit: str
    purchase_date: Optional[str]
    expire_date: Optional[str]
    location: Optional[str]
    status: str
    source_type: Optional[str]
    source_ref_id: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class InventoryEvent:
    event_id: str
    batch_id: str
    event_type: str
    delta_quantity: Optional[float]
    note: Optional[str]
    actor: Optional[str]
    created_at: str


@dataclass
class Recipe:
    recipe_id: int
    name: str
    tags: Optional[str]
    allergens: Optional[str]
    steps: Optional[str]
    nutrition_json: Optional[str]


@dataclass
class RecipeIngredient:
    recipe_id: int
    item_id: int
    quantity: float
    unit: str
    optional: int


@dataclass
class MenuPlan:
    menu_id: str
    days: int
    servings: int
    constraints: Dict[str, Any]
    generated_at: str


@dataclass
class MenuPlanItem:
    id: str
    menu_id: str
    date: str
    meal_type: str
    recipe_id: int
    explain: List[str]
    nutrition: Optional[Dict[str, Any]]


@dataclass
class ShoppingListItem:
    id: str
    menu_id: str
    item_id: Optional[int]
    item_name_snapshot: str
    need_qty: float
    unit: str
    reason: Dict[str, Any]
    checked: bool
