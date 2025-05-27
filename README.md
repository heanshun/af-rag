# PIKE-RAG 项目扩展

## 项目简介

本项目是基于PIKE-RAG的开源项目进行的二次开发。我们在原有框架的基础上，整合了自定义的工作流程，以提升检索增强生成(RAG)系统的性能和实用性。

## 主要特点

- 基于PIKE-RAG的核心功能
- 自定义工作流程优化
- [更多特点待补充]

## 环境配置

### Docker 环境准备

1. 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. 确保 Docker 服务正常运行

### 配置环境变量

1. 在项目根目录创建 `.env` 文件：
```env
MONGO_USERNAME=YOUR_USERNAMAE          # MongoDB 用户名
MONGO_PASSWORD=YOUR_PASSWORD      # MongoDB 密码
MILVUS_HOST=localhost        # Milvus 主机地址
MILVUS_PORT=19530           # Milvus 端口
```

### 启动数据库服务

1. 创建数据存储目录：
```bash
mkdir -p data/mongodb data/milvus
```

2. 启动服务：
```bash
docker-compose up -d
```

3. 验证服务状态：
```bash
docker-compose ps
```

### 验证数据库连接

1. 连接 MongoDB：
```bash
docker exec -it mongodb mongosh -u "YOUR_USERNAMAE" -p "YOUR_PASSWORD!"
```
成功连接后，您将看到 MongoDB shell 提示符。可以执行以下命令测试：
```javascript
show dbs          # 显示所有数据库
use your_db_name  # 切换到指定数据库
show collections  # 显示所有集合
```

2. 验证 Milvus：
Milvus 服务将在 19530 端口运行，可以通过项目代码中的客户端进行连接测试。

### 常见问题

1. 如果遇到权限问题：
   - 确保 Docker Desktop 有足够的权限
   - 检查数据目录的权限设置

2. 如果需要重置数据：
```bash
# 停止服务
docker-compose down

# 清理数据目录
rm -rf data/mongodb/* data/milvus/*

# 重新启动服务
docker-compose up -d
```

3. 查看服务日志：
```bash
# 查看 MongoDB 日志
docker-compose logs mongodb

# 查看 Milvus 日志
docker-compose logs milvus-standalone
```

## 工作流程

## 环境准备
1. 确保已安装 Docker 和相关依赖
2. 启动必要的服务:
   - Docker 服务
   - Milvus 向量数据库服务
   - MongoDB 数据库服务

## 配置说明
推荐使用阿里云百炼API。
1. 在 `vectorapi\embeddings.py` 中配置API：
   ```python
   API_KEY = "your-api-key"
   ```

2. 配置sk-062f03efe4df47298433b72464c190ce在tests\pikerag\workflows\configs的.yml文件中。

## 运行方式
### 方式一：Web 应用方式（推荐）
1. 启动后端服务：
   ```bash
   python -m tests.pikerag.workflows.web_app
   ```

2. 部署前端界面：
   ```bash
   # 克隆前端项目
   git clone https://github.com/heanshun/af-rag-vue.git
   
   # 进入项目目录
   cd af-rag-vue
   
   # 安装依赖并启动
   npm install
   npm run dev
   ```

3. 前端界面预览：
   
   部署成功后，您将看到如下界面：
   - 左侧为历史对话列表
   - 右侧为当前对话内容
   - 支持查看问答的详细信息，包括回答内容、理由和参考来源
   ![image.png](image.png)

### 方式二：命令行问答方式
直接执行以下命令进行问答测试：

```bash
python -m tests.pikerag.workflows.test_answer tests\pikerag\workflows\configs\mongodb_qa_retriever.yml 0
```

## 贡献

欢迎提交Issue和Pull Request来帮助改进项目。

