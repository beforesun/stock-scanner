# 🚀 A股量化交易筛选系统 - 互联网部署指南

## 📋 部署概述

本指南将帮助您将A股量化交易筛选系统部署到互联网服务器上，支持HTTPS、监控、自动备份等生产级功能。

## 🖥️ 服务器要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB
- **存储**: 50GB SSD
- **带宽**: 10Mbps
- **系统**: Ubuntu 20.04+ / CentOS 8+

### 推荐配置
- **CPU**: 4核心
- **内存**: 8GB
- **存储**: 100GB SSD
- **带宽**: 50Mbps
- **系统**: Ubuntu 22.04 LTS

## 🛠️ 环境准备

### 1. 购买服务器
推荐云服务商：
- 国内：阿里云、腾讯云、华为云
- 国外：AWS、Google Cloud、DigitalOcean

### 2. 域名准备（可选但推荐）
- 购买域名（如：stockscanner.yourdomain.com）
- 将域名解析到服务器IP

### 3. 开放端口
确保服务器防火墙开放以下端口：
- 80 (HTTP)
- 443 (HTTPS)
- 8000 (API，可选)
- 3001 (Grafana监控)
- 9090 (Prometheus监控)

## 🚀 快速部署

### 一键部署脚本

```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/stock-scanner/main/deploy/deploy.sh
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 手动部署步骤

#### 第一步：连接到服务器

```bash
# 使用SSH连接
ssh username@your-server-ip

# 或使用密钥连接
ssh -i your-key.pem username@your-server-ip
```

#### 第二步：运行服务器配置脚本

```bash
# 下载并运行服务器配置脚本
wget https://raw.githubusercontent.com/your-repo/stock-scanner/main/deploy/server-setup.sh
chmod +x server-setup.sh
./server-setup.sh

# 重新登录以使Docker权限生效
exit
ssh username@your-server-ip
```

#### 第三步：克隆项目代码

```bash
# 克隆项目
git clone https://github.com/your-repo/stock-scanner.git
cd stock-scanner/deploy
```

#### 第四步：配置环境变量

```bash
# 创建环境变量文件
cp .env.prod .env

# 编辑环境变量
nano .env
```

#### 第五步：运行部署脚本

```bash
chmod +x deploy.sh
./deploy.sh
```

#### 第六步：配置SSL证书

```bash
chmod +x ssl-setup.sh
./ssl-setup.sh
```

## 🔧 详细配置

### 1. 环境变量配置

编辑 `.env` 文件：

```bash
# 数据库配置
POSTGRES_PASSWORD=your-strong-password

# 应用配置
SECRET_KEY=your-very-long-secret-key-at-least-32-characters

# 监控配置
GRAFANA_PASSWORD=your-grafana-password
```

### 2. Nginx配置

编辑 `nginx/nginx.conf`：

```nginx
server_name your-domain.com;
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

### 3. Docker Compose配置

编辑 `docker-compose.yml`：

```yaml
environment:
  - DATABASE_URL=postgresql://stock_user:${POSTGRES_PASSWORD}@postgres:5432/stock_db
  - REDIS_URL=redis://redis:6379/0
```

## 🌐 域名和SSL配置

### 1. 使用Let's Encrypt（推荐）

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --standalone -d your-domain.com --email your-email@example.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. 使用Cloudflare（CDN + 免费SSL）

1. 注册Cloudflare账号
2. 添加您的域名
3. 修改域名DNS服务器为Cloudflare提供的服务器
4. 在Cloudflare控制台启用SSL/TLS

### 3. 自签名证书（测试用）

```bash
# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=StockScanner/CN=your-domain.com"
```

## 📊 监控和日志

### 1. 查看服务状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f scheduler
```

### 2. 访问监控面板

- **Grafana**: http://your-server-ip:3001
  - 用户名: admin
  - 密码: 您在.env文件中设置的密码

- **Prometheus**: http://your-server-ip:9090

### 3. 设置告警

在Grafana中：
1. 添加通知渠道（邮件、钉钉、微信等）
2. 创建告警规则
3. 配置告警条件

## 💾 备份和恢复

### 自动备份

备份脚本已设置为每天凌晨2点自动运行：

```bash
# 手动运行备份
./backup.sh

# 查看备份文件
ls -la ~/stock-scanner-deploy/backup/
```

### 手动备份

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U stock_user stock_db > backup.sql

# 备份整个系统
tar -czf stock-scanner-backup.tar.gz ~/stock-scanner-deploy/
```

### 恢复数据

```bash
# 恢复数据库
docker-compose exec -T postgres psql -U stock_user stock_db < backup.sql

# 恢复Redis数据
cp backup.rdb data/redis/dump.rdb
docker-compose restart redis
```

## 🔒 安全加固

### 1. 防火墙配置

```bash
# 安装ufw（Ubuntu）
sudo apt install -y ufw

# 配置防火墙
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. 系统安全

```bash
# 创建非root用户
sudo adduser stockuser
sudo usermod -aG docker stockuser

# 禁用root登录
sudo nano /etc/ssh/sshd_config
# 修改：PermitRootLogin no
# 修改：PasswordAuthentication no

sudo systemctl restart sshd
```

### 3. 应用安全

- 定期更新依赖包
- 使用强密码
- 启用HTTPS
- 限制API访问频率
- 定期审计日志

## 📈 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_weekend_scan_date ON weekend_scan_results(scan_date);
CREATE INDEX CONCURRENTLY idx_daily_pool_date ON daily_pool(scan_date);
CREATE INDEX CONCURRENTLY idx_signals_date ON trade_signals(signal_date);
```

### 2. Redis优化

```bash
# 在redis.conf中添加
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 3. 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 1024" >> /etc/sysctl.conf
sysctl -p
```

## 🔄 更新和维护

### 1. 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose down
docker-compose build
docker-compose up -d
```

### 2. 数据库迁移

```bash
# 如果有数据库结构变更
docker-compose exec backend alembic upgrade head
```

### 3. 日志轮转

```bash
# 设置logrotate
sudo nano /etc/logrotate.d/stock-scanner

# 添加：
/home/stock-scanner/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 user user
}
```

## 🚨 故障排除

### 常见问题

1. **容器无法启动**
   ```bash
   docker-compose logs <服务名>
   docker-compose ps
   ```

2. **数据库连接失败**
   - 检查PostgreSQL是否运行
   - 验证连接字符串
   - 检查防火墙设置

3. **SSL证书问题**
   - 检查证书有效期
   - 验证证书路径
   - 查看Nginx错误日志

4. **性能问题**
   - 检查系统资源使用情况
   - 查看数据库慢查询
   - 优化查询语句

### 获取帮助

- 查看日志：`docker-compose logs -f`
- 检查系统状态：`docker-compose ps`
- 监控系统资源：`htop` 或 `top`

## 📚 附加资源

### 监控指标

- 系统CPU、内存使用率
- 数据库连接数
- API响应时间
- 扫描任务执行时间
- 错误率统计

### 备份策略

- 数据库：每日全量备份，保留30天
- 配置文件：实时备份到Git
- 日志文件：压缩保存，保留90天

### 安全清单

- [ ] 使用强密码
- [ ] 启用HTTPS
- [ ] 配置防火墙
- [ ] 定期更新系统
- [ ] 启用日志监控
- [ ] 设置备份策略
- [ ] 限制SSH访问
- [ ] 使用非root用户运行服务

---

## 🎉 恭喜！

您已经成功将A股量化交易筛选系统部署到互联网！

系统现在可以：
- ✅ 自动扫描A股市场
- ✅ 识别交易信号
- ✅ 提供Web界面管理
- ✅ 支持HTTPS安全访问
- ✅ 提供监控和告警
- ✅ 自动备份数据

访问您的系统：
- 前端界面：https://your-domain.com
- API文档：https://your-domain.com/docs
- 监控面板：http://your-server-ip:3001

祝您使用愉快！🎊

---

*如遇问题，请查看日志或提交Issue寻求帮助*