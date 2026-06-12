"""Mall Intent Router — routes queries to MCP tools."""
from __future__ import annotations
import logging, os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.core.state_manager import MallConversationState

logger = logging.getLogger(__name__)


class RouteMode(str, Enum):
    MCP = "mcp"
    GENERAL = "general"


class RouteDecision(BaseModel):
    mode: RouteMode
    intent: str
    tool_name: Optional[str] = None
    reason: str = ""
    entities_snapshot: dict = Field(default_factory=dict)


# Customer intents
CUSTOMER_TOOL_MAP = {
    "search_product":   "search_products_tool",
    "check_price":      "check_product_price",
    "check_stock":      "check_product_stock",
    "browse_category":  "get_products_by_category_tool",
    "reserve_product":  "reserve_product",
    "buy_product":      "buy_product",
    "check_order":      "check_order_status",
}

# Manager intents
MANAGER_TOOL_MAP = {
    "get_sales_report":    "get_sales_report_tool",
    "get_revenue":         "get_revenue_analysis",
    "get_top_products":    "get_top_selling_products",
    "predict_demand":      "predict_product_demand",
    "predict_sales_trends": "predict_overall_sales_trends",
    "low_stock_alert":     "get_low_stock_alert",
    "product_correlation": "get_product_correlation_insights",
    "manager_insights":    "get_manager_insights",
    "account_summary":     "get_account_summary_tool",
}

ALL_MCP_INTENTS = set(CUSTOMER_TOOL_MAP) | set(MANAGER_TOOL_MAP)


def route_conversation(state: MallConversationState,
                       user_query: str) -> RouteDecision:
    """Determine routing from state intent — no LLM call needed here."""
    intent = state.intent
    entities = state.entities.model_dump()

    # Direct mapping — works with or without LLM
    if intent in CUSTOMER_TOOL_MAP:
        return RouteDecision(
            mode=RouteMode.MCP,
            intent=intent,
            tool_name=CUSTOMER_TOOL_MAP[intent],
            reason="customer intent mapped",
            entities_snapshot=entities,
        )

    if intent in MANAGER_TOOL_MAP:
        return RouteDecision(
            mode=RouteMode.MCP,
            intent=intent,
            tool_name=MANAGER_TOOL_MAP[intent],
            reason="manager intent mapped",
            entities_snapshot=entities,
        )

    # General fallback
    return RouteDecision(
        mode=RouteMode.GENERAL,
        intent="general_inquiry",
        reason="no specific intent detected",
        entities_snapshot=entities,
    )