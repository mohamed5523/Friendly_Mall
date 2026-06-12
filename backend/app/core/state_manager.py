"""Mall State Manager — extracts structured state from Egyptian Arabic shopping conversations."""
from __future__ import annotations
import logging, os
from typing import List, Literal, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MallEntities(BaseModel):
    product_name: Optional[str] = Field(None, description="اسم المنتج المذكور")
    product_id: Optional[int] = Field(None, description="ID المنتج بعد التحليل")
    category: Optional[str] = Field(None, description="فئة المنتج (مثال: أجهزة كهربائية، المطبخ)")
    quantity: Optional[int] = Field(None, description="الكمية المطلوبة")
    customer_name: Optional[str] = Field(None, description="اسم العميل إذا ذُكر")
    customer_phone: Optional[str] = Field(None, description="رقم تليفون العميل")
    order_id: Optional[int] = Field(None, description="رقم الطلب إذا ذُكر")
    budget: Optional[float] = Field(None, description="الميزانية المحددة من العميل")
    time_period: Optional[str] = Field(None, description="الفترة الزمنية للمدير: اليوم/الأسبوع/الشهر")
    is_confirmed: Optional[bool] = Field(False, description="هل أكد المستخدم عملية الشراء/الحجز صراحة بـ (ايوة/نعم/أكد)؟")


class MallConversationState(BaseModel):
    entities: MallEntities = Field(default_factory=MallEntities)
    intent: str = Field(default="unknown")
    role: Literal["customer", "manager"] = Field(default="customer")
    last_user_question: str = ""
    needs_followup: bool = False


_SYSTEM_PROMPT = """\
أنت نظام استخراج حالة من محادثات مول منزلي مصري. أخرج JSON يطابق الـ Schema.

الـ Intents الممكنة:
- search_product: البحث عن منتج (عندكم؟، في عندكم؟، محتاج)
- check_price: السؤال عن السعر (بكام، سعر، كام)
- check_stock: هل المنتج متاح؟ (في، متوفر، موجود)
- browse_category: عرض فئة كاملة (اعرضلي، شوفلي)
- reserve_product: حجز منتج (احجزلي، عايز أحجز)
- buy_product: شراء منتج (عايز أشتري، هجيب، هاخد)
- check_order: متابعة طلب (طلبي، أوردر رقم)
- get_sales_report: تقرير مبيعات للمدير
- get_revenue: الأرباح والإيرادات للمدير
- get_top_products: أكثر المنتجات مبيعاً
- predict_demand: توقع الطلب لمنتج
- low_stock_alert: منتجات قريبة من النفاد
- product_correlation: الارتباط بين المنتجات
- manager_insights: رؤى تحليلية شاملة
- account_summary: ملخص الحسابات
- general_inquiry: استفسار عام

قواعد:
- إذا ذُكر منتج محدد → استخرجه في product_name
- إذا ذُكرت فئة عامة → استخرجها في category
- إذا قال "عايز أشتري كنبة" → intent=buy_product, product_name=كنبة
- إذا قال "بكام الثلاجة" → intent=check_price, product_name=ثلاجة
- الأرقام المذكورة للكمية → quantity
- أرقام الطلبات → order_id
- إذا قال "الشهر ده" أو "آخر 30 يوم" → time_period=30
- إذا سأل المساعد "أأكد لحضرتك الشراء؟" وأجاب المستخدم بالموافقة (مثل: اه، توكل على الله، أكد، هشتري) → is_confirmed=true

أجب بـ JSON فقط.
"""


class MallStateManager:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = os.getenv("LLM_MODEL", "gpt-4o")

    def extract_state(self, query: str, history: List[dict],
                      previous_state: Optional[MallConversationState] = None,
                      role: str = "customer") -> MallConversationState:
        if not self.client:
            return MallConversationState(
                entities=MallEntities(), intent="general_inquiry",
                role=role, last_user_question=query
            )
        history_text = "\n".join([
            f"{'عميل' if m['role']=='user' else 'مساعد'}: {m['content']}"
            for m in history[-4:]
        ])
        # Role constraint injected into prompt
        role_constraint = (
            "\n\nتنبيه مهم: المستخدم عميل عادي. لا تستخدم أبداً intent من هذه القائمة: "
            "get_sales_report, get_revenue, get_top_products, predict_demand, "
            "low_stock_alert, product_correlation, manager_insights, account_summary. "
            "إذا سأل العميل عن المبيعات أو الأرباح → استخدم intent=general_inquiry."
        ) if role == "customer" else ""
        user_content = (
            f"السياق السابق:\n{history_text}\n\n"
            f"الحالة السابقة:\n{previous_state.model_dump_json() if previous_state else 'لا يوجد'}\n\n"
            f"السؤال الحالي: {query}\n"
            f"دور المستخدم: {role}{role_constraint}"
        )
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format=MallConversationState,
                temperature=0.0,
            )
            parsed = response.choices[0].message.parsed
            parsed.last_user_question = query
            parsed.role = role
            return parsed
        except Exception as e:
            logger.error("State extraction failed: %s", e)
            return MallConversationState(
                entities=MallEntities(), intent="general_inquiry",
                role=role, last_user_question=query
            )


state_manager = MallStateManager()