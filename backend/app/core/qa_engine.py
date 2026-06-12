"""Mall QA Engine — generates natural Egyptian Arabic responses."""
from __future__ import annotations
import logging, os
from typing import List, Optional
from openai import OpenAI, AuthenticationError, APIConnectionError

logger = logging.getLogger(__name__)

MALL_NAME = os.getenv("MALL_NAME", "لمعي جراند مول")
_PLACEHOLDER = "your_openai_api_key_here"

_CUSTOMER_SYSTEM = f"""\
أنت "مالي" — مساعد {MALL_NAME} الذكي للعملاء فقط.

ما تقدر تساعد فيه كعميل:
- سعر أي منتج
- توافر وتفاصيل المنتجات
- تصفح الفئات
- حجز أو شراء منتج
- متابعة الطلبات

قواعد صارمة:
- إذا سألك العميل عن المبيعات أو الأرباح أو الإيرادات أو التقارير أو رؤى الإدارة أو الحسابات → ارفض بأدب وقل "المعلومات دي مخصصة للإدارة بس" ولا تجاوب عليها أبداً
- لا تعطي أي أرقام مبيعات أو إيرادات للعميل
- بتكلم بالعربية المصرية العامية الطبيعية
- أسلوبك ودود ومبهج
- لو المنتج مش موجود اقترح بديل
"""

_MANAGER_SYSTEM = f"""\
أنت "مالي" — المساعد التحليلي الشامل لمدير {MALL_NAME}.
- لديك صلاحية الوصول لكل البيانات: المبيعات، الأرباح، الإيرادات، المخزون، تحليل المنتجات
- بتتكلم بالعربية المصرية العامية المهنية
- بتحول الأرقام لكلام واضح ومفيد
- بتقدم توصيات قابلة للتنفيذ
- لما تعرض أرقام، استخدم التنسيق المناسب
- أسلوبك مباشر وواضح ومهني
"""


class MallQAEngine:
    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._model = os.getenv("LLM_MODEL", "gpt-4o")
        self._initialized = False

    def _init(self):
        if self._initialized:
            return
        self._initialized = True
        key = os.getenv("OPENAI_API_KEY", "")
        if key and key != _PLACEHOLDER:
            try:
                self._client = OpenAI(api_key=key)
                logger.info("QA Engine: OpenAI client initialized")
            except Exception as e:
                logger.warning("QA Engine: failed to init OpenAI: %s", e)
                self._client = None
        else:
            logger.warning("QA Engine: OPENAI_API_KEY not set — running in DB-only mode")
            self._client = None

    def is_available(self) -> bool:
        self._init()
        return self._client is not None

    def generate_response(self, question: str, mcp_data: str,
                          history: List[dict], role: str = "customer") -> str:
        self._init()
        if not self._client:
            # Return raw data with a polite wrapper
            return _wrap_raw(mcp_data, role)

        system = _CUSTOMER_SYSTEM if role == "customer" else _MANAGER_SYSTEM
        messages = [{"role": "system", "content": system}]
        messages.extend(history[-4:])
        messages.append({
            "role": "user",
            "content": f"سؤال المستخدم: {question}\n\nالبيانات:\n{mcp_data}\n\nرد بشكل طبيعي ومفيد."
        })
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.4,
                max_tokens=700,
            )
            return resp.choices[0].message.content.strip()
        except (AuthenticationError, APIConnectionError) as e:
            logger.error("OpenAI auth/connection error: %s", e)
            return _wrap_raw(mcp_data, role)
        except Exception as e:
            logger.error("QA generation failed: %s", e)
            return _wrap_raw(mcp_data, role)

    def general_response(self, question: str, history: List[dict],
                         role: str = "customer") -> str:
        self._init()
        if not self._client:
            return _general_fallback(role)

        system = _CUSTOMER_SYSTEM if role == "customer" else _MANAGER_SYSTEM
        messages = [{"role": "system", "content": system}]
        messages.extend(history[-4:])
        messages.append({"role": "user", "content": question})
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.5,
                max_tokens=400,
            )
            return resp.choices[0].message.content.strip()
        except (AuthenticationError, APIConnectionError) as e:
            logger.error("OpenAI error in general_response: %s", e)
            return _general_fallback(role)
        except Exception as e:
            logger.error("General response failed: %s", e)
            return _general_fallback(role)


def _wrap_raw(data: str, role: str) -> str:
    """Format raw DB data as a readable response without LLM."""
    if not data:
        return "مش لاقي بيانات مناسبة. ممكن توضح أكتر؟"
    return data


def _general_fallback(role: str) -> str:
    if role == "customer":
        return (
            "أهلاً! أنا مساعد لمعي جراند مول.\n"
            "جرب تسألني:\n"
            "• بكام الثلاجة؟\n"
            "• في كنبة متاحة؟\n"
            "• اعرضلي أجهزة المطبخ\n"
            "• عايز أشتري مروحة"
        )
    return (
        "أهلاً مديرنا!\n"
        "جرب:\n"
        "• تقرير المبيعات\n"
        "• الأرباح الشهر ده\n"
        "• أكثر منتج بيتباع\n"
        "• منتجات قريبة من النفاد"
    )


qa_engine = MallQAEngine()