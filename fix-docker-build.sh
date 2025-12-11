#!/bin/bash

echo "=== 修复Docker构建问题 ==="
echo ""

# 清理Docker构建缓存
echo "1. 清理Docker构建缓存..."
docker system prune -af --volumes || true

# 重新构建
echo "2. 重新构建Docker镜像..."
cd backend

# 直接构建后端镜像
echo "构建后端镜像..."
docker build -f Dockerfile.simple -t stock-scanner-backend:latest .

# 直接构建调度器镜像（使用相同的Dockerfile）
echo "构建调度器镜像..."
docker build -f Dockerfile.simple -t stock-scanner-scheduler:latest .

echo ""
echo "构建完成！"
echo ""
echo "现在可以运行："
echo "  docker-compose up -d"
echo ""
echo "或者使用docker-compose build："
echo "  docker-compose build backend scheduler"
echo "  docker-compose up -d"