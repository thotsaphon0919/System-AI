from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field


_LOCK = threading.RLock()


class CommerceSettingsPatch(BaseModel):
    shop_name: str | None = None
    slug: str | None = None
    contact: str | None = None
    payment_note: str | None = None
    order_note: str | None = None
    shop_enabled: bool | None = None
    booking_enabled: bool | None = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    price: float = Field(default=0, ge=0, le=100000000)
    stock: int = Field(default=0, ge=0, le=100000000)
    image_url: str = Field(default="", max_length=1000)
    sheet_id: str = Field(default="", max_length=160)
    active: bool = True


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    price: float | None = Field(default=None, ge=0, le=100000000)
    stock: int | None = Field(default=None, ge=0, le=100000000)
    image_url: str | None = Field(default=None, max_length=1000)
    sheet_id: str | None = Field(default=None, max_length=160)
    active: bool | None = None


class OrderItemCreate(BaseModel):
    product_id: str = Field(min_length=1, max_length=160)
    qty: int = Field(ge=1, le=999)


class PublicOrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=3, max_length=80)
    note: str = Field(default="", max_length=2000)
    payment_method: str = Field(default="manual", max_length=80)
    items: list[OrderItemCreate]


class OrderPatch(BaseModel):
    status: str | None = None
    payment_status: str | None = None


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    price: float = Field(default=0, ge=0, le=100000000)
    duration_min: int = Field(default=60, ge=5, le=1440)
    available_note: str = Field(default="", max_length=500)
    image_url: str = Field(default="", max_length=1000)
    active: bool = True


class ServicePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    price: float | None = Field(default=None, ge=0, le=100000000)
    duration_min: int | None = Field(default=None, ge=5, le=1440)
    available_note: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=1000)
    active: bool | None = None


class PublicBookingCreate(BaseModel):
    service_id: str = Field(min_length=1, max_length=160)
    customer_name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=3, max_length=80)
    booking_date: str = Field(min_length=10, max_length=10)
    booking_time: str = Field(min_length=5, max_length=5)
    note: str = Field(default="", max_length=2000)


class BookingPatch(BaseModel):
    status: str


def _model_data(model: BaseModel, *, exclude_unset: bool = False) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=exclude_unset)  # type: ignore[attr-defined]
    return model.dict(exclude_unset=exclude_unset)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, limit: int = 500) -> str:
    return str(value or "").strip()[:limit]


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:60]


def _money(value: Any) -> float:
    try:
        number = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="ราคาไม่ถูกต้อง")
    if number < 0:
        raise HTTPException(status_code=400, detail="ราคาต้องไม่ติดลบ")
    return float(number)


def _public_product(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "name": item.get("name", ""),
        "description": item.get("description", ""),
        "price": item.get("price", 0),
        "stock": item.get("stock", 0),
        "image_url": item.get("image_url", ""),
        "sheet_id": item.get("sheet_id", ""),
        "sheet_url": item.get("sheet_url", ""),
        "active": bool(item.get("active", True)),
    }


def _public_service(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "name": item.get("name", ""),
        "description": item.get("description", ""),
        "price": item.get("price", 0),
        "duration_min": item.get("duration_min", 60),
        "available_note": item.get("available_note", ""),
        "image_url": item.get("image_url", ""),
        "active": bool(item.get("active", True)),
    }


def install_commerce_suite(
    app: FastAPI,
    *,
    base_dir: Path,
    current_user_id: Callable[[Request], str | None],
    load_json: Callable[[Path], Any],
    save_json: Callable[[Path, Any], None],
    sheets_file: Path,
) -> None:
    """Install INFINI Commerce Suite 2 routes into the 8032 app."""

    if getattr(app.state, "infini_commerce_suite_2_installed", False):
        return
    app.state.infini_commerce_suite_2_installed = True

    data_dir = Path(base_dir) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    settings_file = data_dir / "commerce_settings.json"
    products_file = data_dir / "commerce_products.json"
    orders_file = data_dir / "commerce_orders.json"
    services_file = data_dir / "commerce_services.json"
    bookings_file = data_dir / "commerce_bookings.json"

    for path in (settings_file, products_file, orders_file, services_file, bookings_file):
        if not path.exists():
            save_json(path, {})

    def owner_id(request: Request) -> str:
        uid = current_user_id(request)
        if not uid:
            raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")
        return uid

    def unique_default_slug(uid: str, all_settings: dict[str, Any]) -> str:
        base = _slug(f"shop-{uid[-8:]}") or f"shop-{uuid.uuid4().hex[:8]}"
        used = {str(v.get("slug", "")) for v in all_settings.values() if isinstance(v, dict)}
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        return slug

    def get_settings(uid: str, *, create: bool = True) -> dict[str, Any]:
        with _LOCK:
            all_settings = load_json(settings_file)
            if not isinstance(all_settings, dict):
                all_settings = {}
            item = all_settings.get(uid)
            if not isinstance(item, dict):
                item = {
                    "shop_name": "ร้านของฉัน",
                    "slug": unique_default_slug(uid, all_settings),
                    "contact": "",
                    "payment_note": "ร้านจะติดต่อกลับเพื่อแจ้งช่องทางชำระเงิน",
                    "order_note": "",
                    "shop_enabled": True,
                    "booking_enabled": True,
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                }
                if create:
                    all_settings[uid] = item
                    save_json(settings_file, all_settings)
            return dict(item)

    def resolve_store(slug: str) -> tuple[str, dict[str, Any]]:
        all_settings = load_json(settings_file)
        if not isinstance(all_settings, dict):
            raise HTTPException(status_code=404, detail="ไม่พบร้าน")
        for uid, item in all_settings.items():
            if isinstance(item, dict) and item.get("slug") == slug:
                return str(uid), dict(item)
        raise HTTPException(status_code=404, detail="ไม่พบร้าน")

    def owner_sheets(uid: str) -> list[dict[str, str]]:
        data = load_json(sheets_file)
        if not isinstance(data, dict):
            return []
        result = []
        for sheet in data.values():
            if isinstance(sheet, dict) and sheet.get("user_id") == uid:
                result.append({"id": str(sheet.get("id", "")), "title": str(sheet.get("title", "แผ่น"))})
        result.sort(key=lambda x: x["title"].lower())
        return result

    def list_owned(path: Path, uid: str, owner_key: str = "user_id") -> list[dict[str, Any]]:
        data = load_json(path)
        if not isinstance(data, dict):
            return []
        items = [dict(v) for v in data.values() if isinstance(v, dict) and v.get(owner_key) == uid]
        items.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return items

    @app.get("/commerce", response_class=HTMLResponse)
    async def commerce_dashboard(request: Request):
        if not current_user_id(request):
            return RedirectResponse("/login", status_code=303)
        return HTMLResponse(COMMERCE_DASHBOARD_HTML)

    @app.get("/store/{slug}", response_class=HTMLResponse)
    async def public_store_page(slug: str):
        resolve_store(slug)
        return HTMLResponse(PUBLIC_STORE_HTML.replace("__STORE_SLUG__", json.dumps(slug, ensure_ascii=False)))

    @app.get("/api/commerce/bootstrap")
    async def commerce_bootstrap(request: Request):
        uid = owner_id(request)
        settings = get_settings(uid)
        return {
            "settings": settings,
            "products": list_owned(products_file, uid),
            "orders": list_owned(orders_file, uid, "store_user_id"),
            "services": list_owned(services_file, uid),
            "bookings": list_owned(bookings_file, uid, "store_user_id"),
            "sheets": owner_sheets(uid),
            "public_url": f"/store/{settings['slug']}",
        }

    @app.patch("/api/commerce/settings")
    async def update_commerce_settings(request: Request, payload: CommerceSettingsPatch):
        uid = owner_id(request)
        patch = _model_data(payload, exclude_unset=True)
        with _LOCK:
            all_settings = load_json(settings_file)
            if not isinstance(all_settings, dict):
                all_settings = {}
            current = get_settings(uid)
            if "slug" in patch:
                clean = _slug(str(patch["slug"] or ""))
                if len(clean) < 3:
                    raise HTTPException(status_code=400, detail="ชื่อ URL ต้องมีอย่างน้อย 3 ตัว")
                for other_uid, item in all_settings.items():
                    if other_uid != uid and isinstance(item, dict) and item.get("slug") == clean:
                        raise HTTPException(status_code=409, detail="ชื่อ URL นี้ถูกใช้แล้ว")
                patch["slug"] = clean
            for key in ("shop_name", "contact", "payment_note", "order_note"):
                if key in patch:
                    patch[key] = _text(patch[key], 1000 if "note" in key else 200)
            current.update(patch)
            current["updated_at"] = _now_iso()
            all_settings[uid] = current
            save_json(settings_file, all_settings)
        return {"ok": True, "settings": current, "public_url": f"/store/{current['slug']}"}

    @app.post("/api/commerce/products")
    async def create_product(request: Request, payload: ProductCreate):
        uid = owner_id(request)
        data = _model_data(payload)
        product_id = f"prd_{uuid.uuid4().hex[:12]}"
        sheet_id = _text(data.get("sheet_id"), 160)
        if sheet_id and sheet_id not in {x["id"] for x in owner_sheets(uid)}:
            raise HTTPException(status_code=403, detail="แผ่นที่เลือกไม่ใช่ของบัญชีนี้")
        item = {
            "id": product_id,
            "user_id": uid,
            "name": _text(data.get("name"), 160),
            "description": _text(data.get("description"), 2000),
            "price": _money(data.get("price", 0)),
            "stock": int(data.get("stock", 0)),
            "image_url": _text(data.get("image_url"), 1000),
            "sheet_id": sheet_id,
            "sheet_url": f"/sheet/{sheet_id}" if sheet_id else "",
            "active": bool(data.get("active", True)),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        with _LOCK:
            products = load_json(products_file)
            if not isinstance(products, dict):
                products = {}
            products[product_id] = item
            save_json(products_file, products)
        return item

    @app.patch("/api/commerce/products/{product_id}")
    async def patch_product(request: Request, product_id: str, payload: ProductPatch):
        uid = owner_id(request)
        patch = _model_data(payload, exclude_unset=True)
        with _LOCK:
            products = load_json(products_file)
            item = products.get(product_id) if isinstance(products, dict) else None
            if not isinstance(item, dict):
                raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
            if item.get("user_id") != uid:
                raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์แก้สินค้า")
            if "sheet_id" in patch:
                sheet_id = _text(patch.get("sheet_id"), 160)
                if sheet_id and sheet_id not in {x["id"] for x in owner_sheets(uid)}:
                    raise HTTPException(status_code=403, detail="แผ่นที่เลือกไม่ใช่ของบัญชีนี้")
                patch["sheet_id"] = sheet_id
                patch["sheet_url"] = f"/sheet/{sheet_id}" if sheet_id else ""
            if "price" in patch:
                patch["price"] = _money(patch["price"])
            if "stock" in patch:
                patch["stock"] = int(patch["stock"])
            for key in ("name", "description", "image_url"):
                if key in patch:
                    patch[key] = _text(patch[key], 2000 if key == "description" else 1000)
            item.update(patch)
            item["updated_at"] = _now_iso()
            products[product_id] = item
            save_json(products_file, products)
        return item

    @app.delete("/api/commerce/products/{product_id}")
    async def delete_product(request: Request, product_id: str):
        uid = owner_id(request)
        with _LOCK:
            products = load_json(products_file)
            item = products.get(product_id) if isinstance(products, dict) else None
            if not isinstance(item, dict):
                raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
            if item.get("user_id") != uid:
                raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์ลบสินค้า")
            del products[product_id]
            save_json(products_file, products)
        return {"ok": True}

    @app.post("/api/commerce/services")
    async def create_service(request: Request, payload: ServiceCreate):
        uid = owner_id(request)
        data = _model_data(payload)
        service_id = f"svc_{uuid.uuid4().hex[:12]}"
        item = {
            "id": service_id,
            "user_id": uid,
            "name": _text(data.get("name"), 160),
            "description": _text(data.get("description"), 2000),
            "price": _money(data.get("price", 0)),
            "duration_min": int(data.get("duration_min", 60)),
            "available_note": _text(data.get("available_note"), 500),
            "image_url": _text(data.get("image_url"), 1000),
            "active": bool(data.get("active", True)),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        with _LOCK:
            services = load_json(services_file)
            if not isinstance(services, dict):
                services = {}
            services[service_id] = item
            save_json(services_file, services)
        return item

    @app.patch("/api/commerce/services/{service_id}")
    async def patch_service(request: Request, service_id: str, payload: ServicePatch):
        uid = owner_id(request)
        patch = _model_data(payload, exclude_unset=True)
        with _LOCK:
            services = load_json(services_file)
            item = services.get(service_id) if isinstance(services, dict) else None
            if not isinstance(item, dict):
                raise HTTPException(status_code=404, detail="ไม่พบบริการ")
            if item.get("user_id") != uid:
                raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์แก้บริการ")
            if "price" in patch:
                patch["price"] = _money(patch["price"])
            if "duration_min" in patch:
                patch["duration_min"] = int(patch["duration_min"])
            for key in ("name", "description", "available_note", "image_url"):
                if key in patch:
                    patch[key] = _text(patch[key], 2000 if key == "description" else 1000)
            item.update(patch)
            item["updated_at"] = _now_iso()
            services[service_id] = item
            save_json(services_file, services)
        return item

    @app.delete("/api/commerce/services/{service_id}")
    async def delete_service(request: Request, service_id: str):
        uid = owner_id(request)
        with _LOCK:
            services = load_json(services_file)
            item = services.get(service_id) if isinstance(services, dict) else None
            if not isinstance(item, dict):
                raise HTTPException(status_code=404, detail="ไม่พบบริการ")
            if item.get("user_id") != uid:
                raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์ลบบริการ")
            del services[service_id]
            save_json(services_file, services)
        return {"ok": True}

    @app.get("/api/public/store/{slug}")
    async def public_store_data(slug: str):
        uid, settings = resolve_store(slug)
        if not settings.get("shop_enabled") and not settings.get("booking_enabled"):
            raise HTTPException(status_code=404, detail="ร้านยังไม่เปิด")
        products = [
            _public_product(item)
            for item in list_owned(products_file, uid)
            if item.get("active", True) and int(item.get("stock", 0)) > 0
        ]
        services = [
            _public_service(item)
            for item in list_owned(services_file, uid)
            if item.get("active", True)
        ]
        return {
            "settings": {
                "shop_name": settings.get("shop_name", "ร้านของฉัน"),
                "contact": settings.get("contact", ""),
                "order_note": settings.get("order_note", ""),
                "shop_enabled": bool(settings.get("shop_enabled", True)),
                "booking_enabled": bool(settings.get("booking_enabled", True)),
            },
            "products": products,
            "services": services,
        }

    @app.post("/api/public/store/{slug}/orders")
    async def create_public_order(slug: str, payload: PublicOrderCreate):
        uid, settings = resolve_store(slug)
        if not settings.get("shop_enabled", True):
            raise HTTPException(status_code=403, detail="ร้านยังไม่เปิดรับออเดอร์")
        data = _model_data(payload)
        if not data.get("items"):
            raise HTTPException(status_code=400, detail="กรุณาเลือกสินค้า")
        with _LOCK:
            products = load_json(products_file)
            if not isinstance(products, dict):
                products = {}
            lines: list[dict[str, Any]] = []
            total = Decimal("0")
            for raw in data["items"]:
                row = raw if isinstance(raw, dict) else _model_data(raw)
                product_id = str(row.get("product_id", ""))
                qty = int(row.get("qty", 0))
                item = products.get(product_id)
                if not isinstance(item, dict) or item.get("user_id") != uid or not item.get("active", True):
                    raise HTTPException(status_code=404, detail="มีสินค้าที่ไม่พบหรือปิดขายแล้ว")
                stock = int(item.get("stock", 0))
                if qty < 1 or qty > stock:
                    raise HTTPException(status_code=409, detail=f"สต็อก {item.get('name', 'สินค้า')} ไม่เพียงพอ")
                price = Decimal(str(item.get("price", 0)))
                subtotal = (price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total += subtotal
                lines.append({
                    "product_id": product_id,
                    "name": item.get("name", "สินค้า"),
                    "price": float(price),
                    "qty": qty,
                    "subtotal": float(subtotal),
                })
            for line in lines:
                products[line["product_id"]]["stock"] = int(products[line["product_id"]].get("stock", 0)) - line["qty"]
                products[line["product_id"]]["updated_at"] = _now_iso()
            order_id = f"ord_{uuid.uuid4().hex[:12]}"
            order = {
                "id": order_id,
                "store_user_id": uid,
                "customer_name": _text(data.get("customer_name"), 160),
                "phone": _text(data.get("phone"), 80),
                "note": _text(data.get("note"), 2000),
                "payment_method": _text(data.get("payment_method"), 80) or "manual",
                "items": lines,
                "total": float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "status": "pending",
                "payment_status": "unpaid",
                "stock_reserved": True,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            orders = load_json(orders_file)
            if not isinstance(orders, dict):
                orders = {}
            orders[order_id] = order
            save_json(products_file, products)
            save_json(orders_file, orders)
        return {
            "ok": True,
            "order_id": order_id,
            "total": order["total"],
            "payment_note": settings.get("payment_note", "ร้านจะติดต่อกลับเพื่อแจ้งช่องทางชำระเงิน"),
        }

    @app.patch("/api/commerce/orders/{order_id}")
    async def patch_order(request: Request, order_id: str, payload: OrderPatch):
        uid = owner_id(request)
        patch = _model_data(payload, exclude_unset=True)
        allowed_status = {"pending", "confirmed", "paid", "shipped", "completed", "cancelled"}
        allowed_payment = {"unpaid", "paid", "refunded"}
        with _LOCK:
            orders = load_json(orders_file)
            order = orders.get(order_id) if isinstance(orders, dict) else None
            if not isinstance(order, dict):
                raise HTTPException(status_code=404, detail="ไม่พบออเดอร์")
            if order.get("store_user_id") != uid:
                raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์แก้ออเดอร์")
            old_status = str(order.get("status", "pending"))
            new_status = str(patch.get("status", old_status))
            if new_status not in allowed_status:
                raise HTTPException(status_code=400, detail="สถานะออเดอร์ไม่ถูกต้อง")
            if "payment_status" in patch and patch["payment_status"] not in allowed_payment:
                raise HTTPException(status_code=400, detail="สถานะชำระเงินไม่ถูกต้อง")
            products = load_json(products_file)
            if not isinstance(products, dict):
                products = {}
            if old_status != "cancelled" and new_status == "cancelled" and order.get("stock_reserved", True):
                for line in order.get("items", []):
                    item = products.get(line.get("product_id"))
                    if isinstance(item, dict) and item.get("user_id") == uid:
                        item["stock"] = int(item.get("stock", 0)) + int(line.get("qty", 0))
                        item["updated_at"] = _now_iso()
                order["stock_reserved"] = False
                save_json(products_file, products)
            elif old_status == "cancelled" and new_status != "cancelled" and not order.get("stock_reserved", False):
                for line in order.get("items", []):
                    item = products.get(line.get("product_id"))
                    if not isinstance(item, dict) or int(item.get("stock", 0)) < int(line.get("qty", 0)):
                        raise HTTPException(status_code=409, detail="สต็อกไม่พอสำหรับเปิดออเดอร์นี้อีกครั้ง")
                for line in order.get("items", []):
                    item = products[line.get("product_id")]
                    item["stock"] = int(item.get("stock", 0)) - int(line.get("qty", 0))
                    item["updated_at"] = _now_iso()
                order["stock_reserved"] = True
                save_json(products_file, products)
            order["status"] = new_status
            if "payment_status" in patch:
                order["payment_status"] = patch["payment_status"]
            order["updated_at"] = _now_iso()
            orders[order_id] = order
            save_json(orders_file, orders)
        return order

    @app.post("/api/public/store/{slug}/bookings")
    async def create_public_booking(slug: str, payload: PublicBookingCreate):
        uid, settings = resolve_store(slug)
        if not settings.get("booking_enabled", True):
            raise HTTPException(status_code=403, detail="ร้านยังไม่เปิดรับจอง")
        data = _model_data(payload)
        try:
            booking_day = date.fromisoformat(str(data.get("booking_date")))
        except ValueError:
            raise HTTPException(status_code=400, detail="วันที่ไม่ถูกต้อง")
        if booking_day < date.today():
            raise HTTPException(status_code=400, detail="ไม่สามารถจองวันที่ผ่านมาแล้ว")
        booking_time = str(data.get("booking_time", ""))
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", booking_time):
            raise HTTPException(status_code=400, detail="เวลาไม่ถูกต้อง")
        with _LOCK:
            services = load_json(services_file)
            service = services.get(data.get("service_id")) if isinstance(services, dict) else None
            if not isinstance(service, dict) or service.get("user_id") != uid or not service.get("active", True):
                raise HTTPException(status_code=404, detail="ไม่พบบริการ")
            bookings = load_json(bookings_file)
            if not isinstance(bookings, dict):
                bookings = {}
            for old in bookings.values():
                if not isinstance(old, dict):
                    continue
                if (
                    old.get("store_user_id") == uid
                    and old.get("service_id") == service.get("id")
                    and old.get("booking_date") == str(booking_day)
                    and old.get("booking_time") == booking_time
                    and old.get("status") not in {"cancelled", "rejected"}
                ):
                    raise HTTPException(status_code=409, detail="ช่วงเวลานี้มีการจองแล้ว")
            booking_id = f"bkg_{uuid.uuid4().hex[:12]}"
            booking = {
                "id": booking_id,
                "store_user_id": uid,
                "service_id": service.get("id"),
                "service_name": service.get("name", "บริการ"),
                "price": service.get("price", 0),
                "duration_min": service.get("duration_min", 60),
                "customer_name": _text(data.get("customer_name"), 160),
                "phone": _text(data.get("phone"), 80),
                "booking_date": str(booking_day),
                "booking_time": booking_time,
                "note": _text(data.get("note"), 2000),
                "status": "pending",
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            bookings[booking_id] = booking
            save_json(bookings_file, bookings)
        return {"ok": True, "booking_id": booking_id}

    @app.patch("/api/commerce/bookings/{booking_id}")
    async def patch_booking(request: Request, booking_id: str, payload: BookingPatch):
        uid = owner_id(request)
        allowed = {"pending", "confirmed", "completed", "cancelled", "rejected"}
        if payload.status not in allowed:
            raise HTTPException(status_code=400, detail="สถานะการจองไม่ถูกต้อง")
        with _LOCK:
            bookings = load_json(bookings_file)
            booking = bookings.get(booking_id) if isinstance(bookings, dict) else None
            if not isinstance(booking, dict):
                raise HTTPException(status_code=404, detail="ไม่พบรายการจอง")
            if booking.get("store_user_id") != uid:
                raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์แก้รายการจอง")
            booking["status"] = payload.status
            booking["updated_at"] = _now_iso()
            bookings[booking_id] = booking
            save_json(bookings_file, bookings)
        return booking

    @app.get("/api/commerce/export")
    async def export_commerce_data(request: Request):
        uid = owner_id(request)
        settings = get_settings(uid)
        payload = {
            "format": "INFINI_COMMERCE_SUITE_2",
            "exported_at": _now_iso(),
            "settings": settings,
            "products": list_owned(products_file, uid),
            "orders": list_owned(orders_file, uid, "store_user_id"),
            "services": list_owned(services_file, uid),
            "bookings": list_owned(bookings_file, uid, "store_user_id"),
        }
        response = JSONResponse(payload)
        response.headers["Content-Disposition"] = f'attachment; filename="infini-commerce-{settings["slug"]}.json"'
        return response


COMMERCE_DASHBOARD_HTML = r'''<!doctype html>
<html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>INFINI Commerce Suite 2</title>
<style>
:root{--bg:#030915;--card:#091528;--line:#184568;--text:#f3f8ff;--muted:#9fb4c8;--accent:#52d5ff;--good:#7df5aa;--warn:#ffd36b}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 50% -10%,#153b61 0,#030915 42%);color:var(--text);font-family:Arial,"Noto Sans Thai",sans-serif;min-height:100vh}
a{color:inherit}.wrap{max-width:980px;margin:auto;padding:16px 14px 90px}.top{display:flex;align-items:center;gap:10px;justify-content:space-between;margin-bottom:14px}.top h1{font-size:21px;margin:0}.top small{color:var(--muted)}.btn{border:1px solid #2673a5;background:#0c2942;color:#fff;border-radius:14px;padding:11px 14px;font-weight:800;cursor:pointer}.btn.primary{background:linear-gradient(100deg,#24c8ff,#7a68ff);border:0;color:#04111e}.btn.danger{border-color:#7b3040;background:#371824}.btn.good{border-color:#26794a;background:#123b2a}.tabs{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;position:sticky;top:0;z-index:5;background:rgba(3,9,21,.94);padding:8px 0}.tab{padding:10px 4px;border:1px solid var(--line);border-radius:12px;background:#071426;color:#cfe8ff;font-weight:800;font-size:12px}.tab.on{background:#123b5e;border-color:#4bcfff}.panel{display:none}.panel.on{display:block}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.stat,.card{background:linear-gradient(155deg,#0b1b31,#07111f);border:1px solid var(--line);border-radius:18px;padding:14px;margin:10px 0}.stat b{display:block;font-size:25px;margin-top:6px}.muted{color:var(--muted);font-size:13px}.row{display:grid;grid-template-columns:1fr 1fr;gap:9px}.field{margin:9px 0}label{display:block;font-size:13px;color:#bcd0df;margin:0 0 5px}input,textarea,select{width:100%;border:1px solid #235a82;border-radius:13px;background:#06101d;color:#fff;padding:12px;font-size:15px}textarea{min-height:78px;resize:vertical}.actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.item{border-top:1px solid #163a58;padding:12px 0}.item:first-child{border-top:0}.price{font-weight:900;color:#8fe9ff}.badge{display:inline-block;border:1px solid #2b6388;border-radius:99px;padding:3px 8px;font-size:11px;color:#cae9ff}.empty{text-align:center;color:var(--muted);padding:24px}.linkbox{display:flex;gap:7px}.linkbox input{flex:1}.notice{background:#2b230c;border:1px solid #795f18;color:#ffe6a0;border-radius:14px;padding:11px;margin:10px 0;font-size:13px}@media(min-width:760px){.grid{grid-template-columns:repeat(4,1fr)}.cols{display:grid;grid-template-columns:1fr 1.35fr;gap:14px}.tabs .tab{font-size:14px}}
</style></head><body><div class="wrap">
<div class="top"><div><h1>🛒 Commerce Suite 2</h1><small>ร้านค้า ออเดอร์ สต็อก และระบบจองของ 8032</small></div><a class="btn" href="http://127.0.0.1:7000/id">ID Home</a></div>
<div class="tabs"><button class="tab on" data-tab="home">ภาพรวม</button><button class="tab" data-tab="products">สินค้า</button><button class="tab" data-tab="orders">ออเดอร์</button><button class="tab" data-tab="booking">จอง</button><button class="tab" data-tab="settings">ตั้งค่า</button></div>
<section id="home" class="panel on"><div class="grid" id="stats"></div><div class="card"><b>ลิงก์หน้าร้าน</b><div class="linkbox"><input id="publicUrl" readonly><button class="btn" onclick="copyPublic()">คัดลอก</button><button class="btn primary" onclick="openPublic()">เปิด</button></div></div><div class="notice">ระบบนี้รับออเดอร์และบันทึกสถานะได้จริง แต่ยังไม่ตัดเงินจริงอัตโนมัติ เจ้าของร้านเป็นคนตรวจและกดสถานะชำระเงินเอง</div></section>
<section id="products" class="panel"><div class="cols"><div class="card"><h3>เพิ่มสินค้า</h3><form id="productForm"><div class="field"><label>ชื่อสินค้า</label><input name="name" required></div><div class="row"><div class="field"><label>ราคา</label><input name="price" type="number" min="0" step="0.01" value="0"></div><div class="field"><label>สต็อก</label><input name="stock" type="number" min="0" value="1"></div></div><div class="field"><label>รูปสินค้า (URL)</label><input name="image_url" placeholder="/uploads/... หรือ https://..."></div><div class="field"><label>เชื่อมไปยังแผ่น</label><select name="sheet_id" id="productSheet"><option value="">ไม่เชื่อมแผ่น</option></select></div><div class="field"><label>รายละเอียด</label><textarea name="description"></textarea></div><button class="btn primary" type="submit">บันทึกสินค้า</button></form></div><div class="card"><h3>สินค้าของฉัน</h3><div id="productList"></div></div></div></section>
<section id="orders" class="panel"><div class="card"><h3>รายการสั่งซื้อ</h3><div id="orderList"></div></div></section>
<section id="booking" class="panel"><div class="cols"><div class="card"><h3>เพิ่มบริการรับจอง</h3><form id="serviceForm"><div class="field"><label>ชื่อบริการ</label><input name="name" required></div><div class="row"><div class="field"><label>ราคา</label><input name="price" type="number" min="0" step="0.01" value="0"></div><div class="field"><label>ระยะเวลา (นาที)</label><input name="duration_min" type="number" min="5" value="60"></div></div><div class="field"><label>เวลาที่เปิดรับ</label><input name="available_note" placeholder="เช่น ทุกวัน 09:00–18:00"></div><div class="field"><label>รูปบริการ (URL)</label><input name="image_url"></div><div class="field"><label>รายละเอียด</label><textarea name="description"></textarea></div><button class="btn primary" type="submit">บันทึกบริการ</button></form><h3>บริการ</h3><div id="serviceList"></div></div><div class="card"><h3>รายการจอง</h3><div id="bookingList"></div></div></div></section>
<section id="settings" class="panel"><div class="card"><h3>ตั้งค่าหน้าร้าน</h3><form id="settingsForm"><div class="field"><label>ชื่อร้าน</label><input name="shop_name"></div><div class="field"><label>ชื่อ URL ร้าน</label><input name="slug" pattern="[a-z0-9-]+"></div><div class="field"><label>ช่องทางติดต่อ</label><input name="contact"></div><div class="field"><label>ข้อความชำระเงิน</label><textarea name="payment_note"></textarea></div><div class="field"><label>ประกาศหน้าร้าน</label><textarea name="order_note"></textarea></div><label><input style="width:auto" name="shop_enabled" type="checkbox"> เปิดรับออเดอร์</label><br><label><input style="width:auto" name="booking_enabled" type="checkbox"> เปิดรับจอง</label><div class="actions"><button class="btn primary" type="submit">บันทึกตั้งค่า</button><a class="btn" href="/api/commerce/export">สำรองข้อมูล JSON</a></div></form></div></section>
</div><script>
let S={settings:{},products:[],orders:[],services:[],bookings:[],sheets:[],public_url:''};const $=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));const money=n=>Number(n||0).toLocaleString('th-TH',{minimumFractionDigits:0,maximumFractionDigits:2})+' บาท';
async function api(url,opt={}){const r=await fetch(url,{headers:{'Content-Type':'application/json',...(opt.headers||{})},...opt});let d={};try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.detail||'เกิดข้อผิดพลาด');return d}
function setTab(name){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x.dataset.tab===name));document.querySelectorAll('.panel').forEach(x=>x.classList.toggle('on',x.id===name))}document.querySelectorAll('.tab').forEach(x=>x.onclick=()=>setTab(x.dataset.tab));
async function load(){S=await api('/api/commerce/bootstrap');render()}
function render(){const openOrders=S.orders.filter(x=>!['completed','cancelled'].includes(x.status)).length;const openBook=S.bookings.filter(x=>!['completed','cancelled','rejected'].includes(x.status)).length;$('stats').innerHTML=[[S.products.length,'สินค้า'],[openOrders,'ออเดอร์เปิด'],[S.services.length,'บริการ'],[openBook,'รายการจอง']].map(x=>`<div class="stat"><span class="muted">${x[1]}</span><b>${x[0]}</b></div>`).join('');$('publicUrl').value=location.origin+S.public_url;$('productSheet').innerHTML='<option value="">ไม่เชื่อมแผ่น</option>'+S.sheets.map(x=>`<option value="${esc(x.id)}">${esc(x.title)}</option>`).join('');renderProducts();renderOrders();renderServices();renderBookings();fillSettings()}
function renderProducts(){$('productList').innerHTML=S.products.length?S.products.map(x=>`<div class="item"><b>${esc(x.name)}</b> <span class="badge">สต็อก ${x.stock}</span><div class="price">${money(x.price)}</div><div class="muted">${esc(x.description||'')}</div><div class="actions"><button class="btn" onclick="editProduct('${x.id}')">แก้</button><button class="btn danger" onclick="delProduct('${x.id}')">ลบ</button>${x.sheet_url?`<a class="btn" href="${esc(x.sheet_url)}">เปิดแผ่น</a>`:''}</div></div>`).join(''):'<div class="empty">ยังไม่มีสินค้า</div>'}
function renderOrders(){$('orderList').innerHTML=S.orders.length?S.orders.map(x=>`<div class="item"><b>${esc(x.id)}</b> <span class="badge">${esc(x.status)}</span> <span class="badge">${esc(x.payment_status)}</span><div>${esc(x.customer_name)} · ${esc(x.phone)}</div><div class="price">${money(x.total)}</div><div class="muted">${x.items.map(i=>`${esc(i.name)} × ${i.qty}`).join(', ')}</div><div class="actions"><button class="btn good" onclick="orderStatus('${x.id}','confirmed')">ยืนยัน</button><button class="btn" onclick="orderStatus('${x.id}','shipped')">จัดส่ง</button><button class="btn" onclick="orderStatus('${x.id}','completed')">สำเร็จ</button><button class="btn primary" onclick="payStatus('${x.id}','paid')">ชำระแล้ว</button><button class="btn danger" onclick="orderStatus('${x.id}','cancelled')">ยกเลิก</button></div></div>`).join(''):'<div class="empty">ยังไม่มีออเดอร์</div>'}
function renderServices(){$('serviceList').innerHTML=S.services.length?S.services.map(x=>`<div class="item"><b>${esc(x.name)}</b><div class="price">${money(x.price)}</div><div class="muted">${x.duration_min} นาที · ${esc(x.available_note||'')}</div><div class="actions"><button class="btn" onclick="editService('${x.id}')">แก้</button><button class="btn danger" onclick="delService('${x.id}')">ลบ</button></div></div>`).join(''):'<div class="empty">ยังไม่มีบริการ</div>'}
function renderBookings(){$('bookingList').innerHTML=S.bookings.length?S.bookings.map(x=>`<div class="item"><b>${esc(x.service_name)}</b> <span class="badge">${esc(x.status)}</span><div>${esc(x.booking_date)} เวลา ${esc(x.booking_time)}</div><div>${esc(x.customer_name)} · ${esc(x.phone)}</div><div class="muted">${esc(x.note||'')}</div><div class="actions"><button class="btn good" onclick="bookingStatus('${x.id}','confirmed')">ยืนยัน</button><button class="btn" onclick="bookingStatus('${x.id}','completed')">เสร็จแล้ว</button><button class="btn danger" onclick="bookingStatus('${x.id}','rejected')">ปฏิเสธ</button></div></div>`).join(''):'<div class="empty">ยังไม่มีรายการจอง</div>'}
function fillSettings(){const f=$('settingsForm');for(const k of ['shop_name','slug','contact','payment_note','order_note'])f.elements[k].value=S.settings[k]||'';f.elements.shop_enabled.checked=!!S.settings.shop_enabled;f.elements.booking_enabled.checked=!!S.settings.booking_enabled}
$('productForm').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/commerce/products',{method:'POST',body:JSON.stringify({name:f.get('name'),price:Number(f.get('price')),stock:Number(f.get('stock')),image_url:f.get('image_url'),sheet_id:f.get('sheet_id'),description:f.get('description'),active:true})});e.target.reset();await load()}catch(err){alert(err.message)}};
$('serviceForm').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/commerce/services',{method:'POST',body:JSON.stringify({name:f.get('name'),price:Number(f.get('price')),duration_min:Number(f.get('duration_min')),available_note:f.get('available_note'),image_url:f.get('image_url'),description:f.get('description'),active:true})});e.target.reset();await load()}catch(err){alert(err.message)}};
$('settingsForm').onsubmit=async e=>{e.preventDefault();const f=e.target;try{await api('/api/commerce/settings',{method:'PATCH',body:JSON.stringify({shop_name:f.shop_name.value,slug:f.slug.value,contact:f.contact.value,payment_note:f.payment_note.value,order_note:f.order_note.value,shop_enabled:f.shop_enabled.checked,booking_enabled:f.booking_enabled.checked})});await load();alert('บันทึกแล้ว')}catch(err){alert(err.message)}};
async function delProduct(id){if(confirm('ลบสินค้านี้?')){await api('/api/commerce/products/'+id,{method:'DELETE'});await load()}}async function delService(id){if(confirm('ลบบริการนี้?')){await api('/api/commerce/services/'+id,{method:'DELETE'});await load()}}
async function editProduct(id){const x=S.products.find(v=>v.id===id);const name=prompt('ชื่อสินค้า',x.name);if(name===null)return;const price=prompt('ราคา',x.price);if(price===null)return;const stock=prompt('สต็อก',x.stock);if(stock===null)return;await api('/api/commerce/products/'+id,{method:'PATCH',body:JSON.stringify({name,price:Number(price),stock:Number(stock)})});await load()}
async function editService(id){const x=S.services.find(v=>v.id===id);const name=prompt('ชื่อบริการ',x.name);if(name===null)return;const price=prompt('ราคา',x.price);if(price===null)return;await api('/api/commerce/services/'+id,{method:'PATCH',body:JSON.stringify({name,price:Number(price)})});await load()}
async function orderStatus(id,status){try{await api('/api/commerce/orders/'+id,{method:'PATCH',body:JSON.stringify({status})});await load()}catch(e){alert(e.message)}}async function payStatus(id,payment_status){await api('/api/commerce/orders/'+id,{method:'PATCH',body:JSON.stringify({payment_status})});await load()}async function bookingStatus(id,status){await api('/api/commerce/bookings/'+id,{method:'PATCH',body:JSON.stringify({status})});await load()}
function copyPublic(){navigator.clipboard?.writeText($('publicUrl').value);alert('คัดลอกลิงก์แล้ว')}function openPublic(){location.href=S.public_url}load().catch(e=>alert(e.message));
</script></body></html>'''


PUBLIC_STORE_HTML = r'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><title>INFINI Store</title><style>
:root{--bg:#030914;--card:#0a1729;--line:#1b4d70;--text:#f5f9ff;--muted:#a8bbcc;--accent:#4bd8ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 50% -10%,#194668,#030914 45%);color:var(--text);font-family:Arial,"Noto Sans Thai",sans-serif}.wrap{max-width:820px;margin:auto;padding:18px 14px 100px}.hero{padding:24px 8px}.hero h1{margin:0 0 7px;font-size:29px}.muted{color:var(--muted)}.tabs{display:flex;gap:8px;margin:8px 0 15px}.tab,.btn{border:1px solid #2a678e;border-radius:14px;background:#0b253c;color:#fff;padding:11px 14px;font-weight:800}.tab.on,.btn.primary{background:linear-gradient(90deg,#25c7ff,#795cff);border:0;color:#03101b}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:11px}.card{background:linear-gradient(150deg,#0c1d32,#07111f);border:1px solid var(--line);border-radius:18px;padding:12px}.card img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:13px;background:#0e2135}.price{font-weight:900;color:#8ceaff;margin:6px 0}.panel{display:none}.panel.on{display:block}.cart{position:fixed;left:0;right:0;bottom:0;background:#071524;border-top:1px solid #2b6a90;padding:10px 14px;z-index:10}.cartinner{max-width:820px;margin:auto;display:flex;gap:8px;align-items:center;justify-content:space-between}.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:20;padding:18px;overflow:auto}.modal.on{display:block}.box{max-width:620px;margin:30px auto;background:#09182a;border:1px solid #2b658b;border-radius:20px;padding:16px}.field{margin:9px 0}label{display:block;font-size:13px;color:#bfd2df;margin-bottom:5px}input,textarea,select{width:100%;padding:12px;border-radius:12px;border:1px solid #286080;background:#06101d;color:#fff}textarea{min-height:76px}.item{padding:10px 0;border-top:1px solid #173d59}.actions{display:flex;gap:7px;flex-wrap:wrap}.empty{text-align:center;color:var(--muted);padding:35px}@media(min-width:720px){.grid{grid-template-columns:repeat(3,1fr)}}
</style></head><body><div class="wrap"><div class="hero"><div class="muted">INFINI COMMERCE SUITE 2</div><h1 id="shopName">กำลังเปิดร้าน…</h1><div id="contact" class="muted"></div><p id="notice"></p></div><div class="tabs"><button class="tab on" data-tab="shop">สินค้า</button><button class="tab" data-tab="booking">จองบริการ</button></div><section id="shop" class="panel on"><div id="productGrid" class="grid"></div></section><section id="booking" class="panel"><div id="serviceGrid" class="grid"></div></section></div><div class="cart"><div class="cartinner"><div><b id="cartCount">ตะกร้า 0 ชิ้น</b><div id="cartTotal" class="muted">0 บาท</div></div><button class="btn primary" onclick="openCart()">ดูตะกร้า / สั่งซื้อ</button></div></div>
<div id="cartModal" class="modal"><div class="box"><div class="actions" style="justify-content:space-between"><h3>ตะกร้าสินค้า</h3><button class="btn" onclick="closeModal('cartModal')">ปิด</button></div><div id="cartItems"></div><form id="orderForm"><div class="field"><label>ชื่อผู้สั่ง</label><input name="customer_name" required></div><div class="field"><label>เบอร์โทร / ช่องทางติดต่อ</label><input name="phone" required></div><div class="field"><label>หมายเหตุ</label><textarea name="note"></textarea></div><button class="btn primary" type="submit">ยืนยันคำสั่งซื้อ</button></form></div></div>
<div id="bookModal" class="modal"><div class="box"><div class="actions" style="justify-content:space-between"><h3 id="bookTitle">จองบริการ</h3><button class="btn" onclick="closeModal('bookModal')">ปิด</button></div><form id="bookForm"><input type="hidden" name="service_id"><div class="field"><label>ชื่อผู้จอง</label><input name="customer_name" required></div><div class="field"><label>เบอร์โทร / ช่องทางติดต่อ</label><input name="phone" required></div><div class="field"><label>วันที่</label><input name="booking_date" type="date" required></div><div class="field"><label>เวลา</label><input name="booking_time" type="time" required></div><div class="field"><label>หมายเหตุ</label><textarea name="note"></textarea></div><button class="btn primary" type="submit">ส่งคำขอจอง</button></form></div></div>
<script>const SLUG=__STORE_SLUG__;let D={settings:{},products:[],services:[]};let cart=JSON.parse(localStorage.getItem('infini_cart_'+SLUG)||'{}');const $=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));const money=n=>Number(n||0).toLocaleString('th-TH',{maximumFractionDigits:2})+' บาท';async function api(url,opt={}){const r=await fetch(url,{headers:{'Content-Type':'application/json',...(opt.headers||{})},...opt});let d={};try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.detail||'เกิดข้อผิดพลาด');return d}document.querySelectorAll('.tab').forEach(x=>x.onclick=()=>{document.querySelectorAll('.tab').forEach(y=>y.classList.toggle('on',x===y));document.querySelectorAll('.panel').forEach(y=>y.classList.toggle('on',y.id===x.dataset.tab))});function saveCart(){localStorage.setItem('infini_cart_'+SLUG,JSON.stringify(cart));renderCartBar()}function add(id){const p=D.products.find(x=>x.id===id);const q=(cart[id]||0)+1;if(q>p.stock)return alert('สต็อกไม่พอ');cart[id]=q;saveCart()}function renderCartBar(){let n=0,t=0;for(const [id,q] of Object.entries(cart)){const p=D.products.find(x=>x.id===id);if(p){n+=q;t+=p.price*q}}$('cartCount').textContent='ตะกร้า '+n+' ชิ้น';$('cartTotal').textContent=money(t)}function openCart(){const lines=[];for(const [id,q] of Object.entries(cart)){const p=D.products.find(x=>x.id===id);if(p)lines.push(`<div class="item"><b>${esc(p.name)}</b> × ${q}<div class="price">${money(p.price*q)}</div><div class="actions"><button class="btn" onclick="changeQty('${id}',-1)">−</button><button class="btn" onclick="changeQty('${id}',1)">＋</button></div></div>`)}$('cartItems').innerHTML=lines.join('')||'<div class="empty">ยังไม่มีสินค้า</div>';$('cartModal').classList.add('on')}function changeQty(id,d){cart[id]=(cart[id]||0)+d;if(cart[id]<=0)delete cart[id];saveCart();openCart()}function closeModal(id){$(id).classList.remove('on')}function openBook(id){const s=D.services.find(x=>x.id===id);$('bookTitle').textContent='จอง '+s.name;$('bookForm').service_id.value=id;$('bookModal').classList.add('on')}async function load(){D=await api('/api/public/store/'+encodeURIComponent(SLUG));$('shopName').textContent=D.settings.shop_name;$('contact').textContent=D.settings.contact||'';$('notice').textContent=D.settings.order_note||'';$('productGrid').innerHTML=D.settings.shop_enabled?(D.products.map(p=>`<div class="card">${p.image_url?`<img src="${esc(p.image_url)}" alt="">`:'<div style="aspect-ratio:1/1;border-radius:13px;background:#10263d;display:grid;place-items:center">สินค้า</div>'}<h3>${esc(p.name)}</h3><div class="muted">${esc(p.description)}</div><div class="price">${money(p.price)}</div><div class="muted">เหลือ ${p.stock}</div><div class="actions"><button class="btn primary" onclick="add('${p.id}')">ใส่ตะกร้า</button>${p.sheet_url?`<a class="btn" href="${esc(p.sheet_url)}">ดูแผ่น</a>`:''}</div></div>`).join('')||'<div class="empty">ยังไม่มีสินค้า</div>'):'<div class="empty">ร้านยังไม่เปิดรับออเดอร์</div>';$('serviceGrid').innerHTML=D.settings.booking_enabled?(D.services.map(s=>`<div class="card">${s.image_url?`<img src="${esc(s.image_url)}" alt="">`:''}<h3>${esc(s.name)}</h3><div class="muted">${esc(s.description)}</div><div class="price">${money(s.price)}</div><div class="muted">${s.duration_min} นาที · ${esc(s.available_note)}</div><button class="btn primary" onclick="openBook('${s.id}')">จอง</button></div>`).join('')||'<div class="empty">ยังไม่มีบริการ</div>'):'<div class="empty">ยังไม่เปิดรับจอง</div>';renderCartBar()}$('orderForm').onsubmit=async e=>{e.preventDefault();const items=Object.entries(cart).map(([product_id,qty])=>({product_id,qty}));if(!items.length)return alert('กรุณาเลือกสินค้า');const f=new FormData(e.target);try{const r=await api('/api/public/store/'+encodeURIComponent(SLUG)+'/orders',{method:'POST',body:JSON.stringify({customer_name:f.get('customer_name'),phone:f.get('phone'),note:f.get('note'),payment_method:'manual',items})});cart={};saveCart();closeModal('cartModal');alert('รับออเดอร์แล้ว เลขที่ '+r.order_id+'\nยอด '+money(r.total)+'\n'+r.payment_note);await load()}catch(err){alert(err.message)}};$('bookForm').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);try{const r=await api('/api/public/store/'+encodeURIComponent(SLUG)+'/bookings',{method:'POST',body:JSON.stringify({service_id:f.get('service_id'),customer_name:f.get('customer_name'),phone:f.get('phone'),booking_date:f.get('booking_date'),booking_time:f.get('booking_time'),note:f.get('note')})});closeModal('bookModal');alert('ส่งคำขอจองแล้ว เลขที่ '+r.booking_id);e.target.reset()}catch(err){alert(err.message)}};load().catch(e=>document.body.innerHTML='<div class="wrap"><div class="empty">'+esc(e.message)+'</div></div>');</script></body></html>'''
