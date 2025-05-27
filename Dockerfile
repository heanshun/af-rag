# 使用阿里云镜像源的Python基础镜像
FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.9-slim

# 设置pip国内源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV MONGO_USERNAME=admin \
    MONGO_PASSWORD=Class123! \
    MILVUS_HOST=milvus-standalone \
    MILVUS_PORT=19530

# 启动命令
CMD ["python", "-m", "tests.pikerag.workflows.web_app"]