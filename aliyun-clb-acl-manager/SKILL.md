---
name: aliyun-clb-acl-manager
description: 管理阿里云北京区CLB ACL配置的专用技能。当用户明确提到要将当前IP添加到阿里云白名单时触发，自动添加用户出口IP到指定的CLB访问控制列表。支持aliyun cli和aliyun core mcp两种工具。
---

# 阿里云CLB ACL管理器

这个技能专门用于将当前用户的出口IP地址添加到阿里云北京区指定的CLB访问控制列表白名单中。

## 触发条件

用户明确提到要将"当前IP"添加到"阿里云白名单"时触发此技能。

## 目标ACL配置

- **ACL ID**: `acl-2zey0bn1wbyz2oiawcb9u`
- **ACL名称**: `临时远程`
- **区域**: `cn-beijing`
- **类型**: 白名单

## 工作流程

### 1. 工具选择和检查

在开始操作前，询问用户选择使用的工具：

"请选择要使用的阿里云工具："
1. `aliyun cli` - 阿里云命令行工具
2. `aliyun core mcp` - 阿里云MCP服务

### 2. 工具可用性检查和安装

#### 检查 aliyun cli
```bash
which aliyun || echo "aliyun cli 未安装"
```

**如果未安装，提供安装指导后退出：**
- **官方文档**: https://help.aliyun.com/zh/cli
- **快速安装**: `curl -fsSL https://aliyuncli.alicdn.com/aliyun-cli-install.sh | bash -s`
- **配置说明**: 安装后需要运行 `aliyun configure` 配置访问密钥

#### 检查和安装 aliyun core mcp

**MCP服务地址**: `https://openapi-mcp.cn-hangzhou.aliyuncs.com/id/GUxHJknZAL5HiKLL/mcp`

**根据当前agent环境提供合适的安装指导：**

1. **如果是Claude Desktop环境**:
   - 配置文件: `~/.claude_desktop_config.json` (Mac/Linux) 或 `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
   - 添加MCP服务器配置

2. **如果是Claude Code环境**:
   - 建议使用Skill工具中的 `update-config` 来添加MCP配置
   - 或手动编辑 `.claude/settings.json`

3. **如果是Cowork环境**:
   - 联系管理员配置MCP服务器
   - 或在用户配置文件中添加MCP配置

4. **如果是Claude.ai网页版**:
   - 无法直接添加MCP服务，建议使用aliyun cli方案

5. **如果是其他环境**:
   - 根据具体环境的MCP配置方式提供指导

**MCP配置示例**:
```json
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
```

### 3. 获取当前身份标识

根据用户选择的工具获取当前身份：

**使用aliyun cli:**
```bash
aliyun sts get-caller-identity --region cn-beijing --output json
```

**使用aliyun core mcp:**
- 调用STS GetCallerIdentity接口
- 获取AccountId和其他身份信息

从返回结果中提取合适的身份标识符。

### 4. 获取当前出口IP

```bash
curl -s cip.cc | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1
```

验证获取的IP是否为有效的IPv4格式。

### 5. 生成备注信息

按照格式 `日期（身份）` 生成备注：
```
格式: YYYY-MM-DD（身份标识）
示例: 2024-03-26（123456789012）
```

### 6. ACL操作流程

#### 6.1 显示现有ACL条目

**使用aliyun cli:**
```bash
aliyun slb describe-access-control-list-attribute \
  --region cn-beijing \
  --access-control-list-id acl-2zey0bn1wbyz2oiawcb9u \
  --output json
```

**使用mcp:**
调用SLB的DescribeAccessControlListAttribute接口，参数为固定的ACL ID。

#### 6.2 检查重复IP

在添加前检查当前IP是否已存在于ACL中，如果存在则询问用户是否更新备注。

#### 6.3 添加新的IP条目

**使用aliyun cli:**
```bash
aliyun slb add-access-control-list-entry \
  --region cn-beijing \
  --access-control-list-id acl-2zey0bn1wbyz2oiawcb9u \
  --acl-entry-ip <CURRENT_IP>/32 \
  --acl-entry-comment "<DATE>（<IDENTITY>）"
```

**使用mcp:**
调用SLB的AddAccessControlListEntry接口。

#### 6.4 确认添加结果

再次查询ACL配置，显示更新后的条目列表，并高亮显示新添加的条目。

## 输出格式

### 操作前状态显示
```
当前ACL条目 (临时远程 - acl-2zey0bn1wbyz2oiawcb9u):
┌─────────────────┬────────────────────────────┬─────────────────────┐
│ IP地址          │ 备注                       │ 添加时间            │
├─────────────────┼────────────────────────────┼─────────────────────┤
│ 192.168.1.100/32│ 2024-03-25（987654321098） │ 2024-03-25 10:30:21 │
│ 10.0.0.50/32    │ 2024-03-20（123456789012） │ 2024-03-20 14:15:10 │
└─────────────────┴────────────────────────────┴─────────────────────┘
```

### 操作执行信息
```
正在添加IP条目到阿里云白名单...
- 当前出口IP: 203.0.113.1
- 身份标识: 123456789012
- 备注信息: 2024-03-26（123456789012）
- 目标ACL: 临时远程 (acl-2zey0bn1wbyz2oiawcb9u)
- 区域: cn-beijing
```

### 操作后状态显示
```
✅ 成功添加到阿里云白名单！更新后的ACL条目:
┌─────────────────┬────────────────────────────┬─────────────────────┐
│ IP地址          │ 备注                       │ 添加时间            │
├─────────────────┼────────────────────────────┼─────────────────────┤
│ 192.168.1.100/32│ 2024-03-25（987654321098） │ 2024-03-25 10:30:21 │
│ 10.0.0.50/32    │ 2024-03-20（123456789012） │ 2024-03-20 14:15:10 │
│🌟203.0.113.1/32 │🌟2024-03-26（123456789012）│🌟2024-03-26 16:45:33│  ← 新增
└─────────────────┴────────────────────────────┴─────────────────────┘
```

## 错误处理

### 工具不可用处理
如果选择的工具未安装或不可用：
1. 提供详细的安装指导文档
2. 明确告知用户需要先安装工具才能继续
3. **立即退出技能执行**

### 其他错误情况
1. **身份获取失败**: 检查认证配置，提示重新配置
2. **IP获取失败**: 提供备选方案 `curl ifconfig.me`
3. **ACL操作失败**: 检查权限和网络连接
4. **重复IP**: 询问是否更新现有条目的备注信息

## 安全注意事项

- 固定操作特定的ACL (acl-2zey0bn1wbyz2oiawcb9u)
- 仅在北京区域(cn-beijing)操作
- 验证IP地址格式(IPv4)
- 显示操作预览，确认后执行
- 记录所有操作用于审计

## 使用示例

**触发示例**:
- "帮我把当前IP加到阿里云白名单"
- "需要将我的IP添加到阿里云白名单中"
- "请把我现在的IP地址加入阿里云白名单"

**完整执行流程**:
1. 用户: "帮我把当前IP加到阿里云白名单"
2. 询问选择工具 (aliyun cli / mcp)
3. 检查工具可用性
4. 获取身份标识: 123456789012
5. 获取当前IP: 203.0.113.1
6. 显示"临时远程"ACL现有条目
7. 添加新条目，备注: "2024-03-26（123456789012）"
8. 显示更新后条目并高亮新增项

## 故障排查

### aliyun cli常见问题
```bash
# 检查配置
aliyun configure list
# 测试连接
aliyun sts get-caller-identity --region cn-beijing
# 测试SLB权限
aliyun slb describe-regions
```

### MCP连接问题
- 验证MCP服务器URL可达性
- 检查网络连接和代理设置
- 验证Claude环境的MCP配置是否正确

### 权限问题
- 确认账号具有SLB相关权限
- 检查是否有特定ACL的修改权限
- 验证区域访问权限(cn-beijing)