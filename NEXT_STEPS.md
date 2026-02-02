# Doraemon Code - 下一步行动计划

## 🎯 当前状态

✅ **加固计划完成** - 所有 16 个任务完成  
✅ **测试覆盖率** - 30.27%  
✅ **评估系统设计** - 完整框架和最佳实践  
✅ **评估任务创建** - 15+ 任务已创建

## 📋 立即可执行的任务

### 1. 运行评估套件 ⚡

```bash
# 列出所有评估任务
python scripts/run_evals.py --list

# 运行基础任务
python scripts/run_evals.py --category basic

# 运行高级任务
python scripts/run_evals.py --category advanced

# 运行对抗性测试
python scripts/run_evals.py --category adversarial

# 运行所有任务
python scripts/run_evals.py --all --trials 3
```

### 2. 提升测试覆盖率 📈

**目标：30% → 70%+**

**优先级文件：**
```bash
# 1. main.py (当前 0%)
pytest tests/host/test_main.py --cov=src/host/cli/main.py

# 2. context_manager.py (当前 42%)
pytest tests/core/test_context_manager.py --cov=src/core/context_manager.py

# 3. planner.py (当前 0%)
pytest tests/core/test_planner.py --cov=src/core/planner.py

# 4. skills.py (当前 0%)
pytest tests/core/test_skills.py --cov=src/core/skills.py
```

**快速提升策略：**
```python
# 为每个未覆盖的模块创建基础测试
# 1. 测试初始化
# 2. 测试主要方法
# 3. 测试错误处理
# 4. 测试边界条件
```

### 3. 扩展评估数据集 📊

**当前：15 个任务**  
**目标：100+ 个任务**

**任务分类：**
- ✅ Basic (5 个文件操作 + 5 个代码生成) = 10 个
- ✅ Advanced (3 个重构 + 3 个调试) = 6 个
- ✅ Adversarial (3 个安全测试) = 3 个

**待创建：**
- [ ] Basic: 命令执行 (5 个)
- [ ] Basic: 信息检索 (5 个)
- [ ] Advanced: 性能优化 (5 个)
- [ ] Advanced: 架构设计 (5 个)
- [ ] Adversarial: 边缘案例 (10 个)
- [ ] Adversarial: 误导输入 (10 个)

### 4. CI/CD 集成 🔄

```yaml
# .github/workflows/eval.yml
name: Continuous Evaluation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 每日运行

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run evaluations
        run: python scripts/run_evals.py --all
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: eval-results
          path: eval_results/
```

## 🚀 快速开始

### 选项 A: 提升测试覆盖率（推荐）

```bash
# 1. 创建测试文件
touch tests/host/test_main_functions.py

# 2. 编写测试
cat > tests/host/test_main_functions.py << 'EOF'
import pytest
from src.host.cli.main import build_system_prompt

def test_build_system_prompt():
    prompt = build_system_prompt("build")
    assert "build" in prompt.lower()
    assert len(prompt) > 0
