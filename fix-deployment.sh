#!/bin/bash

# 修复部署问题的快速脚本

echo "=== 修复A股量化交易系统部署问题 ==="
echo ""

# 1. 确保使用正确的Dockerfile
echo "1. 更新docker-compose.yml使用简化版Dockerfile..."
sed -i 's/dockerfile: Dockerfile/dockerfile: Dockerfile.simple/g' docker-compose.yml

# 2. 清理pandas-ta依赖
echo "2. 清理requirements文件..."
cd backend
# 确保requirements.simple.txt没有pandas-ta
grep -v "pandas-ta" requirements.simple.txt > requirements.simple.tmp || true
mv requirements.simple.tmp requirements.simple.txt

# 3. 清理Docker构建缓存
echo "3. 清理Docker构建缓存..."
docker system prune -f || true

# 4. 重新构建
echo "4. 重新构建Docker镜像..."
cd ..
docker-compose down
docker-compose build --no-cache backend scheduler

# 5. 启动服务
echo "5. 启动服务..."
docker-compose up -d

echo ""
echo "修复完成！如果还有问题，请查看日志："
echo "docker-compose logs"
echo ""
echo "常用命令："
echo "- 查看状态: docker-compose ps"
echo "- 查看日志: docker-compose logs -f backend"
echo "- 重启服务: docker-compose restart"
echo "- 停止服务: docker-compose down"