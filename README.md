# Quality Gate Skills

公开发布的质量门禁相关 skills 仓库，可通过 `npx skills add` 直接安装。

## 包含的 Skills

- `prd-gatekeeper`
- `secure-code-review`
- `test-plan-xmind-generator`
- `testcase-generator`
- `apifox-tests`
- `defect-analysis`
- `test-report-generator`

## 适用流程

推荐按下面这条链路使用：

`产品 Agent 需求准入 -> 开发 receive 代码安全审计 -> QA 测试计划 -> QA 测试用例 -> 接口自动化 -> 缺陷分析 -> 测试报告`

其中：

- `prd-gatekeeper` 适合前置到产品 Agent 侧。
- `secure-code-review` 适合前置到开发 receive 侧。

## 安装

安装整个仓库：

```bash
npx skills add Tiramisu-wwh/quality-gate-skills
```

按仓库 URL 安装：

```bash
npx skills add https://github.com/Tiramisu-wwh/quality-gate-skills
```

按单个 skill 安装：

```bash
npx skills add Tiramisu-wwh/quality-gate-skills --skill prd-gatekeeper
npx skills add Tiramisu-wwh/quality-gate-skills --skill secure-code-review
npx skills add Tiramisu-wwh/quality-gate-skills --skill test-plan-xmind-generator
npx skills add Tiramisu-wwh/quality-gate-skills --skill testcase-generator
npx skills add Tiramisu-wwh/quality-gate-skills --skill apifox-tests
npx skills add Tiramisu-wwh/quality-gate-skills --skill defect-analysis
npx skills add Tiramisu-wwh/quality-gate-skills --skill test-report-generator
```

## 环境准备

- Python 3.11 或更高版本
- Node.js 18 或更高版本
- `git`、`rg`

常用依赖：

```bash
python3 -m pip install xlsxwriter openpyxl requests
```

Apifox 依赖：

```bash
cd skills/apifox-tests
npm install
```

## 首次配置

### Apifox

填写：

- `skills/apifox-tests/env/dev.env`
- `skills/apifox-tests/env/test.env`
- `skills/apifox-tests/env/prod.env`

格式：

```env
APIFOX_ACCESS_TOKEN=APS-你的访问令牌
APIFOX_ENV_ID=你的环境ID
```

### Teambition

填写：

- `skills/defect-analysis/assets/teambition-auth.env`
- `skills/test-report-generator/assets/teambition-auth.env`

并替换：

- `skills/defect-analysis/assets/teambition-id-mapping.json`
- `skills/test-report-generator/assets/teambition-id-mapping.json`

仓库里的鉴权和映射文件都是空模板，不包含真实凭据或项目数据。

## 快速开始

### 1. 需求准入

```text
用 prd-gatekeeper 评审这份 PRD，并输出准入报告。
```

### 2. 代码安全审计

```text
用 secure-code-review 审查这个仓库，并输出高风险问题和控制矩阵。
```

### 3. 测试计划

```text
根据这份 PRD 和接口说明，生成测试计划和 XMind。
```

### 4. 测试用例

```text
根据这份 PRD 生成测试用例，并额外导出一份冒烟集。
```

### 5. 接口自动化

```text
用 apifox-tests 在 test 环境执行 获取项目列表测试，并解释结果。
```

### 6. 缺陷分析

```text
用 defect-analysis 生成 示例项目 Sprint 12 的缺陷分析报告。
```

### 7. 测试报告

```text
用 test-report-generator 生成 示例项目 Sprint 12 的测试报告。
```

## 文档

- [Quickstart](docs/quickstart.md)
- [Apifox CLI + Claude Skills](docs/apifox-cli-claude-skills.md)
- [Release Notes](RELEASE.md)

## 说明

- 这个公开仓库只保留可公开分发的通用 skill、脚本和模板占位文件。
- `apifox-tests/tests/` 中保留的是示例测试文件，接入新团队后通常需要替换成自己的测试集。
- `defect-analysis` 和 `test-report-generator` 依赖 Teambition OpenAPI，首次使用前需要补齐鉴权和映射文件。
