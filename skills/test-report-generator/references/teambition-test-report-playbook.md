# Teambition Test Report Playbook

这份文档用于说明 `test-report-generator` 底层脚本的取数方式和依赖文件。

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
- `GET /v3/project/{projectId}/sprint/search`
- `GET /v3/project/{projectId}/testplan`
- `GET /v3/project/{projectId}/testcase/query`
- `GET /v3/project/{projectId}/task/query`
- `GET /v3/project/{projectId}/taskflowstatus/search`

## 使用方式

如果脚本无法正确生成报告，优先检查：

1. `teambition-auth.env` 是否完整
2. `teambition-id-mapping.json` 是否是当前团队版本
3. 当前账号是否具备测试计划、测试用例、缺陷相关 scope

## 输出重点

- 测试计划信息
- 测试用例统计
- 缺陷统计
- 需要人工补充的字段
