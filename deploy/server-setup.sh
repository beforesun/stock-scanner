#!/bin/bash
# A股量化交易筛选系统 - 服务器配置脚本

set -e

echo "==========================================="
echo "A股量化交易筛选系统 - 服务器配置"
echo "==========================================="

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git vim unzip build-essential

# 安装Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 安装Nginx
sudo apt install -y nginx

# 创建项目目录
mkdir -p ~/stock-scanner
mkdir -p ~/stock-scanner/data/postgres
mkdir -p ~/stock-scanner/data/redis
mkdir -p ~/stock-scanner/logs
mkdir -p ~/stock-scanner/backup

# 设置目录权限
sudo chown -R $USER:$USER ~/stock-scanner
sudo chmod -R 755 ~/stock-scanner

echo "基础配置完成！"
echo "请重新登录以使Docker组权限生效"