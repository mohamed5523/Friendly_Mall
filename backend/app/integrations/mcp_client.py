"""MCP Client — calls mall_server tools via HTTP."""
from __future__ import annotations
import logging, os
import httpx
from typing import Any, Optional

logger = logging.getLogger(__name__)

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8001")


class MCPClientError(Exception):
    pass


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return the text result."""
    url = f"{MCP_BASE_URL}/mcp"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("result", {}).get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "لا توجد بيانات")
            return str(data.get("result", "لا توجد بيانات"))
    except httpx.TimeoutException:
        raise MCPClientError("انتهت مهلة الاتصال بخادم المول")
    except Exception as e:
        raise MCPClientError(f"خطأ في الاتصال بخادم المول: {e}")
