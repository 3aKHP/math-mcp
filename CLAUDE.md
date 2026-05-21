# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Math-MCP is an MCP Server providing symbolic math computation via SymPy. Single Python implementation, dual transport (stdio + streamable-http).

## Architecture

```
src/math_mcp/
├── server.py              # MCP 入口 + FastMCP 实例
├── _parse.py              # 共享解析工具 (_parse, _parse_matrix 等)
├── _symbolic.py           # 符号计算工具 (eval, solve, calculus, manipulate)
├── _matrix.py             # 矩阵与线性代数
├── _number_theory.py      # 数论工具
├── _statistics.py         # 统计与概率分布
└── _convert.py            # 单位换算与物理常数
```

**设计原则**:
- 每个子模块只导入所需的 SymPy 函数
- `_parse.py` 提供共享的表达式解析和数据解析
- `server.py` 创建 FastMCP 实例，子模块通过 `from .server import mcp` 获取并注册工具
- 工具函数同时从 `server.py` 重新导出，便于测试和外部导入

## Commands

```bash
# Install in editable mode
pip install -e .

# Run tests
pytest tests/ -v

# Run server (stdio, default)
symath-mcp

# Run server (streamable-http)
symath-mcp --transport streamable-http

# Syntax check
python -m py_compile src/math_mcp/server.py
```

## Commit Convention

[Conventional Commits](https://www.conventionalcommits.org/): `feat` / `fix` / `refactor` / `docs` / `chore` / `test` / `style` / `perf`

## Version Sync

When bumping version, update:

| File | Field |
|------|-------|
| `src/math_mcp/__init__.py` | `__version__` |
| `CHANGELOG.md` | new entry |

## Known Constraints

- SymPy is the sole compute backend; no fallback for unsupported operations
- `math_statistics` distribution queries use a custom parameter parser, not SymPy's native API
- Temperature conversion has special-case handling separate from the SI factor table
