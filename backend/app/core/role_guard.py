"""
Role Guard — enforces strict boundaries between customer and manager roles.

Customer is ONLY allowed to:
  - search/browse products
  - check price
  - check stock/availability
  - reserve a product
  - buy a product
  - check their own order status
  - ask general product/mall questions

Manager can do everything.

Any query that sounds like a manager request (sales reports, revenue,
top-selling, predictions, insights, accounts) is BLOCKED for customers
and returns a polite refusal in Egyptian Arabic.
"""
from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Intent sets ────────────────────────────────────────────────────────────────

CUSTOMER_INTENTS = {
    "search_product",
    "check_price",
    "check_stock",
    "browse_category",
    "reserve_product",
    "buy_product",
    "check_order",
    "general_inquiry",
}

MANAGER_ONLY_INTENTS = {
    "get_sales_report",
    "get_revenue",
    "get_top_products",
    "predict_demand",
    "low_stock_alert",
    "product_correlation",
    "manager_insights",
    "account_summary",
}

# ── Keyword patterns that clearly indicate a manager-level query ───────────────

_MANAGER_KEYWORD_PATTERNS = [
    # Sales / revenue
    r"(تقرير|مبيعات|بيتباع|المبيعات)",
    r"(أرباح|ارباح|إيراد|ايراد|ربح|دخل|revenue|profit)",
    r"(أكثر منتج|أكتر منتج|الأعلى مبيعاً|الأعلى مبيعا)",
    # Forecasting / analytics
    r"(توقع|تنبؤ|forecast|predict)",
    r"(رؤى|رؤيه|insights?|تحليل شامل|تحليلات)",
    r"(ارتباط.*منتج|منتج.*ارتباط|correlation)",
    # Financial / accounts
    r"(ملخص الحسابات|حسابات المول|account summary)",
    # Stock management (manager perspective: "تنبيه المخزون", "مخزون المول")
    r"(تنبيه.*مخزون|مخزون.*المول|low.?stock.?alert)",
    r"(الشهر ده|الأسبوع ده|آخر \d+ يوم|آخر شهر).*(مبيعات|أرباح|ربح|إيراد)",
]

_MANAGER_REGEX = re.compile(
    "|".join(_MANAGER_KEYWORD_PATTERNS),
    flags=re.IGNORECASE | re.UNICODE,
)

# ── Public API ─────────────────────────────────────────────────────────────────

def is_manager_query(query: str) -> bool:
    """Return True if the query text looks like a manager-level request."""
    return bool(_MANAGER_REGEX.search(query))


def intent_allowed_for_role(intent: str, role: str) -> bool:
    """
    Return True if the detected intent is permitted for the given role.

    - manager: everything allowed
    - customer: only CUSTOMER_INTENTS allowed
    """
    if role == "manager":
        return True
    # customer
    return intent in CUSTOMER_INTENTS


def get_refusal_message(query: str, role: str) -> Optional[str]:
    """
    If the role is customer and the query is a manager-level request,
    return a polite refusal message in Egyptian Arabic.
    Returns None if no refusal is needed.
    """
    if role != "customer":
        return None

    if not is_manager_query(query):
        return None

    return (
        "عذراً، المعلومات دي مخصصة للإدارة بس.\n"
        "أنا بقدر أساعدك في:\n"
        "• معرفة سعر أي منتج (مثال: بكام التلفزيون؟)\n"
        "• التحقق من توافر منتج (مثال: في ثلاجة متاحة؟)\n"
        "• تصفح فئة معينة (مثال: اعرضلي منتجات المطبخ)\n"
        "• حجز أو شراء منتج\n"
        "• متابعة طلبك\n\n"
        "ممكن أساعدك بأي حاجة تانية؟"
    )


def enforce_customer_intent(intent: str, role: str) -> str:
    """
    If role is customer and intent is manager-only, demote intent to general_inquiry
    so that the customer gets a safe fallback rather than manager data.
    """
    if role == "manager":
        return intent
    if intent in MANAGER_ONLY_INTENTS:
        logger.warning(
            "Role guard: blocked intent=%s for role=customer → demoting to general_inquiry",
            intent,
        )
        return "general_inquiry"
    return intent
