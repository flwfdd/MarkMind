# MarkMind 文档导入功能

## 功能总结

我们已经实现了完整的文档导入功能，分为以下几个部分：

### 后端实现

1. **解析端点 (`/api/ingest/parse`)**
   - 支持URL解析（HTML自动转MD或PDF）
   - 支持文件上传（PDF、TXT、MD、HTML）
   - 自动提取标题和内容

2. **预览端点 (`/api/ingest/preview`)**
   - 生成文档摘要
   - 使用LLM提取概念和关系
   - 匹配现有概念，避免重复
   - 返回预览数据供前端确认

3. **确认导入端点 (`/api/ingest/confirm`)**
   - 存储文档
   - 创建文本chunks
   - 创建或链接概念
   - 建立概念关系
   - 完整持久化到数据库

4. **文件处理增强**
   - `fetch_url_content`: 从URL获取内容
   - 支持HTML转Markdown
   - 支持PDF文本提取
   - 自动识别文件类型

5. **概念提取优化**
   - `extract_concepts`函数接受现有概念列表
   - 在system prompt中提供现有概念
   - 优先重用现有概念名称
   - 减少概念重复

### 前端实现

1. **ImportWizard组件**
   - 两步向导界面
   - 第一步：输入信息
     - URL输入和解析
     - 文件上传
     - 手动输入
   - 第二步：预览确认
     - 编辑文档信息
     - 管理提取的概念
     - 查看匹配的现有概念
     - 编辑概念关系

2. **LibraryView更新**
   - 新增"智能导入"按钮
   - 保留原有"快速上传"功能
   - 导入成功后自动刷新列表

3. **API函数**
   - `parseDocument`: 解析文档
   - `previewDocument`: 生成预览
   - `confirmImport`: 确认导入

### 数据模型

新增的Pydantic模型：
- `ParseRequest/ParseResponse`: 解析请求/响应
- `ExtractedConcept`: 提取的概念
- `ExtractedRelation`: 提取的关系
- `DocumentPreview`: 文档预览
- `ConfirmImportRequest`: 确认导入请求

## 使用流程

1. 用户点击"智能导入"按钮
2. 输入URL或上传文件，点击"解析"自动填充
3. 可以手动调整标题、内容、类型
4. 点击"下一步"，后端生成预览
5. 前端显示：
   - 文档摘要
   - 提取的概念（可编辑）
   - 匹配的现有概念
   - 概念关系（可编辑）
6. 用户确认或修改后，点击"确认导入"
7. 后端完整处理并存储到数据库
8. 前端刷新文档列表

## 优势

1. **智能化**：自动识别和提取关键信息
2. **灵活性**：支持多种输入方式和格式
3. **可控性**：导入前预览和编辑
4. **一致性**：优先重用现有概念
5. **完整性**：包含文档、概念、关系的完整处理

## 技术栈

- 后端：FastAPI、Pydantic、LangChain、aiohttp、markdownify
- 前端：Vue 3、TypeScript、Composition API
- 数据库：SurrealDB（通过现有database.py操作）
