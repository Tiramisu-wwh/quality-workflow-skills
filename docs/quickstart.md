# Quickstart

## 1. 安装

```bash
npx skills add Tiramisu-wwh/quality-gate-skills
```

## 2. 依赖

```bash
python3 -m pip install xlsxwriter openpyxl requests
```

```bash
cd skills/apifox-tests
npm install
```

## 3. 配置

### Apifox

填写：

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
根据这份 PRD 和接口说明，生成测试计划和 XMind。
```

### testcase-generator

```text
根据这份 PRD 生成测试用例，并额外导出一份冒烟集。
```

### apifox-tests

先列测试：

```bash
node skills/apifox-tests/scripts/list-tests.js
```

再执行：

```bash
node skills/apifox-tests/scripts/run-cli.js tests/获取项目列表测试.md test
```

如果你需要完整理解这套工作流，继续看：

- [Apifox CLI + Claude Skills](apifox-cli-claude-skills.md)

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
