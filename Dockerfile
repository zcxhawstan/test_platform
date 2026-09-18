# ===== 前端构建阶段 =====
FROM node:22-slim AS frontend-builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com && npm ci
COPY frontend/ ./
RUN npm run build

# ===== 后端运行阶段 =====
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# mysqlclient 编译依赖 + allure 运行依赖（jre-headless）
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev pkg-config gcc \
    openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt \
    && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple gunicorn

# Allure 命令行（解压即用）
ADD https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.32.0/allure-commandline-2.32.0.tgz /opt/allure.tgz
RUN tar -xzf /opt/allure.tgz -C /opt && rm /opt/allure.tgz \
    && ln -s /opt/allure-2.32.0/bin/allure /usr/local/bin/allure \
    && chmod +x /usr/local/bin/allure

# 项目代码
COPY . .

# 容器启动初始化脚本（等库→migrate→管理员→exec主进程）
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 前端构建产物（dist 存在时 Django 自动托管 SPA）
COPY --from=frontend-builder /build/dist ./frontend/dist

# 媒体目录（报告等运行时产物）
RUN mkdir -p /app/media /app/staticfiles

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
# 启动命令（entrypoint 内 migrate 后 exec）
CMD ["gunicorn", "Django.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
