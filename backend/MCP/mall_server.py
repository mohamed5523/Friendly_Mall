"""MCP Server for Mall Management System - 15 Tools."""
from __future__ import annotations
import logging, os, json
from typing import Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

sys_path_fix = os.path.dirname(os.path.dirname(__file__))
import sys; sys.path.insert(0, sys_path_fix)

from data.mall_database import (
    init_db, search_products, get_product_by_id, get_products_by_category,
    get_all_categories, create_order, get_order_status, get_sales_report,
    get_low_stock_products, get_top_products, get_product_sales_history,
    get_category_correlation, get_account_summary,
)
from openai import OpenAI

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("MCP_PORT", "8001"))

mcp = FastMCP("Mall MCP Server", host=SERVER_HOST, port=SERVER_PORT)
init_db()

_llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

# ── Helpers ────────────────────────────────────────────────────────────────

def _fmt_product(p: dict) -> str:
    stock_label = "✅ متاح" if p["stock_count"] > 0 else "❌ نفد المخزون"
    return (
        f"🛍️ **{p['name_ar']}**\n"
        f"  - الفئة: {p.get('category_name','')}\n"
        f"  - السعر: {p['price']:,.0f} جنيه\n"
        f"  - الكمية المتاحة: {p['stock_count']} قطعة — {stock_label}\n"
        + (f"  - الماركة: {p['brand']}\n" if p.get("brand") else "")
        + (f"  - الوصف: {p['description_ar']}\n" if p.get("description_ar") else "")
    )


# ══════════════════════════════════════════════════════════════════════════
# CUSTOMER TOOLS (1-7)
# ══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_products_tool(query: str, category: Optional[str] = None) -> str:
    """
    البحث عن منتجات في المول بناءً على الاسم أو الوصف.
    استخدم دايماً لما العميل يسأل عن منتج معين.
    Args:
        query: اسم المنتج أو وصفه (مثال: ثلاجة، كنبة، مروحة)
        category: الفئة اختيارية (مثال: أجهزة كهربائية، المطبخ)
    """
    results = search_products(query, category, limit=8)
    if not results:
        return f"مفيش منتجات بتطابق '{query}' في المول دلوقتي."
    lines = [f"لقينا {len(results)} منتج يطابق '{query}':\n"]
    for p in results:
        lines.append(_fmt_product(p))
    return "\n".join(lines)


@mcp.tool()
async def check_product_price(product_name: str) -> str:
    """
    الاستعلام عن سعر منتج معين.
    Args:
        product_name: اسم المنتج أو جزء منه
    """
    results = search_products(product_name, limit=5)
    if not results:
        return f"مش لاقي منتج اسمه '{product_name}'."
    lines = [f"أسعار '{product_name}':\n"]
    for p in results:
        lines.append(f"• {p['name_ar']}: **{p['price']:,.0f} جنيه**")
    return "\n".join(lines)


@mcp.tool()
async def check_product_stock(product_name: str) -> str:
    """
    معرفة هل المنتج متاح في المخزون أم لا.
    Args:
        product_name: اسم المنتج
    """
    results = search_products(product_name, limit=5)
    if not results:
        return f"مش لاقي منتج اسمه '{product_name}'."
    lines = []
    for p in results:
        status = f"✅ متاح ({p['stock_count']} قطعة)" if p["stock_count"] > 0 else "❌ نفد المخزون"
        lines.append(f"• {p['name_ar']}: {status}")
    return "\n".join(lines)


@mcp.tool()
async def get_products_by_category_tool(category: str) -> str:
    """
    عرض كل منتجات فئة معينة.
    Args:
        category: اسم الفئة (مثال: المطبخ، غرف النوم، الأجهزة الكهربائية)
    """
    results = get_products_by_category(category, limit=15)
    if not results:
        return f"مفيش منتجات في فئة '{category}'."
    lines = [f"منتجات فئة '{category}' ({len(results)} منتج):\n"]
    for p in results:
        lines.append(f"• {p['name_ar']} — {p['price']:,.0f} جنيه ({p['stock_count']} متاح)")
    return "\n".join(lines)


@mcp.tool()
async def reserve_product(product_name: str, customer_name: str, quantity: int = 1) -> str:
    """
    حجز منتج للعميل بدون دفع فوري.
    Args:
        product_name: اسم المنتج
        customer_name: اسم العميل
        quantity: الكمية المطلوبة (افتراضي 1)
    """
    results = search_products(product_name, limit=1)
    if not results:
        return f"مش لاقي منتج اسمه '{product_name}'."
    p = results[0]
    try:
        order = create_order(p["id"], customer_name, quantity, order_type="حجز")
        return (
            f"✅ تم الحجز بنجاح!\n"
            f"📋 رقم الحجز: {order['order_id']}\n"
            f"🛍️ المنتج: {p['name_ar']}\n"
            f"👤 العميل: {customer_name}\n"
            f"📦 الكمية: {quantity}\n"
            f"💰 الإجمالي: {order['total_price']:,.0f} جنيه\n"
            f"الحالة: {order['status']}"
        )
    except ValueError as e:
        return f"⚠️ مش قادر أحجز: {e}"


@mcp.tool()
async def buy_product(product_name: str, customer_name: str, quantity: int = 1,
                      customer_phone: str = "") -> str:
    """
    شراء منتج وتسجيله في قاعدة البيانات.
    Args:
        product_name: اسم المنتج
        customer_name: اسم العميل
        quantity: الكمية
        customer_phone: رقم التليفون (اختياري)
    """
    results = search_products(product_name, limit=1)
    if not results:
        return f"مش لاقي منتج اسمه '{product_name}'."
    p = results[0]
    try:
        order = create_order(p["id"], customer_name, quantity, order_type="شراء",
                             customer_phone=customer_phone)
        return (
            f"🎉 تمت عملية الشراء بنجاح!\n"
            f"📋 رقم الأوردر: {order['order_id']}\n"
            f"🛍️ المنتج: {p['name_ar']}\n"
            f"👤 العميل: {customer_name}\n"
            f"📦 الكمية: {quantity}\n"
            f"💰 المبلغ الإجمالي: {order['total_price']:,.0f} جنيه\n"
            f"✅ الحالة: {order['status']}"
        )
    except ValueError as e:
        return f"⚠️ مش قادر أتم الشراء: {e}"


@mcp.tool()
async def check_order_status(order_id: int) -> str:
    """
    متابعة حالة طلب أو حجز.
    Args:
        order_id: رقم الطلب
    """
    order = get_order_status(order_id)
    if not order:
        return f"مش لاقي أوردر رقم {order_id}."
    return (
        f"📋 تفاصيل الطلب #{order_id}:\n"
        f"🛍️ المنتج: {order['product_name']}\n"
        f"👤 العميل: {order['customer_name']}\n"
        f"📦 الكمية: {order['quantity']}\n"
        f"💰 الإجمالي: {order['total_price']:,.0f} جنيه\n"
        f"🏷️ نوع: {order['order_type']}\n"
        f"✅ الحالة: {order['status']}\n"
        f"📅 التاريخ: {order['created_at']}"
    )


# ══════════════════════════════════════════════════════════════════════════
# MANAGER TOOLS (8-15)
# ══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_sales_report_tool(days: int = 30) -> str:
    """
    تقرير المبيعات للمدير.
    Args:
        days: عدد الأيام للتقرير (افتراضي 30)
    """
    r = get_sales_report(days)
    lines = [
        f"📊 **تقرير المبيعات — آخر {days} يوم**\n",
        f"💰 إجمالي الإيرادات: {r['total_revenue']:,.0f} جنيه",
        f"📦 إجمالي الوحدات المباعة: {r['total_units_sold']}",
        "\n**المبيعات حسب الفئة:**",
    ]
    for cat in r["by_category"]:
        lines.append(f"  • {cat['name_ar']}: {cat['revenue']:,.0f} جنيه ({cat['qty']} وحدة)")
    lines.append("\n**أكثر 5 منتجات مبيعاً:**")
    for i, p in enumerate(r["top_products"], 1):
        lines.append(f"  {i}. {p['product_name']}: {p['qty']} وحدة — {p['rev']:,.0f} جنيه")
    return "\n".join(lines)


@mcp.tool()
async def get_revenue_analysis(days: int = 30) -> str:
    """
    تحليل الأرباح والإيرادات للمدير.
    Args:
        days: عدد الأيام
    """
    summary = get_account_summary()
    report = get_sales_report(days)
    return (
        f"💹 **تحليل الإيرادات**\n\n"
        f"إيرادات اليوم: {summary['today_revenue_egp']:,.0f} جنيه\n"
        f"إيرادات آخر {days} يوم: {report['total_revenue']:,.0f} جنيه\n"
        f"إجمالي الإيرادات الكلية: {summary['total_revenue_egp']:,.0f} جنيه\n"
        f"متوسط قيمة الطلب: {summary['average_order_value_egp']:,.0f} جنيه\n"
        f"إجمالي الطلبات: {summary['total_orders']}\n"
        f"عدد المنتجات في المخزون: {summary['total_products_in_stock']}"
    )


@mcp.tool()
async def get_top_selling_products(days: int = 30, limit: int = 10) -> str:
    """
    أكثر المنتجات مبيعاً.
    Args:
        days: الفترة الزمنية
        limit: عدد المنتجات
    """
    products = get_top_products(days, limit)
    if not products:
        return "مفيش بيانات مبيعات كافية."
    lines = [f"🏆 **أكثر {limit} منتجات مبيعاً — آخر {days} يوم:**\n"]
    for i, p in enumerate(products, 1):
        lines.append(
            f"{i}. {p['product_name']}\n"
            f"   📦 مبيع: {p['total_sold']} وحدة | 💰 إيراد: {p['total_revenue']:,.0f} جنيه"
        )
    return "\n".join(lines)


@mcp.tool()
async def predict_product_demand(product_name: str) -> str:
    """
    توقع الطلب المستقبلي لمنتج باستخدام الذكاء الاصطناعي.
    Args:
        product_name: اسم المنتج
    """
    results = search_products(product_name, limit=1)
    if not results:
        return f"مش لاقي منتج اسمه '{product_name}'."
    p = results[0]
    history = get_product_sales_history(p["id"], days=90)

    if not history:
        return f"مفيش بيانات مبيعات كافية للمنتج '{p['name_ar']}' للتنبؤ."

    history_text = "\n".join([
        f"- {row['sale_date']}: {row['qty']} وحدة — {row['revenue']:.0f} جنيه"
        for row in history[-30:]
    ])

    prompt = f"""أنت محلل مبيعات خبير. بناءً على بيانات مبيعات المنتج التالية:

المنتج: {p['name_ar']}
الفئة: {p.get('category_name', '')}
السعر الحالي: {p['price']} جنيه
المخزون الحالي: {p['stock_count']} قطعة

بيانات المبيعات (آخر 30 يوم من أصل 90):
{history_text}

المطلوب:
1. تحليل الاتجاه (تصاعدي / تنازلي / مستقر)
2. توقع المبيعات للشهر القادم
3. هل المخزون كافٍ؟
4. توصية للمدير

اكتب التحليل بالعربية المصرية العامية بشكل واضح ومفيد."""

    response = _llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=600,
    )
    analysis = response.choices[0].message.content
    return f"🔮 **توقع الطلب لـ '{p['name_ar']}':**\n\n{analysis}"


@mcp.tool()
async def get_low_stock_alert() -> str:
    """
    تنبيه المدير بالمنتجات التي أوشكت على النفاد.
    """
    products = get_low_stock_products(threshold=5)
    if not products:
        return "✅ كل المنتجات عندها مخزون كافي (أكتر من 5 قطع)."
    lines = [f"⚠️ **تنبيه مخزون منخفض — {len(products)} منتج:**\n"]
    for p in products:
        emoji = "🔴" if p["stock_count"] == 0 else "🟡"
        lines.append(f"{emoji} {p['name_ar']}: **{p['stock_count']} قطعة** متبقية")
    return "\n".join(lines)


@mcp.tool()
async def get_product_correlation_insights() -> str:
    """
    تحليل الارتباط بين المنتجات — أيها بيتباعوا مع بعض.
    """
    correlations = get_category_correlation()
    if not correlations:
        return "مفيش بيانات كافية للارتباط بين المنتجات دلوقتي."

    data_text = "\n".join([
        f"- {c['product_a']} مع {c['product_b']}: {c['co_purchases']} مرة"
        for c in correlations[:10]
    ])

    prompt = f"""أنت محلل مبيعات خبير. بناءً على بيانات المنتجات اللي بتتباع مع بعض:

{data_text}

قدملي:
1. أهم 3 ارتباطات وتفسيرها
2. توصيات لعروض Bundle
3. رأيك في ترتيب المتجر

اكتب بالعربية المصرية العامية."""

    response = _llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )
    analysis = response.choices[0].message.content
    lines = ["🔗 **تحليل الارتباط بين المنتجات:**\n"]
    lines.append("البيانات الخام:")
    for c in correlations[:5]:
        lines.append(f"  • {c['product_a']} + {c['product_b']}: {c['co_purchases']} عملية")
    lines.append(f"\n📊 **تحليل الذكاء الاصطناعي:**\n{analysis}")
    return "\n".join(lines)


@mcp.tool()
async def get_manager_insights() -> str:
    """
    رؤى تحليلية شاملة للمدير عن أداء المول.
    """
    summary = get_account_summary()
    report_30 = get_sales_report(30)
    report_7 = get_sales_report(7)
    low_stock = get_low_stock_products(5)
    top = get_top_products(30, 5)

    data = f"""
إيرادات الأسبوع: {report_7['total_revenue']:,.0f} جنيه
إيرادات الشهر: {report_30['total_revenue']:,.0f} جنيه
إجمالي الإيرادات: {summary['total_revenue_egp']:,.0f} جنيه
متوسط قيمة الطلب: {summary['average_order_value_egp']:,.0f} جنيه
منتجات قريبة من النفاد: {len(low_stock)}
أفضل منتج: {top[0]['product_name'] if top else 'لا يوجد'}
"""
    prompt = f"""أنت مستشار أعمال خبير لمول منزلي مصري.
بناءً على البيانات التالية:
{data}

قدم:
1. تقييم الأداء العام (جملتين)
2. أهم 3 نقاط قوة
3. أهم 3 فرص للتحسين
4. توصية استراتيجية واحدة عاجلة

اكتب بالعربية المصرية العامية بأسلوب مهني وودود."""

    response = _llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=600,
    )
    insights = response.choices[0].message.content
    return f"🧠 **رؤى استراتيجية للمول:**\n\n{insights}"


@mcp.tool()
async def get_account_summary_tool() -> str:
    """
    ملخص الحسابات الكامل للمدير.
    """
    s = get_account_summary()
    return (
        f"📈 **ملخص حسابات المول:**\n\n"
        f"💰 إيرادات اليوم: {s['today_revenue_egp']:,.0f} جنيه\n"
        f"💵 إجمالي الإيرادات: {s['total_revenue_egp']:,.0f} جنيه\n"
        f"🛒 عدد الطلبات الكلي: {s['total_orders']}\n"
        f"📊 متوسط قيمة الطلب: {s['average_order_value_egp']:,.0f} جنيه\n"
        f"📦 عدد المنتجات: {s['total_products_in_stock']}"
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
