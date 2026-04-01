# Doraemon 对标 Claude Code 演进路线

## 目的

把当前 Doraemon 从“单 agent + 统一工具面”的产品，演进到更接近 Claude Code 的“统一 runtime + 多入口 + 可编排 agent 平台”。

这里的对标不是照搬产品外形，而是补齐真正影响上限的组织层级：

- 单 runtime，而不是每个入口各自拼装
- 多入口一致，而不是只有 CLI 是一等公民
- 工具可治理，而不是只有工具可调用
- 支持编排，而不是只有单 agent 回合循环

---

## 一、当前架构

### 当前主链路

```text
CLI
  -> AgentSession
    -> DoraemonAgent(ReActAgent)
      -> ToolRegistry
        -> read / write / search / run / memory_*
      -> Hooks
      -> Checkpoints
      -> Trace
      -> Skills
```

### 当前优点

- 主运行时已经收敛到单一 `AgentSession + DoraemonAgent`
- 工具面已经统一到 `read / write / search / run`
- 已经具备 hooks、trace、checkpoint、permission、MCP extension 等平台基础件
- `plan / build` 模式已经是产品层概念，而不是裸 prompt 拼接

### 当前短板

- 只有单 agent 执行主链，没有 lead/worker 编排层
- CLI 是主入口，IDE / automation / remote control 不是同等级入口
- 工具注册表有了，但“工具治理层”还不够强
  - approval / sandbox / policy 还没有成为产品骨架
  - custom command / scheduled task / background job 还不是一等能力
- 缺少统一的项目上下文协议
  - 有 skills / config / memory
  - 但没有类似 `CLAUDE.md` 的跨入口统一控制面
- eval、host、automation 虽然都能接 runtime，但还没有强约束成同一 contract

### 当前定位

一句话：现在更像“会调用工具的单 coding agent”，还不是“agent 平台”。

---

## 二、Claude Code 式目标架构

### 目标形态

```text
Unified Runtime
├─ Interaction Surfaces
│  ├─ CLI
│  ├─ IDE
│  ├─ Web / Remote
│  └─ Automation / Scheduled Tasks
├─ Agent Runtime
│  ├─ Lead Agent
│  ├─ Worker Agents
│  ├─ Session / Trace / Memory
│  └─ Planning / Execution Orchestration
├─ Tool Governance Layer
│  ├─ Tool Registry
│  ├─ Permission Policy
│  ├─ Sandbox / Approval
│  ├─ Hooks / Commands
│  └─ MCP / Extensions
├─ Context Layer
│  ├─ Project Instructions
│  ├─ User Settings
│  ├─ Skills
│  └─ Long/Short-term Memory
└─ Product Protocol Layer
   ├─ Shared agent/session contract
   ├─ Shared tool contract
   └─ Shared event / trace contract
```

### 目标关键变化

1. 从“单 agent 调工具”升级为“runtime 编排 agent + 工具”
2. 从“CLI 优先”升级为“多入口共用一个 runtime”
3. 从“工具可用”升级为“工具可治理、可审计、可限制、可自动化”
4. 从“上下文分散”升级为“统一项目协议 + 用户协议 + 记忆层”

---

## 三、差距分析

### 1. 运行时层

现状：

- `AgentSession` 驱动单个 `DoraemonAgent`
- `plan/build` 只是工具能力差异

目标：

- 引入 `LeadAgentRuntime`
- 支持把任务拆成子任务，再分配给 worker agents
- 支持串行、并行、回收、失败重试、结果汇总

结论：

- 当前不是多 agent runtime
- 这是和 Claude Code 的最大结构差距之一

### 2. 入口层

现状：

- CLI 是标准入口
- 其他入口还没形成同级 surface

目标：

- CLI / IDE / automation / remote 全都走同一 session contract
- 不允许每个入口自己拼一套 agent 初始化逻辑

结论：

- 现在的 runtime 可以复用，但“入口一致性”还不够

### 3. 工具治理层

现状：

- 已有统一 tool registry
- 已有 hooks、checkpoint、permission、MCP extension

目标：

- 明确 tool policy 层
- 把 approval、sandbox、tool visibility、tool auditing 提升到产品一等概念
- 支持 custom commands、scheduled tasks、background executions

结论：

- 基础不错，但还没形成治理闭环

### 4. 上下文层

现状：

- 有 project config、skills、memory、user settings

目标：

- 统一为“项目级上下文协议”
- 明确定义优先级：
  - project instructions
  - repo policy
  - user settings
  - runtime mode
  - memory

结论：

- 缺少一个对外稳定、对内统一的上下文控制面

### 5. 协议层

现状：

- host / eval / session / agent 之间已经在收敛

目标：

- 统一 event schema、tool schema、session schema、trace schema
- 所有入口和自动化都消费同一协议

结论：

- 这是平台化的基础，目前值得继续强化

---

## 四、三期演进路线

## Phase 1: 把单 agent 产品做成统一 runtime

目标：

- 所有入口只允许通过统一 runtime 创建 session
- 固化 tool/session/trace contract
- 把项目上下文统一起来

要做的事：

- 抽出统一 `RuntimeFactory`
- 禁止 CLI、eval、automation 私自拼装 agent / registry / hooks
- 增加统一 `ProjectContext`
  - 项目指令
  - 用户设置
  - mode
  - skills
  - memory
- 统一 event / trace schema
- 明确 tool visibility 和 policy 接口

交付标准：

- CLI、eval、未来 IDE 入口都走同一套初始化链
- session 初始化只有一个真源头
- context 注入顺序稳定且可测试

为什么先做这个：

- 不先统一 runtime，后面加多 agent 会把分叉逻辑放大

---

## Phase 2: 把工具系统升级为治理系统

目标：

- 工具不只是“能调用”，而是“可配置、可限制、可审计、可编排”

要做的事：

- 增加 `ToolPolicyEngine`
  - mode visibility
  - approval rules
  - sandbox class
  - audit level
- 把 hooks 升级为正式扩展点
  - pre_tool
  - post_tool
  - pre_turn
  - post_turn
  - approval interception
- 引入 custom commands
- 引入 scheduled/background tasks
- MCP extension 元数据标准化

交付标准：

- 每个工具都能回答：
  - 谁能看见
  - 谁能执行
  - 是否审批
  - 在什么沙箱里运行
  - 如何被审计

为什么这是第二期：

- Claude Code 的平台感，很大部分来自工具治理，而不只是多 agent

---

## Phase 3: 引入多 agent 编排层

目标：

- 从单 agent 升级为可编排 runtime

建议架构：

```text
LeadAgentRuntime
├─ Planner
├─ Task Graph
├─ WorkerAgentPool
├─ Result Aggregator
└─ Shared Context + Shared Policy
```

要做的事：

- 定义 `LeadAgent`
  - 负责任务拆分、分发、合并
- 定义 `WorkerAgent`
  - 负责单子任务执行
- 定义 `TaskGraph`
  - dependency
  - retry
  - timeout
  - cancellation
- 定义 worker tool scope
  - 每个 worker 能见到哪些工具
  - 是否共享写权限
- 定义 merge 规则
  - patch merge
  - summary merge
  - trace merge

交付标准：

- 简单任务仍走单 agent
- 复杂任务可自动转多 agent
- 多 agent 全链路 trace 可回放

为什么放第三期：

- 没有统一 runtime 和 tool governance，先上多 agent 只会把系统复杂度失控

---

## 五、建议落地顺序

最建议的实际顺序：

1. 先统一 runtime factory 和 project context
2. 再统一 tool policy / approval / sandbox / audit
3. 然后做 automation surface
4. 最后才做 lead/worker 多 agent

不建议的顺序：

- 直接做 swarm
- 先堆更多工具
- 先做 UI 壳子

原因：

- 这些都不能真正提高平台上限，只会增加表面复杂度

---

## 六、最小可执行版本

如果只做最关键的一小步，建议先完成下面这 4 件事：

1. 新建统一 `RuntimeFactory`
   - 所有入口统一创建 session / registry / hooks / checkpoints / skills
2. 新建 `ProjectContext`
   - 统一项目级指令、mode、settings、skills、memory
3. 新建 `ToolPolicyEngine`
   - 把 visibility / approval / sandbox 统一管理
4. 为 future multi-agent 预留 `LeadAgentRuntime` 接口
   - 先不实现 swarm
   - 先把接口边界定下来

---

## 七、成功标准

如果未来演进成功，应该出现这几个外部信号：

- 新增入口时，不再复制 agent 初始化代码
- 新增工具时，不再手工分散修改权限和暴露逻辑
- 复杂任务可以自然落到 orchestrated execution
- trace 能解释单 agent 和多 agent 两种执行路径
- eval、CLI、IDE、automation 的行为差异显著收敛

---

## 八、简短判断

当前 Doraemon 已经走完了“统一工具面”的关键一步。

下一阶段真正该补的，不是更多工具，也不是更花的 UI，而是：

- 统一 runtime
- 统一 context
- 统一 tool governance
- 最后再上多 agent orchestration

这条路线做对了，才会从“单 agent 产品”变成“agent 平台”。
