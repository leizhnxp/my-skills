# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库概述

这是一个 **自定义技能仓库**。每个顶级目录是一个独立的技能（Skill），可运行在任何支持 SKILL 规范的 agent 环境中。

## 技能目录结构

每个技能遵循以下约定：

```
<skill-name>/
  SKILL.md          # 技能定义文件，包含 YAML frontmatter（name、description）和完整使用说明
  evals/evals.json  # 技能测试用例（prompt + expected_output）
  scripts/          # 辅助脚本（bash/python），由技能调用
```

`SKILL.md` 的 frontmatter 字段（`name`、`description`）控制技能的触发时机和匹配方式。

## 运行评测

使用 `skill-creator` 技能运行评测。每个技能的 `evals/evals.json` 包含测试提示词和预期输出。

## 语言规范

所有技能文档、用户交互输出和注释均使用**简体中文**。创建或修改技能时请保持此规范。
