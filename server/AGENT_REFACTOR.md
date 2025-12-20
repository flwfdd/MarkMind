# Agent 对话模块重构说明

## 主要改进

### 1. 消息格式规范化
- 返回消息符合后端原始格式，便于前端拼接历史
- SSE 事件类型：
  - `message_delta`: 流式更新内容增量
  - `message_complete`: 单条消息完成（完整消息）
  - `round_complete`: 一轮对话结束（完整历史）
  - `error`: 错误消息

### 2. 工具调用显示优化
- 工具调用嵌套在 assistant 消息中，可折叠
- 工具结果单独显示为 tool 消息，也可折叠
- ReAct 流程中的多条消息独立显示
- 默认折叠状态，减少干扰

### 3. Markdown 渲染支持
- User 和 Assistant 消息支持完整 Markdown 渲染
- 支持特殊格式嵌入节点：`[[node:doc:abc123|Display Name]]`
- 节点引用显示为可点击的徽章
- 加入上下文时使用节点引用格式

### 4. UI 改进
- 移除用户和 AI 头像，界面更简洁
- 修复流式显示逻辑，所有消息正确流式输出
- 添加清空对话功能
- 改进消息布局和样式

### 5. Langfuse 集成
- 后端支持 Langfuse LLM 可观测性
- 通过环境变量配置启用
- 可选功能，不影响核心功能

## 配置说明

### 后端 (.env)
```bash
# Langfuse Configuration (可选)
LANGFUSE_ENABLED=true
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 前端
无需额外配置，已安装 `markdown-it` 用于 Markdown 渲染。

## 技术栈

### 后端
- **LangGraph**: 使用 `create_react_agent` 实现 ReAct 模式
- **LangChain**: 工具调用和消息处理
- **Langfuse**: LLM 可观测性（可选）

### 前端
- **Vue 3**: Composition API
- **markdown-it**: Markdown 渲染
- **Tailwind CSS**: 样式

## 使用示例

### 节点引用格式
在对话中引用知识图谱节点：
```markdown
我想了解 [[node:doc:abc123|这个文档]] 的内容
相关概念：[[node:concept:machine_learning]]
```

显示效果：带边框的彩色徽章，鼠标悬停可高亮知识图谱。

### 清空对话
点击输入框左侧的垃圾桶图标即可清空当前对话历史。

## 最佳实践

1. **消息历史管理**：前端保存 `round_complete` 事件返回的完整历史
2. **流式显示**：使用 `message_delta` 实现实时反馈
3. **工具调用**：默认折叠，用户可展开查看详情
4. **节点引用**：使用统一格式，便于解析和渲染
