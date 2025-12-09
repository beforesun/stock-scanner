#!/bin/bash
# SSL证书配置脚本

set -e

echo "==========================================="
echo "SSL证书配置"
echo "==========================================="

# 创建SSL目录
mkdir -p deploy/nginx/ssl

# 方法1：使用Let's Encrypt（推荐）
install_letsencrypt() {
    echo "安装Certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx

    echo "获取SSL证书..."
    read -p "请输入您的域名: " DOMAIN

    sudo certbot certonly --nginx -d $DOMAIN --email admin@$DOMAIN --agree-tos --non-interactive

    # 创建符号链接
    sudo ln -sf /etc/letsencrypt/live/$DOMAIN/fullchain.pem deploy/nginx/ssl/cert.pem
    sudo ln -sf /etc/letsencrypt/live/$DOMAIN/privkey.pem deploy/nginx/ssl/key.pem

    echo "设置自动续期..."
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
}

# 方法2：自签名证书（测试用）
install_selfsigned() {
    echo "生成自签名证书..."

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout deploy/nginx/ssl/key.pem \
        -out deploy/nginx/ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=StockScanner/CN=localhost"

    echo "自签名证书已生成！"
}

# 选择证书类型
echo "请选择SSL证书类型："
echo "1) Let's Encrypt (需要真实域名)"
echo "2) 自签名证书 (测试用)"
read -p "请选择 (1/2): " choice

case $choice in
    1)
        install_letsencrypt
        ;;
    2)
        install_selfsigned
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo "SSL证书配置完成！"