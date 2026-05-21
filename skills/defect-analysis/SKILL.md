---
name: defect-analysis
description: Use when the user asks to generate a Teambition defect analysis report by iteration or date range, including environment, severity, classification, and cause analysis.
---

# Teambition Defect Analysis

这个 skill 直接请求 Teambition OpenAPI，生成项目缺陷分析报告。

## 触发条件

- 用户要求按 `项目 + 迭代` 生成缺陷分析报告
- 用户要求按 `项目 + 日期范围` 生成缺陷分析报告
- 输出需要包含环境、严重程度、分类、原因等维度统计

## 固定输入

- `--project "<项目名称>"`，必填
- `--iteration "<迭代名称>"`，与日期范围二选一
- `--start-date "YYYY-MM-DD"`，与 `--end-date` 配合使用
- `--end-date "YYYY-MM-DD"`，与 `--start-date` 配合使用

可选输入：

- `--date-basis "created|updated|accomplishTime"`，默认 `created`
- `--output "<输出文件路径>"`

默认输出路径：

- `./outputs/defect-analysis/<项目名称>_<迭代或日期范围>_defect-analysis.md`

## 鉴权

固定读取 `assets/teambition-auth.env`。

如果任一字段为空，先补齐再执行：

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

公开仓库里这个文件是空模板。首次接入时，需替换成当前团队自己的映射版本。

## 直接执行

按迭代生成：

```bash
python3 scripts/generate_defect_analysis_report.py \
  --project "示例项目" \
  --iteration "Sprint 12"
```

按日期范围生成：

```bash
python3 scripts/generate_defect_analysis_report.py \
  --project "示例项目" \
  --start-date "2026-04-01" \
  --end-date "2026-04-30"
```

## 默认行为

- 项目名称先转 `projectId`
- 自动识别缺陷类型、环境、严重程度、分类和原因字段
- 按 `迭代` 或 `日期范围` 过滤缺陷
- 输出环境、状态、严重程度、分类、原因等维度统计
- 输出原因交叉分析：
  - 原因与严重程度
  - 原因与状态
  - 原因与环境
  - 原因与迭代

## 返回要求

聊天窗口不要输出整份报告，只返回：

- 生成文件路径
- projectId
- sprintId（如有）
- 缺陷总数
- 主要风险
- 数据局限
