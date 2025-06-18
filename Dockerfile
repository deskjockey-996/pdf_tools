# 基础镜像
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update --fix-missing && \
    apt-get install -y poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建必要的目录
RUN mkdir -p uploads compressed_outputs && \
    chmod 777 uploads compressed_outputs

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口（Flask默认5000）
EXPOSE 8000

# 启动命令
CMD ["python", "app.py"]