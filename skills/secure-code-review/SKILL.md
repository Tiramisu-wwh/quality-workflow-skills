---
name: secure-code-review
description: Use when a team wants a structured source-code security review before merge, release, or handoff, especially for Java, Node.js / TypeScript, or Python services.
---

# Secure Code Review

这个 skill 用于做通用源码安全审查，不绑定任何专有内规或编号体系。

它的目标不是只跑一轮正则，而是把“代码语义审查 + 预扫描线索 + 结构化输出”串起来，帮助团队在开发 receive、提测前或发布前更早发现高风险问题。

## 适用场景

- 新仓库接入前做一次基线安全审查
- 功能开发完成后做 merge 前审查
- 发布前做高风险问题排查
- 接手陌生服务时快速识别鉴权、文件、日志、加密、外部调用风险

## Start

1. 先读取 `references/security_review_checklist.md`。
2. 再读取 `references/agent_review_playbook.md`。
3. 识别主语言后，只加载对应提示文件：
   - Java：`references/java_review_signals.md`
   - Node.js / TypeScript：`references/node_ts_review_signals.md`
   - Python：`references/python_review_signals.md`
4. 只有在需要统一风险口径时，再读 `references/detection_rules.md`。

## Review Workflow

1. 先圈定范围。
   - 入口：controller、route、handler、view
   - 安全边界：auth、guard、middleware、filter、dependency
   - 风险功能：上传下载、压缩包解压、XML / YAML / 反序列化、外部 HTTP 调用、日志、配置
   - 敏感对象：password、token、session、cookie、验证码、资源 ID

2. 先做预扫描收集线索。

```bash
python3 scripts/secure_review_scan.py /path/to/project --format markdown
```

把这一步当成候选问题列表，不要直接当结论。

3. 再用 `rg` 缩小人工审查范围。

```bash
rg -n "GetMapping|RequestMapping|router\\.|app\\.(get|post|put|delete)|@router\\.|PreAuthorize|Secured|RolesAllowed|MultipartFile|multer|UploadFile|request\\.files|zipfile|ZipInputStream|pickle\\.load|yaml\\.load|DocumentBuilderFactory|requests\\.|axios\\.|fetch\\(|exec\\(|subprocess\\.|child_process|redirect\\(|res\\.redirect|set_cookie|res\\.cookie|printStackTrace|error\\.message|MD5|SHA-1|DES|RC4|Math\\.random|new Random|findById\\(|SELECT |INSERT |UPDATE |DELETE " /path/to/project
```

4. 对高风险链路做语义追踪。
   - 追输入来源：参数、请求体、Header、Cookie、Multipart、配置项、外部响应
   - 追缓解措施：鉴权、校验、白名单、编码、事务回滚、统一异常处理、文件隔离、强加密、安全随机数
   - 追危险 sink：SQL、命令执行、重定向、外部请求、文件路径、日志、异常返回、模板回显、下载接口
   - 判断缓解措施是否真实落在当前链路上

5. 输出结构化结论。
   - `pass`：能从源码直接证明控制有效
   - `fail`：存在明确风险或关键控制缺失
   - `needs_manual_review`：依赖部署、网关、运行配置、产品规则或外部系统
   - `not_applicable`：当前系统没有该类能力

6. 明确边界。
   - 不要因为“没搜到”就判定为安全
   - 不要把 TLS、WAF、KMS、MFA、端口收敛、账号策略这类运行态要求写成“已满足”
   - 对越权、资源 ID、文件下载等问题，要结合业务对象和权限链路下结论

## What To Look For

- 敏感信息：硬编码密钥、GET 传敏感字段、过量返回、明文日志、明文存储
- 输入输出：服务端校验、输出编码、SQL 注入、XSS、SSRF、命令执行、重定向、XXE
- 认证授权：入口认证、资源级访问控制、敏感接口二次校验、越权访问
- 会话安全：Cookie 属性、token 随机性、session 更新、会话 ID 是否出现在 URL / 日志
- 文件安全：类型白名单、大小限制、路径规范化、临时文件清理、zip 解压防护、下载鉴权
- 加密与随机数：弱算法、弱随机数、口令存储方式、密钥管理方式
- 日志与异常：敏感信息脱敏、统一异常处理、禁止堆栈和内部细节直出

## Output Requirements

输出至少包含：

- 审查结论：`pass` / `conditional_pass` / `fail`
- 高风险发现：文件、行号、攻击路径、修复建议
- 控制矩阵：`pass / fail / needs_manual_review / not_applicable`
- `needs_manual_review` 列表：说明为什么不能只靠源码证明
- 残余风险：说明本次未覆盖或无法完全证明的区域

优先使用 `assets/report_template.md` 的结构。

## Scripts

- `scripts/secure_review_scan.py`
  - 通用多语言预扫描器
  - 支持 Java、Node.js / TypeScript、Python
  - 输出候选问题、风险类别和需人工确认项

## Assets

- `assets/report_template.md`：通用源码安全审查报告模板
