# Security Review Requirements

## 目录

- 1. 适用范围
- 2. 判定原则
- 3. 可直接通过源码审计的控制项
- 4. 只能部分通过源码推断的控制项
- 5. 需人工确认的控制项
- 6. 敏感信息词典

## 1. 适用范围

用于整理可落到源码审计的安全检查项。

适用语言：

- Java / Spring
- Node.js / TypeScript
- Python

## 2. 判定原则

- `pass`
  - 只有在源码中能看到正向控制证据时才使用
- `fail`
  - 源码中存在明确反例，或者高风险控制缺失
- `needs_manual_review`
  - 依赖部署、网关、运行参数、测试环境、外部系统或产品策略，无法单靠源码证明
- `not_applicable`
  - 系统没有对应功能，例如没有上传、没有密码找回、没有外部接口

不要把“未搜到危险代码”直接写成 `pass`。

## 3. 可直接通过源码审计的控制项

### 3.1 敏感信息处理

- 敏感信息不应出现在 HTTP GET 参数中
  - 重点查：
    - Java：`@GetMapping`、`RequestMethod.GET`
    - Node.js / TypeScript：`app.get`、`router.get`
    - Python：`@app.get`、`@router.get`、`request.args`
  - 高风险证据：`password`、`token`、`mobile`、`email`、`idCard` 等作为 GET 参数

- 敏感信息不得明文存储
  - 重点查：密码存储逻辑、配置文件、数据库字段写入前是否加密或哈希
  - 高风险证据：密码或证件号直接落库、配置文件明文口令

- 禁止硬编码密钥、密码、数据库账号口令
  - 重点查：`.java`、`.js`、`.ts`、`.py`、`.yml`、`.yaml`、`.properties`、`.env`
  - 高风险证据：`password = "..."`、`secret: "..."`、私钥内容直接进仓

- 敏感数据应脱敏展示
  - 重点查：DTO、serializer、schema、response model、template 组装
  - 说明：看到直接返回完整手机号、身份证、银行卡等可判 `fail`

- 响应字段不应超出用户请求或业务需要的范围
  - 重点查：对象直出、模型对象转 JSON、未裁剪字段返回
  - 说明：通常需要结合接口定义或前端调用确认

### 3.2 输入校验与输出编码

- 所有用户可控输入都要在服务端做最终合法性校验
  - 重点查：
    - Java：`@Validated`、Bean Validation、自定义校验器
    - Node.js / TypeScript：`zod`、`joi`、`class-validator`、`express-validator`
    - Python：`pydantic`、`marshmallow`、Django forms、serializers
  - 高风险证据：输入直接进入 SQL、文件路径、外部请求、模板或日志

- 危险字符应在服务端过滤、转义或做上下文相关编码
  - 重点查：模板回显、表达式求值、命令执行、HTML 输出、shell 参数
  - 高风险证据：用户输入未转义直接进入 HTML、脚本、命令、表达式

- URL 重定向应校验输入，并优先使用白名单
  - 重点查：
    - Java：`sendRedirect`、`redirect:`
    - Node.js / TypeScript：`res.redirect`
    - Python：`redirect(...)`

- 输出前应做上下文相关编码或净化
  - 重点查：HTML 输出、SQL / XML / LDAP 拼接、模板自动转义是否被绕开
  - 高风险证据：反射型 XSS、SQL 拼接、XXE 风险 XML 解析

### 3.3 异常、日志与调试代码

- 异常时不得向客户端暴露堆栈、源码、数据库结构、组件版本或敏感信息
  - 重点查：
    - Java：`printStackTrace()`、`return e.getMessage()`
    - Node.js / TypeScript：`res.send(err.message)`、直接回传异常对象
    - Python：`return str(e)`、调试模式泄露

- 应精确捕获异常并恰当处理，避免吞异常
  - 重点查：空 `catch` / `except`、只打印不处理、无回滚

- 日志中不得明文打印密码、手机、身份证、邮箱、银行卡等敏感信息
  - 重点查：`logger.*`、`console.log`、`print`、审计日志拼接内容

- 生产环境应去除调试和测试相关代码、配置、文件
  - 重点查：调试端点、硬编码测试账号、测试开关默认开启、`DEBUG=True`

### 3.4 认证、会话与访问控制

- 除公开内容外，入口先认证；最终认证在服务端完成
  - 重点查：公开接口列表、登录态校验、网关放行与服务端二次校验

- 涉及敏感信息或敏感操作的接口要做有效认证和必要的二次校验
  - 重点查：重置密码、导出、下载、审批、删除、权限变更、对外接口

- 会话标识和 token 应不可猜测，安全场景随机数应使用安全随机数
  - 重点查：
    - Java：`SecureRandom`
    - Node.js / TypeScript：`crypto.randomBytes`、`crypto.randomUUID`
    - Python：`secrets`、`os.urandom`

- Cookie 应设置 `HttpOnly` 和 `Secure`
  - 重点查：
    - Java：`new Cookie(...)`、`ResponseCookie.from(...)`
    - Node.js / TypeScript：`res.cookie(...)`
    - Python：`set_cookie(...)`

- 用户认证后应更新会话，防止会话固定
  - 重点查：登录成功后是否刷新 session 或 token

- 不要在 URL、错误信息或日志中暴露会话标识
  - 重点查：`sessionId`、`token` 是否被放进 query string、日志、异常信息

- 遵循最小权限原则，受保护资源只允许授权用户访问
  - 重点查：管理类接口、下载接口、对象级查询、`findById(id)`、`Model.objects.get(id=...)`、ORM 按主键直取、角色或权限是否只在前端控制

### 3.5 密码、加密与密钥

- 不得存在用户无法修改的密码，例如硬编码密码或重启恢复默认密码
  - 重点查：默认管理员账号、初始化口令、硬编码密码、重置逻辑

- 密码不得明文存储；不可逆存储应使用安全算法
  - 重点查：`MD5`、`SHA-1`、明文口令入库、无盐哈希

- 使用公开且安全的加密算法
  - 重点查：
    - Java：`MD5`、`SHA1`、`DES`、`RC4`、`AES/ECB`
    - Node.js / TypeScript：`createHash("md5")`、`createHash("sha1")`
    - Python：`hashlib.md5`、`hashlib.sha1`

- 密钥应安全存储，配置文件中的密钥字段至少要有缓解措施
  - 重点查：密钥是否直接写进仓库、是否有环境变量、密文配置、密钥托管平台迹象

- 安全场景随机数必须使用安全随机数
  - 重点查：token、IV、盐值、验证码、密钥生成

### 3.6 文件、解析与接口安全

- 上传下载要有身份验证；类型、大小校验在服务端；限制可执行文件
  - 重点查：
    - Java：`MultipartFile`
    - Node.js / TypeScript：`multer`、文件流、`req.files`
    - Python：`UploadFile`、`request.files`

- 建议检查文件头或魔数
  - 重点查：魔数校验、内容类型校验、专用文件检测库

- 上传完成或异常时删除临时文件
  - 重点查：临时目录、`finally` 清理、异常分支回收

- 解析 zip 时校验文件名、大小、个数，并防止解压穿越
  - 重点查：
    - Java：`ZipInputStream`
    - Node.js / TypeScript：zip 解压库与路径拼接
    - Python：`zipfile`

- 下载时校验文件名和路径，防止跨目录访问，并控制目录访问权限
  - 重点查：`new File(base + userInput)`、`path.join(base, userInput)`、`open(base + user_input)`、ID 索引方式下载

- 对外接口应做身份认证，例如签名校验
  - 重点查：对外接口、回调接口、内部接口的签名、token、mTLS 逻辑
  - 说明：很多场景需要结合网关、配置或对端系统

- 接口参数要有容错和防遍历设计，资源 ID 不应易于枚举
  - 重点查：`/{id}`、顺序主键直取、对象级鉴权

## 4. 只能部分通过源码推断的控制项

- 是否“超量返回”，通常需要结合接口契约或前端实际请求字段判断

- 是否满足业务规定的脱敏粒度，通常需要产品确认

- 接口认证可能部分在网关或对端系统，源码只能看到一部分

- 是否完整记录关键审计事件，往往需要结合产品操作面和运行日志样本

## 5. 需人工确认的控制项

以下问题默认不要仅凭源码写成 `pass`：

- HTTPS / TLS 版本和加密套件
- 浏览器自动填充策略
- 登录失败锁定、延迟、验证码触发阈值
- MFA 是否强制开启
- 注册验证码、短信验证码、图形验证码的频率、一次一用和有效期
- 会话超时时间
- 开放端口收敛
- 密码复杂度和定期轮换策略
- 文件是否落专用文件服务器、目录是否无执行权限
- 密钥托管平台或分层管理是否真实启用

## 6. 敏感信息词典

以下字段可作为审计关键词表：

- 身份信息：姓名、身份证、护照、社保卡、居住证、工号
- 账号与认证信息：用户名、密码、口令、token、session、验证码、证书、密钥
- 联系方式：手机号、邮箱、住址、通讯录、好友列表
- 财产信息：银行卡号、账户、交易记录、流水、征信
- 健康信息：病症、诊断、检验报告、过敏史、病史、住院记录
- 生物识别：指纹、声纹、虹膜、人脸
- 设备与网络身份：IP、MAC、IMEI、Android ID、IDFA、GUID、IMSI
- 位置与行为：定位、行踪轨迹、浏览记录、操作日志

如果代码里出现这些数据的直出、明文日志、GET 传参、硬编码或明文存储，都要优先审。
