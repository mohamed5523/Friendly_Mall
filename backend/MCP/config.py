"""Mall MCP Server config."""
from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv()

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("MCP_PORT", "8001"))
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
MALL_NAME = os.getenv("MALL_NAME", "لمعي جراند مول")
