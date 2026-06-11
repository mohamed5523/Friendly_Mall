"""MCP Server entry point."""
import sys, os
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(env_path, override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from mall_server import mcp

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8501"))
    if hasattr(mcp, "run") and "port" in mcp.run.__code__.co_varnames:
        mcp.run(transport="streamable-http", port=port)
    elif "PORT" not in os.environ:
        os.environ["PORT"] = str(port)
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="streamable-http", port=port)
