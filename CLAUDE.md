# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Math-MCP is an MCP Server providing symbolic math computation via SymPy. Single Python implementation, dual transport (stdio + streamable-http).

## Commands

```bash
# Install in editable mode
pip install -e .

# Run tests
pytest tests/ -v

# Run server (stdio, default)
math-mcp

# Run server (streamable-http)
math-mcp --transport streamable-http

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
