# How To Deploy — 本地部署指南

> 从零开始跑通 EmployRAG 企业知识库问答系统

---

## 环境要求

| 工具 | 版本 |
|------|------|
| Docker Desktop | 4.x+ |
| Python | 3.10 ~ 3.13 |
| Node.js | 18+ |
| npm | 9+ |

---

## 第一步：启动基础设施

项目依赖 4 个 Docker 服务：**PostgreSQL**、**Milvus**（向量数据库）、**etcd**（Milvus 依赖）、**MinIO**（Milvus 内部存储）。

```bash
cd Rag_System
docker-compose up -d
```

首次启动需等待 30-60 秒，检查所有服务是否就绪：

```bash
docker-compose ps
```

所有服务显示 `healthy` 后再进行下一步。

> ⚠️ 注意：Milvus 集合名只允许字母、数字、下划线，不要包含中划线或特殊字符。

---

## 第二步：配置环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `.env`，填写必要的变量：

| 变量 | 必填 | 说明 |
|------|------|------|
| `DASHSCOPE_API_KEY` | ✅ | 阿里云 DashScope 的 API Key（通义千问） |
| `PG_HOST` | ✅ | PostgreSQL 地址（Docker 用 `localhost`） |
| `PG_USER` | ✅ | 默认 `kbuser` |
| `PG_PASSWORD` | ✅ | 默认 `kbpass` |
| `MILVUS_HOST` | ✅ | Milvus 地址（Docker 用 `localhost`） |

**其他变量（无需修改可保持默认）：**

- `EMBEDDING_MODEL=text-embedding-v3` — 向量化模型
- `EMBEDDING_BATCH_SIZE=10` — 注意：`text-embedding-v3` 单批次上限 10 条
- `CHUNK_SIZE=500` — 切片大小
- `CHUNK_OVERLAP=50` — 切片重叠

> 💡 本项目已改造为**本地文件存储**模式，即使没有阿里云 OSS 也可正常上传文件。文件保存在 `backend/local_storage/` 目录。

---

## 第三步：启动后端

### 3.1 创建虚拟环境（推荐）

```bash
cd Rag_System/backend
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
# 或
source venv/bin/activate      # macOS / Linux
```

### 3.2 安装依赖

```bash
pip install -r requirements.txt
pip install "psycopg[binary]"        # PostgreSQL 驱动
pip install langgraph-checkpoint-postgres  # LangGraph 持久化检查点
```

### 3.3 启动服务

```bash
cd Rag_System/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端运行在 `http://localhost:8000`，启动时会自动：

1. 检查环境变量配置
2. 初始化 PostgreSQL 表结构
3. 初始化 LangGraph checkpointer

如看到 `应用启动完成` 的日志，说明启动成功。

> ⚠️ 使用 `python main.py` 而不是 `uvicorn` 可能导致启动失败。
>
> ⚠️ 如果报错 "Collection name contains invalid characters"，说明知识库名称有中文或特殊字符，改为英文+下划线即可。

---

## 第四步：启动前端

```bash
cd Rag_System/frontend
npm install
npm run dev
```

前端运行在 `http://localhost:5173`，浏览器打开即可。

> 前端通过 Vite 代理（`/api` → `http://localhost:8000`）与后端通信，无需单独配置跨域。

---

## 第五步：使用系统

### 创建第一个知识库

1. 点击左侧导航 **知识库** → 点击 **创建知识库**
2. 填写名称（英文+下划线，如 `my_kb`）
3. 选择 Embedding 模型（默认 `text-embedding-v3`）
4. 点击创建

### 上传文档

1. 进入 **类目管理**，创建一个类目
2. 进入该类目，上传文件（PDF、DOCX、TXT、Excel 均可）
3. 点击 **开始切分**
4. 在 **知识库** → **文件列表** 中查看切分状态
5. 点击 **上传向量库** 手动触发向量化

### 智能问答

1. 点击左侧导航 **智能对话**
2. 切换到 **知识库** 模式
3. 选择刚创建的知识库
4. 输入问题，等待 RAG 检索回答

---

## 常见问题

### Milvus 启动慢？

首次启动需要初始化 etcd 和 MinIO，等 `docker-compose ps` 显示 `healthy` 后再启动后端。

### Embedding 报 batch size 错误？

`text-embedding-v3` 单批上限 10 条，检查 `.env` 中 `EMBEDDING_BATCH_SIZE=10`。

### 上传同名文件报错？

设计如此——防止静默覆盖。先在文件列表删除旧版本，再重新上传。

### 文件名含中文书名号 `《》` 导致失败？

文件系统正则校验不支持 `《》`，重命名文件后再上传。

### 前端报错 `[object Object]`？

已通过 `v1.0` 修复。如果仍然出现，检查后端是否正确返回了 JSON 错误信息。

### Rerank 如何开启？

在知识库检索配置中将 `rerank_enabled` 设为 `true`，确认 DashScope 已开通 `qwen3-rerank` 权限。多模态知识库会自动跳过 rerank。

---

## 端口一览

| 服务 | 端口 |
|------|------|
| 后端 API | 8000 |
| 前端界面 | 5173 |
| PostgreSQL | 5432 |
| Milvus | 19530 |
| Attu（Milvus GUI） | 8080 |
| MinIO Console | 9001 |

---

## 技术架构

```
用户 → 前端 (Vue 3 + Element Plus)
              ↕ HTTP / SSE
           FastAPI 后端
              ↕
        LangGraph Agent
    ┌───────┼───────┬──────┐
    ↓       ↓       ↓      ↓
  PostgreSQL Milvus LLM  文件系统
  (业务数据) (向量)  (DashScope) (local_storage/)
```

RAG 流水线：`query_rewrite → query_classify → retrieve → rerank → generate → quality_check`
