---
name: apifox-tests
description: Use when running or interpreting Apifox automated API tests for dev, test, or prod validation before commit, merge, release, or targeted regression checks.
---

# Apifox Tests

执行 Apifox 自动化测试并解释结果。

## 前置准备

首次使用前，先确认下面几项已经完成：

1. 电脑已安装 Node 环境：

```bash
node -v
npm -v
```

2. 已全局安装 Apifox CLI：

```bash
npm install -g apifox-cli
apifox --version
```

3. 已在终端直接验证过一条 Apifox CLI 命令。
   - 到 Apifox 的“自动化测试 -> CI/CD”中复制一个“测试场景”或“测试套件”的 CLI 命令
   - 补上 Access Token 后直接执行
   - 看到测试输出，说明 `apifox-cli` 可用

4. 已安装 skill 本地脚本依赖：

```bash
cd skills/apifox-tests
npm install
```

## 适用场景

- 开发自测后验证接口是否可用
- 合并前做接口回归
- 发布前做指定测试集复核
- 按环境执行单个或多个 Apifox 测试

## 工作流程

1. 先确定测试文件。
   - 如果用户已经明确给出测试文件路径、文件名或可唯一匹配的名称，直接使用。
   - 如果信息不明确，先执行：

```bash
node scripts/list-tests.js
```

2. 再确认环境。
   - 支持 `dev`、`test`、`prod`
   - 如果用户没有明确指定环境，先让用户选择

3. 明确是否批量执行。
   - 默认只执行一个测试
   - 如果用户要求“跑这几个”或“全部跑一遍”，进入批量模式
   - 批量模式下，需要说明是顺序执行还是并行执行

4. 执行测试。

```bash
node scripts/run-cli.js <测试文件路径> <环境名>
```

5. 解读结果。
   - 说明通过 / 失败
   - 如果失败，基于测试名称、接口语义和 CLI 输出解释原因

## 失败处理

- 不修改测试文件
- 不修改执行命令
- 仅解释问题，不擅自变更测试设计

## 环境文件

首次使用前需要填写：

- `env/dev.env`
- `env/test.env`
- `env/prod.env`

格式：

```env
APIFOX_ACCESS_TOKEN=APS-你的访问令牌
APIFOX_ENV_ID=你的环境ID
```
