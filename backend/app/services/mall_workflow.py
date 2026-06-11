"""Mall Workflow — calls database functions DIRECTLY (no HTTP MCP server needed)."""
from __future__ import annotations
import logging, os, sys

# Make sure data module is importable from backend root
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from data.mall_database import (
    search_products, get_products_by_category, create_order,
    get_order_status, get_sales_report, get_low_stock_products,
    get_top_products, get_product_sales_history, get_category_correlation,
    get_account_summary, get_all_categories, init_db,
)
from app.core.state_manager import MallConversationState
from app.core.intent_router import RouteDecision
from openai import OpenAI

logger = logging.getLogger(__name__)

# Ensure DB is ready
init_db()

_llm_client = None

def _get_llm():
    global _llm_client
    if _llm_client is None:
        key = os.getenv("OPENAI_API_KEY", "")
        if key and key != "your_openai_api_key_here":
            _llm_client = OpenAI(api_key=key)
    return _llm_client


# ── Formatters ────────────────────────────────────────────────────────────

def _fmt_product(p: dict) -> str:
    stock = "متاح" if p["stock_count"] > 0 else "نفد المخزون"
    brand = f" | ماركة: {p['brand']}" if p.get("brand") else ""
    return (
        f"- {p['name_ar']}: {p['price']:,.0f} جنيه | "
        f"متاح: {p['stock_count']} قطعة ({stock}){brand}"
    )


# ── Customer handlers ─────────────────────────────────────────────────────

def _search_products(state: MallConversationState) -> str:
    q = state.entities.product_name or state.last_user_question
    cat = state.entities.category
    results = search_products(q, cat, limit=8)
    if not results:
        return f"مفيش منتجات بتطابق '{q}' في المول دلوقتي."
    lines = [f"لقينا {len(results)} منتج:\n"]
    lines.extend(_fmt_product(p) for p in results)
    return "\n".join(lines)


def _check_price(state: MallConversationState) -> str:
    q = state.entities.product_name or state.last_user_question
    results = search_products(q, limit=5)
    if not results:
        return f"مش لاقي منتج اسمه '{q}'."
    lines = [f"أسعار '{q}':"]
    for p in results:
        lines.append(f"- {p['name_ar']}: {p['price']:,.0f} جنيه")
    return "\n".join(lines)


def _check_stock(state: MallConversationState) -> str:
    q = state.entities.product_name or state.last_user_question
    results = search_products(q, limit=5)
    if not results:
        return f"مش لاقي منتج اسمه '{q}'."
    lines = []
    for p in results:
        status = f"متاح ({p['stock_count']} قطعة)" if p["stock_count"] > 0 else "نفد المخزون"
        lines.append(f"- {p['name_ar']}: {status}")
    return "\n".join(lines)


def _browse_category(state: MallConversationState) -> str:
    cat = state.entities.category or state.last_user_question
    results = get_products_by_category(cat, limit=15)
    if not results:
        cats = get_all_categories()
        cat_names = ", ".join(c["name_ar"] for c in cats)
        return f"مفيش منتجات في فئة '{cat}'.\nالفئات المتاحة: {cat_names}"
    lines = [f"منتجات '{cat}' ({len(results)} منتج):"]
    for p in results:
        lines.append(f"- {p['name_ar']}: {p['price']:,.0f} جنيه ({p['stock_count']} متاح)")
    return "\n".join(lines)


def _reserve_or_buy(state: MallConversationState, order_type: str) -> str:
    q = state.entities.product_name or ""
    if not q:
        return "محتاج اسم المنتج عشان أكمل. قولي اسمه إيه؟"
    results = search_products(q, limit=1)
    if not results:
        return f"مش لاقي منتج اسمه '{q}'."
    p = results[0]
    customer = state.entities.customer_name or "عميل"
    qty = state.entities.quantity or 1
    try:
        order = create_order(p["id"], customer, qty, order_type=order_type)
        action = "الحجز" if order_type == "حجز" else "الشراء"
        return (
            f"تم {action} بنجاح!\n"
            f"رقم الطلب: {order['order_id']}\n"
            f"المنتج: {p['name_ar']}\n"
            f"الكمية: {qty}\n"
            f"الإجمالي: {order['total_price']:,.0f} جنيه\n"
            f"الحالة: {order['status']}"
        )
    except ValueError as e:
        return f"مش قادر أكمل: {e}"


def _check_order(state: MallConversationState) -> str:
    oid = state.entities.order_id
    if not oid:
        return "محتاج رقم الطلب. قولي رقمه إيه؟"
    order = get_order_status(oid)
    if not order:
        return f"مش لاقي طلب رقم {oid}."
    return (
        f"تفاصيل الطلب #{oid}:\n"
        f"المنتج: {order['product_name']}\n"
        f"العميل: {order['customer_name']}\n"
        f"الكمية: {order['quantity']}\n"
        f"الإجمالي: {order['total_price']:,.0f} جنيه\n"
        f"النوع: {order['order_type']}\n"
        f"الحالة: {order['status']}\n"
        f"التاريخ: {order['created_at']}"
    )


# ── Manager handlers ──────────────────────────────────────────────────────

def _parse_days(state: MallConversationState, default: int = 30) -> int:
    tp = state.entities.time_period
    if tp:
        try:
            return int(tp)
        except Exception:
            pass
    return default


def _sales_report(state: MallConversationState) -> str:
    days = _parse_days(state)
    r = get_sales_report(days)
    lines = [
        f"تقرير المبيعات — آخر {days} يوم:",
        f"الإيرادات: {r['total_revenue']:,.0f} جنيه",
        f"الوحدات المباعة: {r['total_units_sold']}",
        "\nالمبيعات حسب الفئة:",
    ]
    for cat in r["by_category"]:
        lines.append(f"  - {cat['name_ar']}: {cat['revenue']:,.0f} جنيه ({cat['qty']} وحدة)")
    lines.append("\nأكثر 5 منتجات مبيعاً:")
    for i, p in enumerate(r["top_products"], 1):
        lines.append(f"  {i}. {p['product_name']}: {p['qty']} وحدة — {p['rev']:,.0f} جنيه")
    return "\n".join(lines)


def _revenue_analysis(state: MallConversationState) -> str:
    days = _parse_days(state)
    s = get_account_summary()
    r = get_sales_report(days)
    return (
        f"تحليل الإيرادات:\n"
        f"إيرادات اليوم: {s['today_revenue_egp']:,.0f} جنيه\n"
        f"إيرادات آخر {days} يوم: {r['total_revenue']:,.0f} جنيه\n"
        f"إجمالي الإيرادات: {s['total_revenue_egp']:,.0f} جنيه\n"
        f"متوسط قيمة الطلب: {s['average_order_value_egp']:,.0f} جنيه\n"
        f"إجمالي الطلبات: {s['total_orders']}\n"
        f"عدد المنتجات: {s['total_products_in_stock']}"
    )


def _top_products(state: MallConversationState) -> str:
    days = _parse_days(state)
    products = get_top_products(days, 10)
    if not products:
        return "مفيش بيانات مبيعات كافية."
    lines = [f"أكثر 10 منتجات مبيعاً — آخر {days} يوم:"]
    for i, p in enumerate(products, 1):
        lines.append(
            f"{i}. {p['product_name']}: {p['total_sold']} وحدة | {p['total_revenue']:,.0f} جنيه"
        )
    return "\n".join(lines)


def _predict_demand(state: MallConversationState) -> str:
    q = state.entities.product_name or state.last_user_question
    results = search_products(q, limit=1)
    if not results:
        return f"مش لاقي منتج اسمه '{q}'."
    p = results[0]
    history = get_product_sales_history(p["id"], days=90)
    if not history:
        return f"مفيش بيانات مبيعات كافية للمنتج '{p['name_ar']}'."

    history_text = "\n".join([
        f"- {row['sale_date']}: {row['qty']} وحدة"
        for row in history[-30:]
    ])

    llm = _get_llm()
    if not llm:
        return (
            f"بيانات المنتج '{p['name_ar']}':\n{history_text}\n\n"
            "(محتاج OPENAI_API_KEY عشان يولد التحليل الذكي)"
        )

    model = os.getenv("LLM_MODEL", "gpt-4o")
    prompt = (
        f"أنت محلل مبيعات خبير لمول منزلي مصري.\n"
        f"المنتج: {p['name_ar']} | السعر: {p['price']} جنيه | المخزون: {p['stock_count']} قطعة\n\n"
        f"بيانات المبيعات (آخر 30 يوم من 90):\n{history_text}\n\n"
        f"قدم: 1) الاتجاه 2) توقع الشهر القادم 3) هل المخزون كافٍ؟ 4) توصية\n"
        f"اكتب بالعربية المصرية العامية."
    )
    try:
        resp = llm.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        return f"توقع الطلب لـ '{p['name_ar']}':\n\n{resp.choices[0].message.content}"
    except Exception as e:
        logger.error("LLM prediction failed: %s", e)
        return f"بيانات '{p['name_ar']}':\n{history_text}"


def _low_stock(_state: MallConversationState) -> str:
    products = get_low_stock_products(threshold=5)
    if not products:
        return "كل المنتجات عندها مخزون كافٍ (أكتر من 5 قطع)."
    lines = [f"تنبيه مخزون منخفض — {len(products)} منتج:"]
    for p in products:
        tag = "نفد" if p["stock_count"] == 0 else "منخفض"
        lines.append(f"- {p['name_ar']}: {p['stock_count']} قطعة ({tag})")
    return "\n".join(lines)


def _product_correlation(_state: MallConversationState) -> str:
    correlations = get_category_correlation()
    if not correlations:
        return "مفيش بيانات كافية للارتباط دلوقتي."

    data_text = "\n".join([
        f"- {c['product_a']} مع {c['product_b']}: {c['co_purchases']} مرة"
        for c in correlations[:10]
    ])

    llm = _get_llm()
    if not llm:
        return f"أكثر المنتجات اللي بتتباع مع بعض:\n{data_text}"

    model = os.getenv("LLM_MODEL", "gpt-4o")
    prompt = (
        f"محلل مبيعات خبير. المنتجات اللي بتتباع مع بعض:\n{data_text}\n\n"
        f"قدم: 1) أهم 3 ارتباطات 2) توصيات Bundle 3) توصية ترتيب المتجر\n"
        f"بالعربية المصرية العامية."
    )
    try:
        resp = llm.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        return f"تحليل الارتباط بين المنتجات:\n\nالبيانات:\n{data_text}\n\nالتحليل:\n{resp.choices[0].message.content}"
    except Exception as e:
        logger.error("Correlation LLM failed: %s", e)
        return f"المنتجات اللي بتتباع مع بعض:\n{data_text}"


def _manager_insights(_state: MallConversationState) -> str:
    s = get_account_summary()
    r7 = get_sales_report(7)
    r30 = get_sales_report(30)
    low = get_low_stock_products(5)
    top = get_top_products(30, 3)

    summary = (
        f"إيرادات الأسبوع: {r7['total_revenue']:,.0f} جنيه\n"
        f"إيرادات الشهر: {r30['total_revenue']:,.0f} جنيه\n"
        f"إجمالي الإيرادات: {s['total_revenue_egp']:,.0f} جنيه\n"
        f"متوسط الطلب: {s['average_order_value_egp']:,.0f} جنيه\n"
        f"منتجات قريبة من النفاد: {len(low)}\n"
        f"أفضل منتج: {top[0]['product_name'] if top else 'لا يوجد'}"
    )

    llm = _get_llm()
    if not llm:
        return f"ملخص أداء المول:\n{summary}"

    model = os.getenv("LLM_MODEL", "gpt-4o")
    prompt = (
        f"مستشار أعمال خبير لمول منزلي مصري. البيانات:\n{summary}\n\n"
        f"قدم: 1) تقييم الأداء 2) نقاط القوة 3) فرص التحسين 4) توصية عاجلة\n"
        f"بالعربية المصرية المهنية."
    )
    try:
        resp = llm.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=700,
        )
        return f"رؤى استراتيجية:\n\n{resp.choices[0].message.content}"
    except Exception as e:
        logger.error("Insights LLM failed: %s", e)
        return f"ملخص أداء المول:\n{summary}"


def _account_summary(_state: MallConversationState) -> str:
    s = get_account_summary()
    return (
        f"ملخص حسابات المول:\n"
        f"إيرادات اليوم: {s['today_revenue_egp']:,.0f} جنيه\n"
        f"إجمالي الإيرادات: {s['total_revenue_egp']:,.0f} جنيه\n"
        f"عدد الطلبات: {s['total_orders']}\n"
        f"متوسط قيمة الطلب: {s['average_order_value_egp']:,.0f} جنيه\n"
        f"عدد المنتجات: {s['total_products_in_stock']}"
    )


# ── Dispatcher ────────────────────────────────────────────────────────────

_HANDLERS = {
    "search_product":    _search_products,
    "check_price":       _check_price,
    "check_stock":       _check_stock,
    "browse_category":   _browse_category,
    "reserve_product":   lambda s: _reserve_or_buy(s, "حجز"),
    "buy_product":       lambda s: _reserve_or_buy(s, "شراء"),
    "check_order":       _check_order,
    "get_sales_report":  _sales_report,
    "get_revenue":       _revenue_analysis,
    "get_top_products":  _top_products,
    "predict_demand":    _predict_demand,
    "low_stock_alert":   _low_stock,
    "product_correlation": _product_correlation,
    "manager_insights":  _manager_insights,
    "account_summary":   _account_summary,
}


async def run_mall_workflow(decision: RouteDecision,
                             state: MallConversationState) -> str:
    """Execute the appropriate handler directly (no HTTP needed)."""
    handler = _HANDLERS.get(decision.intent)
    if not handler:
        logger.warning("No handler for intent: %s", decision.intent)
        return ""
    try:
        result = handler(state)
        logger.info("Handler '%s' returned %d chars", decision.intent, len(result))
        return result
    except Exception as e:
        logger.error("Handler '%s' failed: %s", decision.intent, e)
        raise
