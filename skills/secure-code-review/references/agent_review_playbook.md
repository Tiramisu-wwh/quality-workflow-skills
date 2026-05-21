# Agent Review Playbook

## 目标

用统一方法做源码安全审查，避免只靠关键词命中就下结论。

## 基本原则

1. 先确定入口、数据流和安全边界。
2. 先用预扫描脚本收集候选问题，再做人工语义审查。
3. 只在源码能直接证明时写 `pass`。
4. 遇到运行态、部署态、网关态问题时，写 `needs_manual_review`。

## 推荐步骤

1. 识别主语言和框架。
2. 找到 controller / route / handler / service / repository / middleware。
3. 跑预扫描：

```bash
python3 scripts/secure_review_scan.py /path/to/project --format markdown --output secure-review-scan.md
```

4. 用 `rg` 和代码阅读缩小高风险范围。
5. 围绕以下主题写结论：
   - secrets
   - auth and access control
   - validation and output
   - file handling
   - logging and exceptions
   - crypto and randomness
   - external calls

## 结论口径

- `pass`：控制存在且能从当前链路直接证明
- `fail`：存在反例或关键控制缺失
- `needs_manual_review`：依赖运行环境、部署配置或外部系统
- `not_applicable`：当前系统没有这类能力
