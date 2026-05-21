---
name: test-report-generator
description: Use when the user asks to generate a Teambition iteration test report from project, sprint, test plan, test case, and defect data.
---

# Teambition Test Report Generator

交付目标：

- 输入：`项目名称`、`迭代名称`
- 输出：一份按模板填充后的 Markdown 测试报告
- 数据来源：项目、迭代、测试计划、测试用例、缺陷

## 固定输入

- `--project "<项目名称>"`
- `--iteration "<迭代名称>"`

可选输入：

- `--output "<输出文件路径>"`

默认输出路径：

- `./outputs/test-reports/<项目名称>_<迭代名称>_test-report.md`

## 鉴权

固定读取 `assets/teambition-auth.env`：

```env
TEAMBITION_APP_ID=""
TEAMBITION_APP_SECRET=""
TEAMBITION_TENANT_ID=""
TEAMBITION_TENANT_TYPE="organization"
TEAMBITION_OPERATOR_ID=""
```

## 映射文件

项目和人员映射默认读取：

- `assets/teambition-id-mapping.json`

公开仓库里这个文件是空模板，首次接入时需要替换成当前团队自己的映射版本。

## 直接执行

```bash
python3 scripts/generate_teambition_test_report.py \
  --project "示例项目" \
  --iteration "Sprint 12"
```

如果需要指定输出文件：

```bash
python3 scripts/generate_teambition_test_report.py \
  --project "示例项目" \
  --iteration "Sprint 12" \
  --output "/absolute/path/report.md"
```

## 默认行为

- 项目名称先转 `projectId`
- 迭代名称先转 `sprintId`
- 测试计划名称再转 `testplanId`
- 按 `testplanId` 拉测试用例
- 按 `sprintId` 拉缺陷
- 按报告模板输出 Markdown

## 返回要求

聊天窗口不要输出整份报告，只返回：

- 生成文件路径
- projectId
- sprintId
- testplanId
- 用例统计
- 缺陷统计
- 需要人工补充的字段
