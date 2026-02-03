from __future__ import annotations

import base64
import json
import os
import random
from typing import Any, Dict, List
import requests
from . import db
from .utils import add_days, format_date, stable_hash, today
from functools import lru_cache
from pathlib import Path
import zipfile

def _project_root() -> Path:
    """定位项目根目录：smart-fridge/ （lib/ 的上一层）"""
    return Path(__file__).resolve().parents[1]

def _resolve_to_abs(path_str: str) -> Path:
    """把相对路径按项目根目录转成绝对路径；绝对路径原样返回。"""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (_project_root() / p).resolve()

def _ensure_model_dir(model_ref: str) -> str:
    """
    自动识别 model_ref 是目录还是 zip：
    - 目录：返回绝对路径
    - zip：解压到 <project_root>/.cache/models/<zip_stem>/ 并返回该目录绝对路径
    """
    root = _project_root()
    cache_base = (root / ".cache" / "models")
    cache_base.mkdir(parents=True, exist_ok=True)

    p = _resolve_to_abs(model_ref)

    # 1) 目录：直接返回
    if p.exists() and p.is_dir():
        return str(p)

    # 2) zip：解压到 .cache/models/<stem>/
    #    - model_ref 可能是相对路径，也可能就是 zip 文件名
    is_zip = (p.suffix.lower() == ".zip") or (p.exists() and zipfile.is_zipfile(p))
    if is_zip:
        if not p.exists():
            raise ProviderNotAvailable("MODEL_NOT_FOUND", f"Model zip not found: {p}")

        out_dir = cache_base / p.stem
        marker = out_dir / ".extracted.ok"

        if not marker.exists():
            # 清理旧目录（可选）：避免残留
            out_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(p, "r") as z:
                z.extractall(out_dir)
            marker.write_text("ok", encoding="utf-8")

        # 有些 zip 会多套一层目录：比如 out_dir/owlvit-base-patch32/config.json
        # 这里做一次“向下探测”，找到真正包含 config.json 的目录
        if (out_dir / "config.json").exists():
            return str(out_dir)

        # 向下找一层
        for child in out_dir.iterdir():
            if child.is_dir() and (child / "config.json").exists():
                return str(child)

        # 找不到就返回 out_dir（至少不报错，方便你检查）
        return str(out_dir)

    # 3) 既不是目录也不是 zip：报错提示
    raise ProviderNotAvailable(
        "MODEL_NOT_FOUND",
        f"VISION_HF_MODEL must be a local dir or a zip file. Got: {p}",
    )

class ProviderNotAvailable(Exception):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


class BaseVisionProvider:
    id: str
    name: str

    def is_available(self) -> tuple[bool, str]:
        raise NotImplementedError

    def detect(self, image_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        raise NotImplementedError


class MockVisionProvider(BaseVisionProvider):
    id = "mock"
    name = "Mock (Offline)"

    def __init__(self) -> None:
        self.items = db.list_items()

    def is_available(self) -> tuple[bool, str]:
        return True, ""

    def detect(self, image_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.items:
            return []
        rng = random.Random(stable_hash(image_id))
        sample_size = min(top_k, max(6, min(10, len(self.items))))
        candidates = rng.sample(self.items, k=min(sample_size, len(self.items)))
        detections = []
        for item in candidates:
            confidence = round(rng.uniform(0.6, 0.95), 2)
            quantity = round(rng.uniform(1, 4), 1)
            shelf_life = item.get("shelf_life_days_default") or 5
            expire_date = format_date(add_days(today(), shelf_life))
            detections.append(
                {
                    "temp_id": f"det_{item['item_id']}_{stable_hash(image_id)}",
                    "item_id": item["item_id"],
                    "item_name": item["name"],
                    "confidence": confidence,
                    "quantity": quantity,
                    "unit": item.get("default_unit") or "unit",
                    "suggest_expire_date": expire_date,
                    "location": "fridge",
                }
            )
        return detections


class HttpVisionProvider(BaseVisionProvider):
    id = "http"
    name = "HTTP Vision (Generic)"

    def __init__(self) -> None:
        self.endpoint = os.getenv("VISION_HTTP_ENDPOINT")
        self.headers_json = os.getenv("VISION_HTTP_HEADERS_JSON", "")
        timeout = os.getenv("VISION_HTTP_TIMEOUT", "20")
        self.timeout = int(timeout) if timeout.isdigit() else 20

    def is_available(self) -> tuple[bool, str]:
        if not self.endpoint:
            return False, "VISION_HTTP_ENDPOINT is not configured"
        return True, ""

    def _headers(self) -> Dict[str, str]:
        if not self.headers_json:
            return {"Content-Type": "application/json"}
        try:
            headers = json.loads(self.headers_json)
            headers["Content-Type"] = "application/json"
            return headers
        except json.JSONDecodeError as exc:
            raise ProviderNotAvailable("PROVIDER_CONFIG_ERROR", f"Invalid VISION_HTTP_HEADERS_JSON: {exc}") from exc

    def detect(self, image_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        available, reason = self.is_available()
        if not available:
            raise ProviderNotAvailable("PROVIDER_NOT_AVAILABLE", reason)
        image = db.get_image(image_id)
        if not image:
            raise ProviderNotAvailable("IMAGE_NOT_FOUND", f"Image {image_id} not found")
        file_path = image.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise ProviderNotAvailable("IMAGE_NOT_FOUND", f"Image file missing for {image_id}")
        with open(file_path, "rb") as file_handle:
            image_base64 = base64.b64encode(file_handle.read()).decode("utf-8")
        payload = {"image_id": image_id, "image_base64": image_base64, "top_k": top_k}
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        detections = data.get("detections", [])
        items = {item["name"]: item for item in db.list_items()}
        normalized = []
        for idx, det in enumerate(detections):
            name = det.get("name") or det.get("item_name") or "未知"
            item = items.get(name)
            suggest_expire_date = det.get("suggest_expire_date")
            if not suggest_expire_date and det.get("suggest_expire_days") is not None:
                try:
                    days = int(det.get("suggest_expire_days"))
                    suggest_expire_date = format_date(add_days(today(), days))
                except (ValueError, TypeError):
                    suggest_expire_date = None
            normalized.append(
                {
                    "temp_id": det.get("temp_id") or f"det_http_{image_id}_{idx}",
                    "item_id": item["item_id"] if item else None,
                    "item_name": item["name"] if item else name,
                    "confidence": det.get("confidence", 0.0),
                    "quantity": det.get("quantity", 1),
                    "unit": det.get("unit") or (item.get("default_unit") if item else "unit"),
                    "suggest_expire_date": suggest_expire_date,
                    "location": det.get("location", "fridge"),
                }
            )
        return normalized




def get_provider(name: str) -> BaseVisionProvider:
    providers = list_providers()
    if name not in providers:
        raise ProviderNotAvailable("PROVIDER_NOT_FOUND", f"Provider '{name}' not registered")
    provider = providers[name]
    available, reason = provider.is_available()
    if not available:
        raise ProviderNotAvailable("PROVIDER_NOT_AVAILABLE", reason)
    return provider

# ✅ 全局缓存：避免 Streamlit 反复 rerun 时重复加载大模型
@lru_cache(maxsize=1)
def _get_hf_owlvit_pipeline(model_dir: str, device: int):
    """
    从本地目录加载（强制离线），并缓存 pipeline，避免 Streamlit rerun 重复加载。
    关键: OWL-ViT 需要 tokenizer + image_processor，不能只加载 image processor。
    """
    from transformers import (
        AutoTokenizer,
        AutoImageProcessor,
        OwlViTForObjectDetection,
        pipeline,
    )

    # ✅ 强制离线：只读本地文件
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    image_processor = AutoImageProcessor.from_pretrained(model_dir, local_files_only=True)
    model = OwlViTForObjectDetection.from_pretrained(model_dir, local_files_only=True)

    # ✅ 显式传 tokenizer / image_processor，避免 “guess tokenizer” 失败
    return pipeline(
        "zero-shot-object-detection",
        model=model,
        tokenizer=tokenizer,
        image_processor=image_processor,
        device=device,
    )



class HFOwlViTVisionProvider(BaseVisionProvider):
    id = "hf_owlvit"
    name = "HF OWL-ViT (Local)"

    def __init__(self) -> None:

        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        self.model_ref = os.getenv("VISION_HF_MODEL", "models/owlvit-base-patch32")
        self.device = int(os.getenv("VISION_HF_DEVICE", "-1"))        
        # 标签映射：解决“模型英文label vs 你DB中文食材名”的对齐问题
        # 例：{"apple":"苹果","tomato":"西红柿","egg":"鸡蛋"}
        self.label_map = {  "apple": "苹果",
                            "banana": "香蕉",
                            "tomato": "西红柿",
                            "egg": "鸡蛋",
                            "milk": "牛奶",
                            "orange": "橙子",
                            "cucumber": "黄瓜",
                            "carrot": "胡萝卜",
                            "bread": "面包",
                            "cheese": "奶酪",
                            "yogurt": "酸奶",
                            "chicken": "鸡肉",
                            "beef": "牛肉",
                            "pork": "猪肉",
                            "fish": "鱼",
                            "spring onion": "葱",
                            "garlic": "大蒜",
                            "ginger": "姜",
                            "potato": "土豆",
                            "onion": "洋葱",
                            "bell pepper": "甜椒",
                            "lettuce": "生菜"}
        raw = os.getenv("VISION_LABEL_MAP_JSON", "")
        if raw:
            try:
                self.label_map = json.loads(raw)
            except Exception:
                self.label_map = {}

        # 置信度阈值
        self.threshold = float(os.getenv("VISION_HF_THRESHOLD", "0.12"))

    def is_available(self) -> tuple[bool, str]:
        try:
            import transformers  # noqa: F401
            import PIL  # noqa: F401
        except Exception as exc:
            return False, f"Missing deps: {exc}"
        return True, ""

    def detect(self, image_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        image = db.get_image(image_id)
        if not image:
            raise ProviderNotAvailable("IMAGE_NOT_FOUND", f"Image {image_id} not found")

        file_path = image.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise ProviderNotAvailable("IMAGE_NOT_FOUND", f"Image file missing for {image_id}")

        from PIL import Image
        pil_img = Image.open(file_path).convert("RGB")

        # 1) 构造候选标签（给模型用）
        items = db.list_items()
        # 如果你提供了 label_map（英文->中文DB名），优先用英文key作为候选
        if self.label_map:
            candidate_labels = list(self.label_map.keys())
        else:
            # 没有 label_map 时，退化：直接用 DB 的 name（若是中文，效果可能一般）
            candidate_labels = [it["name"] for it in items]

        candidate_labels = candidate_labels[: max(5, min(60, len(candidate_labels)))]  # 控制长度避免太慢

        model_dir = _ensure_model_dir(self.model_ref)               # ✅ 自动识别目录/zip + 解压到 .cache/models/
        detector = _get_hf_owlvit_pipeline(model_dir, self.device)  # ✅ local_files_only 强制离线加载

        # 2) 跑检测（输出包含 label/score/box）
        # transformers 的 object detection pipeline 输出通常包含 score/label/box 字段
        raw = detector(pil_img, candidate_labels=candidate_labels, threshold=self.threshold)

        # 3) label -> item 映射 & 计数合并（用“同类框数量”估算 quantity）
        items_by_name = {it["name"]: it for it in items}
        # 若 label_map 存在：模型 label(英文) -> 你的 DB 中文名
        def map_label(lbl: str) -> str:
            return self.label_map.get(lbl, lbl)

        grouped: Dict[str, Dict[str, Any]] = {}
        for det in raw[: max(top_k * 3, 30)]:  # 先取更多，后面会合并
            lbl = det.get("label") or "未知"
            name = map_label(lbl)
            score = float(det.get("score", 0.0))

            entry = grouped.get(name)
            if not entry:
                item = items_by_name.get(name)
                shelf_life = (item.get("shelf_life_days_default") if item else None) or 5
                entry = {
                    "temp_id": f"det_hf_{image_id}_{name}",
                    "item_id": item["item_id"] if item else None,
                    "item_name": item["name"] if item else name,
                    "confidence_sum": 0.0,
                    "count": 0,
                    "unit": (item.get("default_unit") if item else None) or "unit",
                    "suggest_expire_date": format_date(add_days(today(), int(shelf_life))),
                    "location": "fridge",
                }
                grouped[name] = entry

            entry["confidence_sum"] += score
            entry["count"] += 1

        # 4) 输出标准化
        results = []
        for name, entry in grouped.items():
            avg_conf = entry["confidence_sum"] / max(1, entry["count"])
            results.append(
                {
                    "temp_id": entry["temp_id"],
                    "item_id": entry["item_id"],
                    "item_name": entry["item_name"],
                    "confidence": round(avg_conf, 3),
                    "quantity": float(entry["count"]),   # ✅ 黑客松阶段：数量=同类检测框数量
                    "unit": entry["unit"],
                    "suggest_expire_date": entry["suggest_expire_date"],
                    "location": entry["location"],
                }
            )

        # 按置信度排序，取 top_k
        results.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        return results[:top_k]


def list_providers() -> Dict[str, BaseVisionProvider]:
    return {
        MockVisionProvider.id: MockVisionProvider(),
        HttpVisionProvider.id: HttpVisionProvider(),
        HFOwlViTVisionProvider.id: HFOwlViTVisionProvider(),
    }
