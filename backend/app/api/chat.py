"""Mall Chat API endpoint."""
from __future__ import annotations
import logging, uuid, os
from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from app.models.schemas import ChatRequest, ChatResponse
from app.core.state_manager import state_manager, MallConversationState, MallEntities
from app.core.intent_router import route_conversation, RouteMode
from app.core.conversation_memory import short_term_memory
from app.core.qa_engine import qa_engine
from app.services.mall_workflow import run_mall_workflow
from app.core.role_guard import get_refusal_message, enforce_customer_intent

logger = logging.getLogger(__name__)
router = APIRouter()


def _fallback_route(query: str, role: str) -> Optional[str]:
    """
    Keyword-based fallback routing when LLM is not available.
    Strictly respects role — customers only get customer intents.
    Returns the intent string or None.
    """
    q = query.lower()

    CUSTOMER_KEYWORDS = {
        "search_product":  ["\u0639\u0646\u062f\u0643\u0645", "\u0641\u064a \u0639\u0646\u062f\u0643\u0645", "\u0645\u062d\u062a\u0627\u062c", "\u0623\u0628\u062d\u062b", "\u0627\u0628\u062d\u062b", "\u0641\u064a\u0647", "\u0639\u0627\u064a\u0632 \u0623\u0634\u0648\u0641"],
        "check_price":     ["\u0628\u0643\u0627\u0645", "\u0633\u0639\u0631", "\u0643\u0627\u0645", "\u062a\u0643\u0644\u0641\u0629", "\u064a\u0643\u0644\u0641"],
        "check_stock":     ["\u0645\u062a\u0648\u0641\u0631", "\u0645\u062a\u0627\u062d", "\u0645\u0648\u062c\u0648\u062f", "\u0641\u064a \u0645\u062e\u0632\u0648\u0646"],
        "browse_category": ["\u0627\u0639\u0631\u0636\u0644\u064a", "\u0634\u0648\u0641\u0644\u064a", "\u0643\u0644 \u0645\u0646\u062a\u062c\u0627\u062a", "\u0641\u0626\u0629", "\u0642\u0627\u0626\u0645\u0629"],
        "reserve_product": ["\u0627\u062d\u062c\u0632\u0644\u064a", "\u0639\u0627\u064a\u0632 \u0623\u062d\u062c\u0632", "\u062d\u062c\u0632"],
        "buy_product":     ["\u0639\u0627\u064a\u0632 \u0623\u0634\u062a\u0631\u064a", "\u0647\u0634\u062a\u0631\u064a", "\u0647\u0627\u062e\u062f", "\u0647\u062c\u064a\u0628"],
        "check_order":     ["\u0637\u0644\u0628\u064a", "\u0623\u0648\u0631\u062f\u0631", "\u062d\u0627\u0644\u0629 \u0637\u0644\u0628"],
    }

    MANAGER_KEYWORDS = {
        "get_sales_report":    ["\u062a\u0642\u0631\u064a\u0631", "\u0645\u0628\u064a\u0639\u0627\u062a", "\u0628\u064a\u062a\u0628\u0627\u0639"],
        "get_revenue":         ["\u0623\u0631\u0628\u0627\u062d", "\u0625\u064a\u0631\u0627\u062f", "\u0631\u0628\u062d", "\u062f\u062e\u0644"],
        "get_top_products":    ["\u0623\u0643\u062b\u0631 \u0645\u0646\u062a\u062c", "\u0623\u0643\u062a\u0631", "\u0627\u0644\u0623\u0641\u0636\u0644 \u0645\u0628\u064a\u0639\u0627"],
        "predict_demand":      ["\u062a\u0648\u0642\u0639", "\u0645\u0633\u062a\u0642\u0628\u0644", "\u062a\u0646\u0628\u0624"],
        "low_stock_alert":     ["\u062a\u0646\u0628\u064a\u0647 \u0645\u062e\u0632\u0648\u0646", "\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u0645\u0648\u0644", "\u0647\u064a\u0646\u062a\u0647\u064a"],
        "product_correlation": ["\u0627\u0631\u062a\u0628\u0627\u0637 \u0628\u064a\u0646 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a"],
        "manager_insights":    ["\u0631\u0624\u0649", "\u0625\u0646\u0633\u0627\u064a\u062a\u0633", "\u062a\u062d\u0644\u064a\u0644 \u0634\u0627\u0645\u0644"],
        "account_summary":     ["\u062d\u0633\u0627\u0628\u0627\u062a", "\u0645\u0644\u062e\u0635 \u062d\u0633\u0627\u0628\u0627\u062a"],
    }

    # Strictly role-based — customer only looks up customer intents
    keywords = MANAGER_KEYWORDS if role == "manager" else CUSTOMER_KEYWORDS
    for intent, kws in keywords.items():
        if any(kw in q for kw in kws):
            return intent
    return None


_CUSTOMER_REFUSAL = (
    "\u0639\u0630\u0631\u0627\u064b\u060c \u0627\u0644\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u062f\u064a \u0645\u062e\u0635\u0635\u0629 \u0644\u0644\u0625\u062f\u0627\u0631\u0629 \u0628\u0633.\n"
    "\u0623\u0646\u0627 \u0628\u0642\u062f\u0631 \u0623\u0633\u0627\u0639\u062f\u0643 \u0641\u064a:\n"
    "\u2022 \u0633\u0639\u0631 \u0623\u064a \u0645\u0646\u062a\u062c \u2014 \u0645\u062b\u0627\u0644: \u0628\u0643\u0627\u0645 \u0627\u0644\u062a\u0644\u0641\u0632\u064a\u0648\u0646\u061f\n"
    "\u2022 \u062a\u0648\u0627\u0641\u0631 \u0645\u0646\u062a\u062c \u2014 \u0645\u062b\u0627\u0644: \u0641\u064a \u062b\u0644\u0627\u062c\u0629 \u0645\u062a\u0627\u062d\u0629\u061f\n"
    "\u2022 \u062a\u0635\u0641\u062d \u0641\u0626\u0629 \u2014 \u0645\u062b\u0627\u0644: \u0627\u0639\u0631\u0636\u0644\u064a \u0645\u0646\u062a\u062c\u0627\u062a \u0627\u0644\u0645\u0637\u0628\u062e\n"
    "\u2022 \u062d\u062c\u0632 \u0623\u0648 \u0634\u0631\u0627\u0621 \u0645\u0646\u062a\u062c\n"
    "\u2022 \u0645\u062a\u0627\u0628\u0639\u0629 \u0637\u0644\u0628\u0643\n\n"
    "\u0641\u064a\u0647 \u062d\u0627\u062c\u0629 \u062a\u0627\u0646\u064a\u0629 \u062a\u0642\u062f\u0631 \u0623\u0633\u0627\u0639\u062f\u0643 \u0628\u064a\u0647\u0627\u061f"
)


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest,
                     x_session_id: Optional[str] = Header(None)):
    """Main chat endpoint for customer and manager queries."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    session_id = x_session_id or str(uuid.uuid4())
    role = request.role or "customer"
    query = request.query.strip()

    # ── LAYER 1: Fast keyword role guard ───────────────────────────────────
    # Blocks obvious manager queries BEFORE any LLM or DB call.
    refusal = get_refusal_message(query, role)
    if refusal:
        short_term_memory.add_message(session_id, "user", query)
        short_term_memory.add_message(session_id, "assistant", refusal)
        logger.info("RoleGuard-L1: blocked manager query for customer session=%s", session_id)
        return ChatResponse(answer=refusal, model_used="role-guard")

    # Add user message to history
    short_term_memory.add_message(session_id, "user", query)
    history = short_term_memory.get_history_dicts(session_id, limit=6)

    # ── State extraction (LLM or keyword fallback) ─────────────────────────
    previous_state = short_term_memory.get_state(session_id)

    if qa_engine.is_available():
        state = state_manager.extract_state(query, history, previous_state, role=role)
    else:
        intent = _fallback_route(query, role) or "general_inquiry"
        entities = MallEntities()
        if intent in ("search_product", "check_price", "check_stock"):
            entities.product_name = query
        state = MallConversationState(
            entities=entities,
            intent=intent,
            role=role,
            last_user_question=query,
        )

    # ── LAYER 2: Intent-level role guard ───────────────────────────────────
    # The LLM may still classify a manager intent for a customer. Catch it here.
    guarded_intent = enforce_customer_intent(state.intent, role)
    if guarded_intent != state.intent:
        logger.info(
            "RoleGuard-L2: intent=%s blocked for role=customer", state.intent
        )
        short_term_memory.add_message(session_id, "assistant", _CUSTOMER_REFUSAL)
        return ChatResponse(answer=_CUSTOMER_REFUSAL, model_used="role-guard")

    state.intent = guarded_intent
    short_term_memory.save_state(session_id, state)

    # ── Route ──────────────────────────────────────────────────────────────
    decision = route_conversation(state, query)
    logger.info("Route: mode=%s intent=%s role=%s", decision.mode, decision.intent, role)

    answer = ""

    # ── Execute MCP workflow (direct DB calls) ─────────────────────────────
    if decision.mode == RouteMode.MCP and decision.intent != "general_inquiry":
        try:
            raw_data = await run_mall_workflow(decision, state)
            if raw_data:
                if qa_engine.is_available():
                    answer = qa_engine.generate_response(query, raw_data, history, role)
                else:
                    answer = raw_data
            else:
                answer = "\u0645\u0634 \u0644\u0627\u0642\u064a \u0628\u064a\u0627\u0646\u0627\u062a \u0645\u0646\u0627\u0633\u0628\u0629. \u0645\u0645\u0643\u0646 \u062a\u0648\u0636\u062d \u0623\u0643\u062a\u0631\u061f"
        except Exception as e:
            logger.error("Workflow error: %s", e)
            answer = f"\u062d\u0635\u0644\u062a \u0645\u0634\u0643\u0644\u0629: {str(e)[:100]}"

    # ── General conversation ───────────────────────────────────────────────
    else:
        if qa_engine.is_available():
            answer = qa_engine.general_response(query, history, role)
        else:
            if role == "customer":
                answer = (
                    "\u0623\u0647\u0644\u0627\u064b! \u0623\u0646\u0627 \u0645\u0633\u0627\u0639\u062f \u0644\u0645\u0639\u064a \u062c\u0631\u0627\u0646\u062f \u0645\u0648\u0644.\n"
                    "\u0645\u0645\u0643\u0646 \u062a\u0633\u0623\u0644\u0646\u064a \u0639\u0646:\n"
                    "- \u0633\u0639\u0631 \u0623\u064a \u0645\u0646\u062a\u062c (\u0645\u062b\u0627\u0644: \u0628\u0643\u0627\u0645 \u0627\u0644\u062b\u0644\u0627\u062c\u0629\u061f)\n"
                    "- \u062a\u0648\u0627\u0641\u0631 \u0645\u0646\u062a\u062c (\u0645\u062b\u0627\u0644: \u0641\u064a \u0645\u0631\u0627\u0648\u062d \u0645\u062a\u0627\u062d\u0629\u061f)\n"
                    "- \u062a\u0635\u0641\u062d \u0641\u0626\u0629 (\u0645\u062b\u0627\u0644: \u0627\u0639\u0631\u0636\u0644\u064a \u0645\u0646\u062a\u062c\u0627\u062a \u0627\u0644\u0645\u0637\u0628\u062e)\n"
                    "- \u062d\u062c\u0632 \u0623\u0648 \u0634\u0631\u0627\u0621 \u0645\u0646\u062a\u062c"
                )
            else:
                answer = (
                    "\u0623\u0647\u0644\u0627\u064b \u0645\u062f\u064a\u0631\u0646\u0627!\n"
                    "\u0645\u0645\u0643\u0646 \u062a\u0633\u0623\u0644\u0646\u064a \u0639\u0646:\n"
                    "- \u062a\u0642\u0631\u064a\u0631 \u0627\u0644\u0645\u0628\u064a\u0639\u0627\u062a\n"
                    "- \u0627\u0644\u0623\u0631\u0628\u0627\u062d \u0648\u0627\u0644\u0625\u064a\u0631\u0627\u062f\u0627\u062a\n"
                    "- \u0623\u0643\u062b\u0631 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a \u0645\u0628\u064a\u0639\u0627\u064b\n"
                    "- \u0645\u0646\u062a\u062c\u0627\u062a \u0642\u0631\u064a\u0628\u0629 \u0645\u0646 \u0627\u0644\u0646\u0641\u0627\u062f\n"
                    "- \u0645\u0644\u062e\u0635 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a"
                )

    short_term_memory.add_message(session_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        model_used=os.getenv("LLM_MODEL", "direct-db"),
    )


@router.get("/health")
async def chat_health():
    llm_ok = qa_engine.is_available()
    key = os.getenv("OPENAI_API_KEY", "")
    return {
        "status": "ok",
        "ai_available": llm_ok,
        "api_key_set": bool(key and key != "your_openai_api_key_here"),
        "mall": os.getenv("MALL_NAME", "\u0644\u0645\u0639\u064a \u062c\u0631\u0627\u0646\u062f \u0645\u0648\u0644"),
        "mode": "llm+db" if llm_ok else "db-only (keyword routing)",
    }