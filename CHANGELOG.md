# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- **Modular architecture**: Split monolithic `server.py` (1317 lines) into focused modules:
  - `_parse.py`: Expression parsing and data validation utilities
  - `_symbolic.py`: Core symbolic computation tools (eval, solve, calculus, manipulate)
  - `_matrix.py`: Linear algebra operations
  - `_number_theory.py`: Number theory functions
  - `_statistics.py`: Statistical analysis and probability distributions
  - `_convert.py`: Unit conversion and physical constants
  - `server.py`: Thin orchestrator (~50 lines) that creates FastMCP instance and imports all tool modules
- Tool functions remain accessible from `math_mcp.server` for backward compatibility
- Updated CLAUDE.md with architecture documentation

## [0.1.0] - 2026-05-22

### Added

- Initial release
- 8 MCP tools: `math_eval`, `math_solve`, `math_calculus`, `math_matrix`, `math_manipulate`, `math_number_theory`, `math_statistics`, `math_convert`
- Dual transport: stdio (default) and streamable-http
- Docker support
- 56 unit tests
