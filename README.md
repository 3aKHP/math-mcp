# Symath-MCP

[![PyPI](https://img.shields.io/pypi/v/symath-mcp)](https://pypi.org/project/symath-mcp/)
[![License: MIT](https://img.shields.io/github/license/3aKHP/math-mcp)](LICENSE)

**Language / 语言:** [English](#english) | [中文](#中文)

---

<a id="english"></a>

## English

Symath MCP Server — symbolic computation, calculus, linear algebra, number theory, statistics, and unit conversion via the Model Context Protocol.

### Quick Start

#### stdio (Claude Desktop / Claude Code)

```bash
pip install symath-mcp
```

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "math": {
      "command": "symath-mcp"
    }
  }
}
```

#### Streamable HTTP (server mode)

```bash
pip install symath-mcp
symath-mcp --transport streamable-http
```

Or with Docker:

```bash
docker compose up -d
```

The server listens on `http://127.0.0.1:5109/mcp` by default.

### Tools

| Tool | Description |
|------|-------------|
| `math_eval` | Evaluate mathematical expressions with arbitrary precision |
| `math_solve` | Solve equations and systems (algebraic, differential) |
| `math_calculus` | Integration, differentiation, limits, series |
| `math_matrix` | Eigenvalues, SVD, LU/QR decomposition, linear solve |
| `math_manipulate` | Simplify, expand, factor, partial fractions |
| `math_number_theory` | Prime factorization, GCD/LCM, Fibonacci, CRT |
| `math_statistics` | Descriptive stats, regression, probability distributions |
| `math_convert` | Unit conversion and physical constants |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Bind address (streamable-http mode) |
| `PORT` | `5109` | Listen port (streamable-http mode) |

### License

MIT

---

<a id="中文"></a>

## 中文

Symath MCP 服务器 — 通过 Model Context Protocol 提供符号计算、微积分、线性代数、数论、统计和单位换算。

### 快速开始

#### stdio 模式（Claude Desktop / Claude Code）

```bash
pip install symath-mcp
```

在 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "math": {
      "command": "symath-mcp"
    }
  }
}
```

#### Streamable HTTP 模式（服务器）

```bash
pip install symath-mcp
symath-mcp --transport streamable-http
```

或使用 Docker：

```bash
docker compose up -d
```

默认监听 `http://127.0.0.1:5109/mcp`。

### 工具列表

| 工具 | 说明 |
|------|------|
| `math_eval` | 计算数学表达式，支持任意精度 |
| `math_solve` | 求解方程/方程组（代数、微分） |
| `math_calculus` | 积分、求导、极限、级数展开 |
| `math_matrix` | 特征值、SVD、LU/QR 分解、线性方程组 |
| `math_manipulate` | 化简、展开、因式分解、部分分式 |
| `math_number_theory` | 质因数分解、GCD/LCM、斐波那契、中国剩余定理 |
| `math_statistics` | 描述性统计、回归、概率分布 |
| `math_convert` | 单位换算与物理常数查询 |

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | 绑定地址（streamable-http 模式） |
| `PORT` | `5109` | 监听端口（streamable-http 模式） |

### 许可证

MIT
