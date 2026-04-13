#!/bin/bash

# 检查工具可用性
# 参数: $1 - 工具类型 (cli 或 mcp)

TOOL_TYPE="$1"

case "$TOOL_TYPE" in
    "cli"|"aliyun-cli")
        echo "检查 aliyun cli 可用性..."

        if ! command -v aliyun &> /dev/null; then
            echo "❌ aliyun cli 未安装"
            echo ""
            echo "请按以下步骤安装 aliyun cli:"
            echo "1. 官方文档: https://help.aliyun.com/zh/cli"
            echo "2. 快速安装: curl -fsSL https://aliyuncli.alicdn.com/aliyun-cli-install.sh | bash -s"
            echo "3. 配置访问密钥: aliyun configure"
            echo ""
            echo "安装完成后请重新运行此技能。"
            exit 1
        fi

        # 检查配置状态
        CONFIG_STATUS=$(aliyun configure list 2>/dev/null | grep "default" | awk '{print $3}')

        if [ "$CONFIG_STATUS" = "Invalid" ] || [ -z "$CONFIG_STATUS" ]; then
            echo "❌ aliyun cli 未配置或配置无效"
            echo ""
            echo "请运行以下命令配置访问密钥:"
            echo "aliyun configure"
            echo ""
            echo "需要提供:"
            echo "- Access Key ID"
            echo "- Access Key Secret"
            echo "- Default Region Name (建议: cn-beijing)"
            echo "- Default Output Format (建议: json)"
            exit 1
        fi

        echo "✅ aliyun cli 可用 (配置状态: $CONFIG_STATUS)"
        ;;

    "mcp"|"aliyun-mcp")
        echo "检查 aliyun core mcp 可用性..."

        # 检查当前环境类型并提供相应的安装指导
        if [ ! -z "$CLAUDE_DESKTOP" ]; then
            # Claude Desktop 环境
            echo "检测到 Claude Desktop 环境"
            MCP_CONFIG_PATH="$HOME/.claude_desktop_config.json"

        elif [ ! -z "$CLAUDE_CODE" ] || [ -d ".claude" ]; then
            # Claude Code 环境
            echo "检测到 Claude Code 环境"
            MCP_CONFIG_PATH=".claude/settings.json"

        elif [ ! -z "$COWORK" ]; then
            # Cowork 环境
            echo "检测到 Cowork 环境"

        else
            # 其他环境
            echo "检测到其他环境"
        fi

        echo "❌ aliyun core mcp 需要配置"
        echo ""
        echo "MCP 服务地址: https://openapi-mcp.cn-hangzhou.aliyuncs.com/id/GUxHJknZAL5HiKLL/mcp"
        echo ""

        if [ ! -z "$CLAUDE_CODE" ] || [ -d ".claude" ]; then
            echo "在 Claude Code 中配置 MCP:"
            echo "1. 使用 update-config 技能:"
            echo "   \"/update-config 添加MCP服务器配置\""
            echo ""
            echo "2. 或手动编辑 .claude/settings.json 添加:"

        elif [ ! -z "$CLAUDE_DESKTOP" ]; then
            echo "在 Claude Desktop 中配置 MCP:"
            echo "1. 编辑配置文件: $MCP_CONFIG_PATH"
            echo "2. 添加以下配置:"

        else
            echo "MCP 配置方法:"
            echo "1. 根据您的环境添加以下配置:"
        fi

        cat << 'EOF'

{
  "mcpServers": {
    "aliyun-core": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "MCP_SERVER_URL": "https://openapi-mcp.cn-hangzhou.aliyuncs.com/id/GUxHJknZAL5HiKLL/mcp"
      }
    }
  }
}
EOF

        echo ""
        echo "配置完成后请重启 Claude 并重新运行此技能。"
        exit 1
        ;;

    *)
        echo "❌ 未知的工具类型: $TOOL_TYPE"
        echo "支持的类型: cli, mcp"
        exit 1
        ;;
esac