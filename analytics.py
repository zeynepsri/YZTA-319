from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.schemas import AnalyticsOut
from backend.security import get_current_user
from database.base import get_db
from database.models import PriceHistory, Receipt, ReceiptItem, Store, User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsOut)
def get_analytics(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Harcama analizleri - grafikler için veri."""
    today = date.today()
    start_date = today - timedelta(days=30 * months)

    receipts = (
        db.query(Receipt)
        .filter(
            Receipt.user_id == current_user.id,
            Receipt.status == "completed",
            Receipt.receipt_date >= start_date,
        )
        .all()
    )

    
    monthly: dict[str, float] = defaultdict(float)
    for r in receipts:
        if r.receipt_date:
            key = r.receipt_date.strftime("%Y-%m")
            monthly[key] += r.total_amount or 0
    monthly_spending = [
        {"month": k, "total": round(v, 2)} for k, v in sorted(monthly.items())
    ]

    
    category_dist: dict[str, float] = defaultdict(float)
    for r in receipts:
        for item in r.items:
            cat = "Diğer"
            if item.product and item.product.category:
                cat = item.product.category.name
            category_dist[cat] += item.total_price
    category_distribution = dict(sorted(category_dist.items(), key=lambda x: -x[1]))

    
    store_comp: dict[str, float] = defaultdict(float)
    for r in receipts:
        if r.store:
            store_comp[r.store.name] += r.total_amount or 0
    store_comparison = dict(sorted(store_comp.items(), key=lambda x: -x[1]))

  
    product_counts: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "total": 0.0})
    for r in receipts:
        for item in r.items:
            name = item.raw_name
            product_counts[name]["count"] += item.quantity
            product_counts[name]["total"] += item.total_price
    top_products = sorted(
        [{"name": k, "count": v["count"], "total": round(v["total"], 2)} for k, v in product_counts.items()],
        key=lambda x: -x["count"],
    )[:10]

    
    inflated: list[dict] = []
    products_with_history = (
        db.query(PriceHistory.product_id, PriceHistory.price, PriceHistory.recorded_date)
        .join(ReceiptItem, ReceiptItem.product_id == PriceHistory.product_id)
        .join(Receipt, Receipt.id == ReceiptItem.receipt_id)
        .filter(Receipt.user_id == current_user.id)
        .distinct()
        .all()
    )
    
    product_prices: dict[int, list[tuple[date, float]]] = defaultdict(list)
    for ph in products_with_history:
        product_prices[ph.product_id].append((ph.recorded_date, ph.price))

    for pid, prices in product_prices.items():
        if len(prices) >= 2:
            prices.sort(key=lambda x: x[0])
            first_price = prices[0][1]
            last_price = prices[-1][1]
            if first_price > 0:
                change = round(((last_price - first_price) / first_price) * 100, 2)
                if change > 0:
                    product = db.query(ReceiptItem).filter(ReceiptItem.product_id == pid).first()
                    name = product.raw_name if product else f"Ürün {pid}"
                    inflated.append({"name": name, "change_percent": change, "old_price": first_price, "new_price": last_price})

    most_inflated = sorted(inflated, key=lambda x: -x["change_percent"])[:10]

    return AnalyticsOut(
        monthly_spending=monthly_spending,
        category_distribution=category_distribution,
        store_comparison=store_comparison,
        top_products=top_products,
        most_inflated_products=most_inflated,
    )