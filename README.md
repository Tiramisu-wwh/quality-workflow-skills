# Quality Workflow Skills

公开发布的质量门禁相关 skills 仓库，可通过 `npx skills add` 直接安装。

## 包含的 Skills

- `prd-gatekeeper`
- `secure-code-review`
- `test-plan-xmind-generator`
- `testcase-generator`
- `apifox-tests`
- `defect-analysis`
- `test-report-generator`

## 仓库定位

这个仓库维护的是一组可公开分发的质量流程 skills，重点覆盖从需求评审到测试复盘的主链路。它适合下面几类场景：

- 产品、研发、测试希望按统一口径协作，不再各自写一套临时提示词
- 需求、代码、测试和复盘资料需要有固定输入输出
- 团队希望先把质量流程跑顺，再按项目逐步接入自己的模板、鉴权和数据源

当前主流程覆盖以下环节：

`需求准入 -> 代码安全审计 -> 测试计划 -> 测试用例 -> 接口自动化 -> 缺陷分析 / 测试报告`

其中有两个前置环节已经单独接入到上游角色侧：

- `prd-gatekeeper` 已前置提供给 PRD Agent。
- `secure-code-review` 已前置提供到开发侧 code review 阶段，测试阶段不需要再单独执行一次，但仓库继续保留该 skill 入口。

当前范围不包含发布审批、统一 CI 平台接入和非质量主题的通用工具。

## 主流程能力

| 环节 | 主要使用人 | Skill | 什么时候用 | 主要输入 | 主要输出 | 给下游提供什么 |
| --- | --- | --- | --- | --- | --- | --- |
| 需求准入 | 产品、项目、QA | `prd-gatekeeper` | PRD 初稿完成后、评审前，通常由 PRD Agent 前置执行 | PRD、BRD、技术方案、Figma、Figma Make | Excel 准入评审报告 | 明确需求是否完整、是否可测、缺哪些关键内容 |
| 代码安全审计 | 开发、架构、安全、QA | `secure-code-review` | 开发侧 code review、提测前、合并前、发布前 | 源码目录 | 高风险问题清单、控制矩阵、审查结论 | 明确哪些风险必须先修，哪些点需要人工确认 |
| 测试计划 | QA | `test-plan-xmind-generator` | 需求范围稳定后、正式写用例前 | PRD、设计稿、接口文档、技术方案 | `test-plan.md`、`.xmind` | 统一测试范围、重点模块、主流程和风险点 |
| 测试用例 | QA | `testcase-generator` | 测试计划确认后 | PRD、设计稿、接口文档、测试计划 | 结构化测试用例、冒烟集、可选 UI 自动化场景 | 给执行测试、接口回归和自动化筛选提供基础数据 |
| 接口自动化 | 开发、QA | `apifox-tests` | 联调、自测、回归、发布前复核 | 环境、测试场景或测试套件 | 执行结果和失败原因解读 | 快速确认接口链路是否可用，识别回归问题 |
| 缺陷分析 | QA、测试负责人、项目经理 | `defect-analysis` | 迭代中、迭代后复盘 | 项目、迭代或日期范围 | 缺陷分析报告 | 说明问题主要集中在哪些环境、等级、分类和原因 |
| 测试报告 | QA、测试负责人、项目经理 | `test-report-generator` | 提测结束、迭代收口 | 项目、迭代 | 测试报告 | 汇总计划、执行、缺陷和未完成项，给项目结项或汇报使用 |

## 每个环节解决什么问题

### 1. `prd-gatekeeper`

这一步先看需求资料是否达到可评审、可排期、可测试的基本标准。它会把缺失项、冲突点和高风险模糊项提前暴露出来，避免测试计划和测试用例建立在不完整输入上。

目前这个能力已经前置提供给 PRD Agent。对于已经有 Figma 或 Figma Make 的项目，可以把页面结构、字段和交互线索一起纳入判断；测试侧默认消费它的评审结果，不需要再重复补做一轮同类检查。

### 2. `secure-code-review`

这一步处理“代码是否已经具备进入测试或发布的基本安全条件”。它关注的是源码里能直接看到的鉴权、输入校验、日志、文件、加密和外部调用风险，不把运行环境里的控制措施混写成已满足。

目前这个能力已经前置提供到开发侧 code review 阶段。测试阶段默认不再单独执行一次同样的源码安全审查，但仓库继续保留该 skill 入口，便于需要补审、回溯或独立接入的团队继续使用。

### 3. `test-plan-xmind-generator`

这一步把需求资料整理成测试视角的范围说明。重点是先把模块拆分、测试重点、异常流、依赖和风险讲清楚，再进入大批量写用例。

如果一个项目输入很多，来源又不一致，这个环节可以先统一测试口径，减少后续用例返工。

### 4. `testcase-generator`

这一步把需求和计划落成可执行的测试内容。除了完整测试用例，它还会顺带给出冒烟集；如果用户关注 UI 自动化，还可以补充适合 Midscene 的自然语言场景。

这个 skill 适合作为测试执行前的主产出环节。它把“测什么、怎么测、哪些先测”固定下来，后续无论是人工执行还是自动化筛选，都有统一基础。

### 5. `apifox-tests`

这一步处理“已经有测试集，怎么快速验证接口状态”。它不负责设计测试，而是负责执行已有的 Apifox 自动化测试并解释结果，适合联调、自测、指定回归和发布前复核。

如果团队已经把关键接口整理进 Apifox，这个环节能把接口验证从口头确认变成可复现执行。

### 6. `defect-analysis`

这一步面向复盘。它关注缺陷分布和原因归类，适合回答“这次问题主要出在哪里”“高风险缺陷集中在哪个环境”“是否有重复类型问题”这类管理问题。

适合在迭代中期发现趋势，也适合在迭代结束后做复盘输入。

### 7. `test-report-generator`

这一步面向交付总结。它把测试计划、用例、缺陷和待补字段汇总成一份标准报告，适合给项目经理、研发负责人或业务方做阶段说明。

如果说 `defect-analysis` 更偏问题结构，`test-report-generator` 更偏项目测试结果汇总，两者可以一起使用，也可以按场景单独使用。

## 推荐使用顺序

推荐顺序如下：

1. `prd-gatekeeper`
2. `secure-code-review`
3. `test-plan-xmind-generator`
4. `testcase-generator`
5. `apifox-tests`
6. `defect-analysis`
7. `test-report-generator`

这条顺序对应的是一个常见协作过程：

- 先由 PRD Agent 执行 `prd-gatekeeper`，确认需求资料是否足够支撑测试和排期。
- 再由开发侧在 code review 阶段执行 `secure-code-review`，提前暴露会影响提测结论的高风险问题。
- 然后统一测试范围和主流程，再批量产出测试用例。
- 接口自动化用于联调和回归验证。
- 缺陷分析和测试报告用于迭代内跟踪和收口汇报。

如果团队当前只缺其中一环，不需要一次接入全部 skill，可以按单个阶段拆开使用。

## 安装

安装整个仓库：

```bash
npx skills add Tiramisu-wwh/quality-workflow-skills
```

按仓库 URL 安装：

```bash
npx skills add https://github.com/Tiramisu-wwh/quality-workflow-skills
```

按单个 skill 安装：

```bash
npx skills add Tiramisu-wwh/quality-workflow-skills --skill prd-gatekeeper
npx skills add Tiramisu-wwh/quality-workflow-skills --skill secure-code-review
npx skills add Tiramisu-wwh/quality-workflow-skills --skill test-plan-xmind-generator
npx skills add Tiramisu-wwh/quality-workflow-skills --skill testcase-generator
npx skills add Tiramisu-wwh/quality-workflow-skills --skill apifox-tests
npx skills add Tiramisu-wwh/quality-workflow-skills --skill defect-analysis
npx skills add Tiramisu-wwh/quality-workflow-skills --skill test-report-generator
```

## 环境准备

- Python 3.11 或更高版本
- Node.js 18 或更高版本
- `git`、`rg`

常用依赖：

```bash
python3 -m pip install xlsxwriter openpyxl requests
```

Apifox CLI 前置准备：

1. 确认电脑已安装 Node 环境：

```bash
node -v
npm -v
```

2. 全局安装 Apifox CLI：

```bash
npm install -g apifox-cli
apifox --version
```

看到版本号，说明 Apifox CLI 已安装成功。

3. 到 Apifox 的“自动化测试 -> CI/CD”中，复制一个“测试场景”或“测试套件”的 CLI 命令到终端执行，并补上 Access Token。

看到测试输出，说明 Apifox CLI 可以正常工作。

Apifox skill 本地脚本依赖：

```bash
cd skills/apifox-tests
npm install
```

## 首次配置

### Apifox

先确认上面的 Apifox CLI 前置准备已经完成，再填写：

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
根据这份 PRD ，生成测试计划和 XMind。
```

### 4. 测试用例

```text
根据这份 PRD 生成测试用例。
```

### 5. 接口自动化

```text
用 apifox-tests 在 test 环境执行 获取项目列表测试，并解释结果。
```

如果是首次接入，先按“环境准备 -> Apifox CLI 前置准备”完成 Node、`apifox-cli`、Access Token 和 CLI 命令验证，再开始使用 skill。

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
- [Apifox CLI + Agent Skills](docs/apifox-cli-agent-skills.md)
- [Release Notes](RELEASE.md)

## 说明

- 这个公开仓库只保留可公开分发的通用 skill、脚本和模板占位文件。
- `apifox-tests/tests/` 中保留的是示例测试文件，接入新团队后通常需要替换成自己的测试集。
- `defect-analysis` 和 `test-report-generator` 依赖 Teambition OpenAPI，首次使用前需要补齐鉴权和映射文件。
