"""
math_mcp.server
Math MCP 服务器入口。
创建 FastMCP 实例并注册所有工具模块。
"""
from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# ── MCP 服务器 ──────────────────────────────────────────────────────────────────

_port = int(os.environ.get("PORT", 5109))
_host = os.environ.get("HOST", "127.0.0.1")
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp = FastMCP(
    "mcp-math",
    host=_host,
    port=_port,
    streamable_http_path="/mcp",
    transport_security=_transport_security,
)

# ── 导入工具模块（注册工具）────────────────────────────────────────────────────

from . import _symbolic  # noqa: E402, F401
from . import _matrix  # noqa: E402, F401
from . import _number_theory  # noqa: E402, F401
from . import _statistics  # noqa: E402, F401
from . import _convert  # noqa: E402, F401

# 重新导出工具函数（便于测试和外部导入）
from ._symbolic import math_eval, math_solve, math_calculus, math_manipulate  # noqa: F401
from ._matrix import math_matrix  # noqa: F401
from ._number_theory import math_number_theory  # noqa: F401
from ._statistics import math_statistics  # noqa: F401
from ._convert import math_convert  # noqa: F401

# ── 入口 ────────────────────────────────────────────────────────────────────────


def main():
    """CLI 入口：支持 stdio 和 streamable-http 两种传输模式。"""
    import argparse

    parser = argparse.ArgumentParser(description="Math MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="传输模式 (默认: stdio)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
