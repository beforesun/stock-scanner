FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 尝试安装TA-Lib，如果失败则跳过
RUN (wget -O ta-lib-0.4.0-src.tar.gz https://github.com/mrjbq7/ta-lib/releases/download/ta-lib-0.4.0/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz) || \
    echo "TA-Lib installation failed, continuing without it..."

# 安装Python依赖
COPY requirements.txt requirements.simple.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple || \
    (echo "Failed to install all requirements, trying without TA-Lib..." && \
     pip install --no-cache-dir -r requirements.simple.txt -i https://pypi.tuna.tsinghua.edu.cn/simple)

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 默认命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]