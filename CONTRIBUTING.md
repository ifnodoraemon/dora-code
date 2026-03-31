# Contributing

## Setup

```bash
git clone https://github.com/ifnodoraemon/dora-code.git
cd dora-code
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Before Opening a PR

运行最少这几项：

```bash
ruff check src/ tests/
ruff format src/ tests/
pytest tests/ -v
```

如果改动涉及 provider / eval / MCP，补一条最小真实回归。

## Scope Rules

- 不保留已经废弃的兼容层
- 不把新能力直接塞进默认 built-in 主链
- browser / database / 外部系统能力优先放到 MCP extensions
- 文档只描述当前行为，不描述已经删除的历史结构

## Commit Rules

- 每个独立改动单独提交
- commit message 直接说明行为变化
- 不要把无关脏改动混进同一个提交
