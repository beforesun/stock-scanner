#!/bin/bash
# A股量化交易筛选系统 - 备份脚本

set -e

# 配置
BACKUP_DIR="$HOME/stock-scanner-deploy/backup"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 创建备份目录
mkdir -p $BACKUP_DIR/{postgres,redis,full}

# 备份PostgreSQL
info "备份PostgreSQL数据库..."
docker-compose exec -T postgres pg_dump -U stock_user stock_db > $BACKUP_DIR/postgres/backup_$DATE.sql

# 备份Redis
docker-compose exec -T redis redis-cli BGSAVE
sleep 5  # 等待保存完成
cp $HOME/stock-scanner-deploy/data/redis/dump.rdb $BACKUP_DIR/redis/backup_$DATE.rdb

# 备份配置文件和代码
info "备份配置文件..."
tar -czf $BACKUP_DIR/full/backup_$DATE.tar.gz \
    -C $HOME/stock-scanner-deploy \
    --exclude=data \
    --exclude=logs \
    --exclude=backup \
    .

# 备份Docker卷
docker run --rm \
    -v stock-scanner_postgres_data:/data/postgres \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/volumes/postgres_backup_$DATE.tar.gz -C /data/postgres .

docker run --rm \
    -v stock-scanner_redis_data:/data/redis \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/volumes/redis_backup_$DATE.tar.gz -C /data/redis .

# 清理旧备份
info "清理旧备份..."
find $BACKUP_DIR -name "backup_*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup_*.rdb" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR/volumes -name "*_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# 记录备份信息
echo "Backup completed at $(date)" >> $BACKUP_DIR/backup.log
echo "Backup files:"
ls -lh $BACKUP_DIR/*/*$DATE* >> $BACKUP_DIR/backup.log

info "✅ 备份完成！"
info "备份文件保存在: $BACKUP_DIR"
info "备份日期: $DATE"