# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制本地的依赖文件和应用程序文件到容器中
COPY requirements.txt ./
COPY main.py ./

# 安装依赖项，并指定 pip 源
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ --upgrade pip && \
    /app/.venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

RUN apt-get update && apt-get install -y libgtk-3-0

# 安装 NGINX
RUN apt-get update && apt-get install -y nginx && \
    rm /etc/nginx/sites-enabled/default

# 复制 NGINX 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV FLET_SERVER_PORT=8000

# 开放端口
EXPOSE 80

# 启动 Flet 和 NGINX
CMD service nginx start && python main.py
