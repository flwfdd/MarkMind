# MarkMind Backend

## 1. 项目背景与目标

构建一个本地化、隐私优先的个人知识库系统（MVP）。
系统支持用户上传 Markdown、PDF 或自动导入如小红书笔记（暂时不需要实现）。系统需对文档进行处理，提取知识图谱，并支持混合检索（Graph RAG）。
**核心约束**：

  - **极简架构**：只保留最核心功能，不增加非必要实体。
  - **图谱单位**：知识图谱的可视化基础单位是 **文档 (Document)** 和 **概念 (Concept)**，而不是切片 (Chunk)。切片仅用于底层高精度检索。
  - **存储**：SurrealDB。
  - **向量维度**：统一使用 **1024** 维。

## 2. 技术栈

  - **Language**: Python
  - **Framework**: FastAPI
  - **Database**: SurrealDB (使用 `surrealdb` 和 `langchain-surrealdb` Python SDK)
  - **Orchestration**: LangGraph
  - **LLM/Embeddings**: OpenAI Compatible API (LLM), 兼容 1024 维的 Embedding 模型 。

## 3. 数据库设计 (SurrealDB Schema)

### 3.1 节点表 (Vertices)

#### `doc` (核心图谱节点)

存储文档的完整信息，用于图谱展示和原文溯源。

  - `id`: `doc:<random_id>`
  - `title`: string (标题)
  - `summary`: string (LLM 生成的摘要，用于图谱 Hover 展示)
  - `content`: string (全文内容，用于详情页展示)
  - `type`: string (`pdf`, `md`, `xhs`, `text`)
  - `created_at`: datetime
  - `embedding`: array<float, 1024> (文档级向量，用于粗粒度推荐)
  - `meta`: object (包含 url, author 等 type 相关元数据)

#### `concept` (核心图谱节点)

从文档中提取的关键知识点或实体。

  - `id`: `concept:<name_with_underscores>` (直接用概念名做 ID，实现自动去重)
  - `desc`: string (一句话定义)
  - `embedding`: array<float, 1024> (概念向量，用于模糊搜索)

#### `chunk` (底层检索单元 - 不在图谱中展示)

用于高精度的语义搜索（RAG），挂载在 doc 下。

  - `id`: `chunk:<random_id>`
  - `text`: string (切片文本)
  - `embedding`: array<float, 1024> (切片向量)
  - `source`: record<doc> (指向所属文档)

### 3.2 边关系表 (Edges)

#### `mentions` (连接 文档 -> 概念)

表示该文档核心讨论了哪些概念。这是图谱可视化的主要连线。

  - `in`: `doc:<id>`
  - `out`: `concept:<id>`
  - `desc`: string

#### `related` (连接 概念 <-> 概念)

表示知识点之间的关联（如 "包含", "对立", "相关"）。

  - `in`: `concept:<id>`
  - `out`: `concept:<id>`
  - `desc`: string

-----

## 4. 核心 API 接口定义

请实现以下 RESTful API：

### A. 数据摄入 (`/api/ingest`)

**1. `POST /api/ingest/upload`**

  - **功能**: 处理文件上传或文本导入。
  - **输入**: Multipart File 或 JSON `{title, content, type, ...}`
  - **处理流程 (Pipeline)**:
    1.  **Store Doc**: 将原文存入 `doc` 表，生成 `summary` 和 `doc_embedding`。
    2.  **Chunking**: 将全文切分为 `chunk`，计算 `chunk_embedding` 并存入 `chunk` 表。
    3.  **Graph Extraction (LLM)**: 基于全文或摘要，提取关键 `Concept` 和 `Mentions` 关系。
          - 写入 `concept` 表 (如果 ID 已存在则忽略或更新)。
          - 建立 `mentions` 边 (`doc` -> `concept`)。
    4.  **Concept Linking**: (可选) 让 LLM 分析新 Concept 之间的关系，建立 `related` 边。

### B. 图谱交互 (`/api/graph`)

**2. `GET /api/graph/overview`**

  - **功能**: 获取全量图谱数据。
  - **返回**: 所有的 `doc` 节点、`concept` 节点以及 `mentions`、`related` 边。
  - **数据结构**: 适配前端图形库 (如 G6) 的标准 JSON `{nodes: [], edges: []}`。

**3. `GET /api/graph/node/{node_id}`**

  - **功能**: 获取节点详情及相关推荐。
  - **逻辑**:
      - 如果是 `doc`: 返回 summary + full_text。
      - 如果是 `concept`: 返回 desc。
      - **推荐算法**: 使用当前节点的 embedding 在 `doc` 或 `chunk` 表中进行向量检索 (Vector Search)，返回 Top 5 相关内容，作为"猜你喜欢"。

**4. `POST /api/graph/search`**

  - **功能**: 基于关键词搜索图谱节点。
  - **输入**: `{query: string}`
  - **逻辑**:
      1. 计算 Query 向量 (1024维)。
      2. 在 `chunk` 和 `concept` 表中进行向量搜索，返回最相关的节点列表。


### C. 智能对话 (`/api/chat`)

**5. `POST /api/chat`**

  - **功能**: Agent RAG 对话，ReAct 模式执行，提供基于图谱和向量检索的工具支持。
  - **输入**: `{messages: list}`
  - **逻辑**:
    1.  **Step 1**: 判断是否有 system 消息，没有则添加。
    2.  **Step 2**: 循环执行：
      - Agent 调用工具（图谱查询、向量检索）。
      - 流式返回过程和回答。
      - 直到不再有工具调用。

-----

## 5. 开发注意事项

1.  **异步处理**: 所有数据库操作和 LLM 调用必须是异步的 (`async/await`)。
2.  **Prompt Engineering**: 提取图谱时，强制 LLM 输出 JSON 格式，并对 Concept 名称进行标准化（如转小写，去特殊字符）。
3.  **Mock Data**: 提供一个 `init_db` 函数，用于插入完整模拟测试数据以便快速验证前端效果。