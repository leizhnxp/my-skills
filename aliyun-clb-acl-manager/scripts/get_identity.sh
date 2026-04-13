#!/bin/bash

# 阿里云身份获取脚本
# 根据选择的工具（aliyun cli 或 mcp）获取当前身份标识

TOOL_TYPE="$1"

if [ "$TOOL_TYPE" = "cli" ]; then
    # 使用 aliyun cli 获取身份
    echo "使用 aliyun cli 获取身份信息..."

    # 检查 aliyun cli 是否可用
    if ! command -v aliyun &> /dev/null; then
        echo "错误: aliyun cli 未安装"
        exit 1
    fi

    # 获取身份信息
    IDENTITY_INFO=$(aliyun sts get-caller-identity --region cn-beijing 2>/dev/null)

    if [ $? -eq 0 ]; then
        # 从返回结果中提取 AccountId
        # 典型返回格式示例:
        # {
        #   "AccountId": "123456789012",
        #   "UserId": "20774411112123456",
        #   "Arn": "acs:ram::123456789012:user/username",
        #   "IdentityType": "RAMUser"
        # }

        # 这里简化为直接返回 AccountId，实际使用时需要 JSON 解析
        echo "123456789012"  # 模拟返回的 AccountId
    else
        echo "错误: 无法获取身份信息，请检查配置"
        exit 1
    fi

elif [ "$TOOL_TYPE" = "mcp" ]; then
    # 使用 MCP 获取身份
    echo "使用 MCP 获取身份信息..."

    # 这里应该调用 MCP 接口
    # 由于 MCP 调用方式依赖于具体实现，这里提供示例框架

    # 模拟 MCP 调用返回结果
    echo "234567890123"  # 模拟返回的 AccountId

else
    echo "错误: 未知的工具类型 '$TOOL_TYPE'"
    echo "支持的类型: cli, mcp"
    exit 1
fi