# Quickstart

## 1. 安装

```bash
npx skills add Tiramisu-wwh/quality-workflow-skills
```

## 2. 依赖

```bash
python3 -m pip install xlsxwriter openpyxl requests
```

### Apifox CLI 前置准备

先确认电脑已安装 Node 环境：

```bash
node -v
npm -v
```

全局安装 Apifox CLI：

```bash
npm install -g apifox-cli
apifox --version
```

看到版本号，说明安装成功。

再到 Apifox 的「自动化测试 -> CI/CD」中，复制一个“测试场景”或“测试套件”的 CLI 命令到终端执行，并补上 Access Token。

看到测试输出，说明 Apifox CLI 可以正常工作。

### Apifox skill 本地脚本依赖

```bash
cd skills/apifox-tests
npm install
```

## 3. 配置

### Apifox

先完成上面的 Apifox CLI 前置准备，再填写：

- `skills/apifox-tests/env/dev.env`
- `skills/apifox-tests/env/test.env`
- `skills/apifox-tests/env/prod.env`

### Teambition

填写：

- `skills/defect-analysis/assets/teambition-auth.env`
- `skills/test-report-generator/assets/teambition-auth.env`

替换：

- `skills/defect-analysis/assets/teambition-id-mapping.json`
- `skills/test-report-generator/assets/teambition-id-mapping.json`

## 4. 接入位置

- `prd-gatekeeper`：前置到产品 Agent 侧
- `secure-code-review`：前置到开发 receive 侧
- 其他 skill：按 QA 规划、设计、执行、复盘阶段使用

## 5. 每个 Skill 的最短用法

### prd-gatekeeper

```text
用 prd-gatekeeper 评审这份 PRD，并输出准入报告。
```

### secure-code-review

```text
用 secure-code-review 审查这个仓库，并输出高风险问题和控制矩阵。
```

### test-plan-xmind-generator

```text
根据这份 PRD ，生成测试计划和 XMind。
```

### testcase-generator

```text
根据这份 PRD 生成测试用例。
```

### apifox-tests

首次接入建议先直接在终端验证一条从 Apifox 复制出来的 CLI 命令，确认 `apifox-cli`、Access Token 和测试场景本身都可用。

先列测试：

```bash
node skills/apifox-tests/scripts/list-tests.js
```

再执行：

```bash
node skills/apifox-tests/scripts/run-cli.js tests/获取项目列表测试.md test
```

如果你需要完整理解这套工作流，继续看：

- [Apifox CLI + Agent Skills](apifox-cli-agent-skills.md)

### defect-analysis

```bash
python3 skills/defect-analysis/scripts/generate_defect_analysis_report.py \
  --project "示例项目" \
  --iteration "Sprint 12"
```

### test-report-generator

```bash
python3 skills/test-report-generator/scripts/generate_teambition_test_report.py \
  --project "示例项目" \
  --iteration "Sprint 12"
```
