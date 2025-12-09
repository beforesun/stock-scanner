#!/bin/bash
# A股量化交易筛选系统 - 部署脚本

set -e

echo "==========================================="
echo "A股量化交易筛选系统 - 生产环境部署"
echo "==========================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   error "请不要以root用户运行此脚本"
fi

# 检查依赖
info "检查系统依赖..."
command -v docker > /dev/null 2>&1 || error "Docker未安装"
command -v docker-compose > /dev/null 2>&1 || error "Docker Compose未安装"

# 获取用户输入
read -p "请输入您的域名 (如: stock.example.com): " DOMAIN
read -p "请输入您的邮箱 (用于SSL证书): " EMAIL
read -sp "请输入PostgreSQL密码: " POSTGRES_PASSWORD
echo
read -sp "请输入Grafana管理员密码: " GRAFANA_PASSWORD
echo
read -sp "请输入应用密钥 (至少32位): " SECRET_KEY
echo

# 生成随机密码（如果没有输入）
if [[ -z "$POSTGRES_PASSWORD" ]]; then
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    info "生成的PostgreSQL密码: $POSTGRES_PASSWORD"
fi

if [[ -z "$GRAFANA_PASSWORD" ]]; then
    GRAFANA_PASSWORD=$(openssl rand -base64 16)
    info "生成的Grafana密码: $GRAFANA_PASSWORD"
fi

if [[ -z "$SECRET_KEY" ]]; then
    SECRET_KEY=$(openssl rand -base64 32)
    info "生成的应用密钥: $SECRET_KEY"
fi

# 创建部署目录
info "创建部署目录..."
mkdir -p ~/stock-scanner-deploy
mkdir -p ~/stock-scanner-deploy/{data,logs,backup,nginx/ssl,monitoring}

# 复制项目文件
info "复制项目文件..."
cp -r ../backend ~/stock-scanner-deploy/
cp -r ../frontend ~/stock-scanner-deploy/
cp -r ../sql ~/stock-scanner-deploy/
cp -r ./* ~/stock-scanner-deploy/

# 进入部署目录
cd ~/stock-scanner-deploy

# 创建环境变量文件
info "创建环境变量文件..."
cat > .env << EOF
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
GRAFANA_PASSWORD=$GRAFANA_PASSWORD
SECRET_KEY=$SECRET_KEY
EOF

# 创建生产环境配置文件
info "创建生产环境配置文件..."
cp docker-compose.prod.yml docker-compose.yml

# 设置SSL证书
info "设置SSL证书..."
if [[ -n "$DOMAIN" ]]; then
    # 使用Let's Encrypt
    mkdir -p nginx/ssl
    docker run --rm -v $PWD/nginx/ssl:/etc/letsencrypt -p 80:80 certbot/certbot certonly \
        --standalone -d $DOMAIN --email $EMAIL --agree-tos --non-interactive || warn "SSL证书获取失败，将使用自签名证书"
fi

# 如果没有SSL证书，生成自签名证书
if [[ ! -f nginx/ssl/cert.pem ]]; then
    warn "生成自签名证书用于测试..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=StockScanner/CN=$DOMAIN"
fi

# 创建Prometheus配置
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'stock-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: '/metrics'
    scrape_interval: 15s
EOF

# 设置权限
info "设置文件权限..."
chmod +x *.sh
find . -type f -name "*.py" -exec chmod 644 {} \;
find . -type f -name "*.yml" -exec chmod 644 {} \;
find . -type f -name "*.conf" -exec chmod 644 {} \;

# 停止旧容器（如果存在）
info "停止旧容器..."
docker-compose down || true

# 构建镜像
info "构建Docker镜像..."
docker-compose build

# 启动服务
info "启动服务..."
docker-compose up -d

# 等待服务启动
info "等待服务启动..."
sleep 30

# 检查服务状态
info "检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    info "✅ 服务已成功启动！"
else
    error "❌ 服务启动失败"
fi

# 显示访问信息
echo ""
echo "==========================================="
echo "🎉 部署完成！"
echo "==========================================="
echo ""
echo "📱 访问地址："
echo "   前端界面: https://$DOMAIN (或 https://$(curl -s ifconfig.me))"
echo "   API文档: https://$DOMAIN/docs (或 https://$(curl -s ifconfig.me)/docs)"
echo "   监控面板: http://$(curl -s ifconfig.me):3001 (Grafana)"
echo "   Prometheus: http://$(curl -s ifconfig.me):9090"
echo ""
echo "📊 管理命令："
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo "   更新代码: git pull && docker-compose up -d --build"
echo ""
echo "🔐 安全信息："
echo "   PostgreSQL密码: $POSTGRES_PASSWORD"
echo "   Grafana密码: $GRAFANA_PASSWORD"
echo "   应用密钥: $SECRET_KEY"
echo ""
echo "📁 文件位置："
echo "   项目目录: $HOME/stock-scanner-deploy"
echo "   日志目录: $HOME/stock-scanner-deploy/logs"
echo "   数据目录: $HOME/stock-scanner-deploy/data"
echo "   备份目录: $HOME/stock-scanner-deploy/backup"
echo ""
echo "🔄 定时任务："
echo "   周末扫描: 每周日 20:00"
echo "   日筛选: 工作日 15:05"
echo "   MACD更新: 工作日 10:30, 13:00, 15:05"
echo "   数据清理: 每周六 02:00"
echo ""
echo "📚 查看日志："
echo "   docker-compose logs -f"
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f scheduler"
echo ""

# 保存配置信息
cat > deployment-info.txt << EOF
部署时间: $(date)
域名: $DOMAIN
邮箱: $EMAIL
PostgreSQL密码: $POSTGRES_PASSWORD
Grafana密码: $GRAFANA_PASSWORD
应用密钥: $SECRET_KEY
服务器IP: $(curl -s ifconfig.me)
EOF

info "部署信息已保存到 deployment-info.txt"

# 设置定时备份
echo "0 2 * * * $HOME/stock-scanner-deploy/backup.sh" | crontab -

info "定时备份已设置（每天凌晨2点）"

info "🎉 恭喜！您的A股量化交易筛选系统已成功部署到互联网！"