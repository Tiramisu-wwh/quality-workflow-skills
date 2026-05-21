# Security Review Checklist

这份清单用于公开版源码安全审查 skill，不绑定内部编号。

## 1. Secrets And Sensitive Data

- 是否存在硬编码密钥、token、私钥、访问凭据
- 是否把敏感字段放在 GET 参数、日志或错误返回中
- 是否存在过量返回的个人或业务敏感信息

## 2. Input Validation And Output Handling

- 是否对输入做服务端校验
- 是否存在 SQL 注入、命令执行、XSS、XXE、SSRF 风险
- 是否把未处理的错误信息直接返回给客户端

## 3. Auth And Access Control

- 入口是否有认证
- 资源读取和修改是否做服务端鉴权
- 是否存在越权访问、ID 可遍历、角色边界缺失

## 4. Session And Token Handling

- Cookie 是否设置 `HttpOnly` / `Secure`
- token 或 session ID 是否由强随机数生成
- 会话标识是否暴露在 URL、日志或明文配置中

## 5. File Handling

- 上传是否校验类型、大小、文件名
- 下载是否校验权限和路径
- 压缩包解压是否防止 zip slip

## 6. Crypto And Randomness

- 是否使用弱哈希、弱加密、弱随机数
- 口令是否安全存储
- 密钥是否有安全的配置或托管方式

## 7. Logging And Exceptions

- 日志是否脱敏
- 是否有统一异常处理
- 是否向客户端暴露堆栈、路径、库版本、数据库信息

## 8. External Calls

- 外部 URL 是否可被用户输入控制
- 重定向目标是否受控
- 对第三方回调或 webhook 是否有签名、token 或来源校验
