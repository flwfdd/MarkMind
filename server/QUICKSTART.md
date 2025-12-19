# MarkMind 后端快速启动指南

## 一键启动脚本（开发环境）

### 前置要求

1. **Python >= 3.11**
2. **SurrealDB** - 安装方式：
   ```bash
   # macOS
   brew install surrealdb/tap/surreal
   
   # Linux
   curl -sSf https://install.surrealdb.com | sh
   
   # Windows
   iwr https://ps.surrealdb.com -useb | iex
   ```

3. **OpenAI API Key** 或兼容的 API

### 快速启动步骤

#### 1. 安装依赖

```bash
cd server

# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

#### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，配置你的 API Key
# vim .env 或使用你喜欢的编辑器
```

必须配置的关键参数：
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

#### 3. 启动 SurrealDB (开启新终端)

```bash
# 使用内存模式（开发测试用，重启后数据会丢失）
surreal start --log trace --user root --pass root memory

# 或使用文件模式（数据持久化）
surreal start --log trace --user root --pass root file://markmind.db
```

保持这个终端运行。

#### 4. 初始化数据库 (开启新终端)

```bash
cd server
python -m app.init_db
```

这会：
- 创建数据库表结构
- 插入测试数据（3篇关于机器学习的文档）
- 建立知识图谱关系

#### 5. 启动 FastAPI 服务

```bash
cd server
fastapi dev main.py
```

服务将在 http://localhost:8000 启动。

#### 6. 验证运行

浏览器访问：
- 主页: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

或使用 curl：
```bash
# 健康检查
curl http://localhost:8000/health

# 获取知识图谱
curl http://localhost:8000/api/graph/overview
```

## 常见问题

### Q: SurrealDB 连接失败？
确保 SurrealDB 正在运行，检查配置文件中的连接地址。

### Q: 缺少某个 Python 包？
运行 `uv sync` 或 `pip install -e .` 重新安装依赖。

### Q: OpenAI API 调用失败？
检查 `.env` 文件中的 API Key 和 Base URL 是否正确。

### Q: 向量维度不匹配？
确保使用的 embedding 模型支持 1024 维，推荐使用 `text-embedding-3-large`。

## 测试 API

### 1. 上传文档

```bash
# 上传文本
curl -X POST http://localhost:8000/api/ingest/upload \
  -F "title=测试文档" \
  -F "content=这是一个测试文档的内容..." \
  -F "type=text"

# 上传文件
curl -X POST http://localhost:8000/api/ingest/upload \
  -F "file=@/path/to/your/document.pdf" \
  -F "type=pdf"
```

### 2. 搜索知识

```bash
curl -X POST http://localhost:8000/api/graph/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "limit": 5}'
```

### 3. 获取节点详情

```bash
# 使用 overview API 获取的节点 ID
curl http://localhost:8000/api/graph/node/doc:xxxxx
```

### 4. 智能对话

```bash
curl -X POST http://localhost:8000/api/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me about machine learning"}
    ]
  }'
```

## 生产环境部署

生产环境建议：

1. 使用持久化的 SurrealDB 存储
2. 配置合适的 CORS 策略
3. 使用 gunicorn + uvicorn workers
4. 配置反向代理 (Nginx/Caddy)
5. 启用 HTTPS
6. 设置环境变量而非 .env 文件

启动命令示例：
```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 下一步

- 查看 [README.md](README.md) 了解详细架构
- 查看 [prd.md](prd.md) 了解产品设计
- 访问 http://localhost:8000/docs 探索完整 API 文档
