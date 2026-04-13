#!/bin/bash

# 获取当前出口IP地址
# 支持多种IP获取方式，增强鲁棒性

echo "获取当前出口IP地址..."

# 方式1: 使用 cip.cc (主要方式)
IP=$(curl -s --connect-timeout 5 cip.cc | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1)

if [ -z "$IP" ]; then
    echo "主要IP获取服务不可用，尝试备选方式..."

    # 方式2: 使用 ifconfig.me
    IP=$(curl -s --connect-timeout 5 ifconfig.me)

    if [ -z "$IP" ]; then
        # 方式3: 使用 ipinfo.io
        IP=$(curl -s --connect-timeout 5 ipinfo.io/ip)
    fi
fi

# 验证IP格式 (IPv4)
if echo "$IP" | grep -E '^([0-9]{1,3}\.){3}[0-9]{1,3}$' > /dev/null; then
    # 进一步验证IP地址范围 (0-255)
    IFS='.' read -ra ADDR <<< "$IP"
    VALID=true

    for i in "${ADDR[@]}"; do
        if [ "$i" -lt 0 ] || [ "$i" -gt 255 ]; then
            VALID=false
            break
        fi
    done

    if [ "$VALID" = true ]; then
        echo "$IP"
    else
        echo "错误: 获取到的IP地址格式无效: $IP"
        exit 1
    fi
else
    echo "错误: 无法获取有效的IP地址"
    echo "请检查网络连接或手动提供IP地址"
    exit 1
fi