# 🚀 A股量化交易筛选系统 - 部署包

## 📦 部署包内容

```
deploy/
├── deploy.sh              # 主部署脚本
├── server-setup.sh        # 服务器环境配置
├── ssl-setup.sh          # SSL证书配置
├── backup.sh             # 备份脚本
├── docker-compose.prod.yml # 生产环境Docker配置
├── nginx/                # Nginx配置
│   ├── nginx.conf        # 主配置文件
│   └── ssl/              # SSL证书目录
├── monitoring/           # 监控配置
│   └── prometheus.yml    # Prometheus配置
├── .env.prod            # 生产环境变量模板
├── DEPLOYMENT_GUIDE.md  # 详细部署指南
└── README.md            # 本文件
```

## 🚀 快速部署

### 方法1：一键部署

```bash
# 上传整个deploy目录到服务器
# 进入deploy目录
cd deploy

# 运行一键部署
./deploy.sh
```

### 方法2：分步部署

```bash
# 1. 服务器环境配置
./server-setup.sh

# 2. 复制项目文件到deploy目录
# 3. 配置环境变量
cp .env.prod .env
nano .env

# 4. 运行部署
./deploy.sh

# 5. 配置SSL（可选）
./ssl-setup.sh
```

## 🔧 部署前准备

### 服务器要求
- 操作系统：Ubuntu 20.04+ 或 CentOS 8+
- 内存：至少4GB（推荐8GB）
- 存储：至少50GB可用空间
- 网络：开放80、443、8000端口

### 域名和SSL（可选但推荐）
- 准备一个域名
- 确保域名已解析到服务器IP

## 📋 部署步骤

### 第一步：上传文件
将本deploy目录上传到服务器的用户主目录：
```bash
scp -r deploy username@your-server-ip:~/
```

### 第二步：运行部署
```bash
ssh username@your-server-ip
cd ~/deploy
chmod +x *.sh
./deploy.sh
```

### 第三步：按提示输入信息
- 域名（如：stock.yourdomain.com）
- 邮箱（用于SSL证书）
- 数据库密码
- Grafana管理员密码
- 应用密钥

### 第四步：等待部署完成
部署过程大约需要5-10分钟，请耐心等待。

## 🌐 访问系统

部署完成后，您将看到：

```
🎉 部署完成！
===========================================

📱 访问地址：
   前端界面: https://your-domain.com
   API文档: https://your-domain.com/docs
   监控面板: http://your-server-ip:3001
   Prometheus: http://your-server-ip:9090

📊 管理命令：
   查看日志: docker-compose logs -f
   停止服务: docker-compose down
   重启服务: docker-compose restart
   更新代码: git pull && docker-compose up -d --build
```

## 🔧 管理命令

### 基本操作
```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新系统
docker-compose pull && docker-compose up -d --build
```

### 备份和恢复
```bash
# 手动备份
./backup.sh

# 查看备份文件
ls -la ~/stock-scanner-deploy/backup/
```

### 监控访问
- **Grafana**: http://your-server-ip:3001
  - 用户名: admin
  - 密码: 部署时设置的密码

- **Prometheus**: http://your-server-ip:9090

## 🔒 安全建议

1. **修改默认密码**
   - PostgreSQL密码
   - Grafana管理员密码
   - 应用密钥

2. **配置防火墙**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **定期更新**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade

   # 更新Docker镜像
   docker-compose pull
   docker-compose up -d --build
   ```

## 🚨 故障排除

### 查看日志
```bash
# 查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f postgres
```

### 常见问题

1. **部署失败**
   - 检查网络连接
   - 查看错误日志
   - 确保端口未被占用

2. **SSL证书问题**
   - 确保域名正确解析
   - 检查证书有效期
   - 验证Nginx配置

3. **数据库连接失败**
   - 检查PostgreSQL状态
   - 验证密码是否正确
   - 查看数据库日志

## 📊 系统特点

✅ **完整的量化交易策略**
- 周末扫描：233周均线 + 成交量筛选
- 日筛选：均量线金叉 + MACD红柱放大
- 形态识别：缩量旗形 + 放量中阳

✅ **生产级部署**
- Docker容器化
- Nginx反向代理
- SSL/HTTPS支持
- 自动备份
- 监控告警

✅ **高可用性**
- 健康检查
- 自动重启
- 日志管理
- 数据备份

✅ **易于管理**
- Web界面管理
- API接口
- 监控面板
- 一键部署

## 🎯 系统功能

1. **周末扫描**
   - 自动扫描全市场股票
   - 筛选收盘价 > 233周均线
   - 要求周成交量 > 周MA20

2. **日筛选池**
   - 从周末结果中精选
   - 均量线20日金叉60日
   - 120分钟MACD红柱放大

3. **买入信号**
   - 识别缩量旗形形态
   - 涨停板后回调2-8天
   - 今日放量中阳突破
   - 提供止损建议

4. **Web界面**
   - 周末扫描结果查看
   - 日筛选池管理
   - 交易信号确认
   - K线图表展示

5. **API接口**
   - RESTful API设计
   - 支持手动触发扫描
   - 信号状态管理
   - 个股数据查询

## 📈 监控指标

- 系统CPU、内存使用率
- 数据库连接数
- API响应时间
- 扫描任务执行时间
- 错误率统计

## 🔄 定时任务

- **周末扫描**: 每周日 20:00
- **日筛选**: 工作日 15:05
- **MACD更新**: 工作日 10:30, 13:00, 15:05
- **数据清理**: 每周六 02:00
- **自动备份**: 每天凌晨2点

## 🚀 后续扩展

1. **消息推送**
   - 微信推送
   - 钉钉机器人
   - 邮件通知

2. **策略扩展**
   - 多因子选股
   - 机器学习优化
   - 策略回测

3. **移动端**
   - 响应式设计
   - PWA应用
   - 微信小程序

---

## 📞 获取帮助

- 查看日志：`docker-compose logs -f`
- 检查状态：`docker-compose ps`
- 查看部署信息：`cat deployment-info.txt`

祝您部署顺利！🎉

---

*如遇问题，请查看详细部署指南或提交Issue*