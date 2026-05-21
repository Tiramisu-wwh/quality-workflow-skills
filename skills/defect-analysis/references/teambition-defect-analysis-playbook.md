# Teambition Defect Analysis Playbook

这份文档用于说明 `defect-analysis` 底层脚本依赖的 Teambition OpenAPI 调用链。

## 必备文件

- `assets/teambition-auth.env`
- `assets/teambition-id-mapping.json`

## 鉴权

先获取 `appToken`：

- `POST https://open.teambition.com/api/appToken`

后续请求统一带：

- `Authorization`
- `X-Tenant-Id`
- `X-Tenant-Type`
- `X-Operator-Id`

## 主要取数接口

- `GET /v3/project/query`
- `GET /v3/project/{projectId}/scenariofieldconfig/search`
- `GET /v3/project/{projectId}/customfield/search`
- `GET /v3/project/{projectId}/task/query`
- `GET /v3/project/{projectId}/taskflowstatus/search`
- `GET /v3/project/{projectId}/sprint/search`

## 使用方式

如果脚本无法直接命中项目、字段或状态映射，优先检查：

1. `teambition-auth.env` 是否完整
2. `teambition-id-mapping.json` 是否是当前团队版本
3. 当前账号是否具备对应 scope

## 输出重点

- 缺陷总数
- 环境分布
- 状态分布
- 严重程度分布
- 分类分布
- 原因分析和交叉分析
