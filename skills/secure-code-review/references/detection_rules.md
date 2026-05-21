# Detection Rules

## Severity

- `critical`：可直接导致大规模数据泄露、远程命令执行、严重越权或密钥泄露
- `high`：高概率造成敏感数据暴露、认证绕过、任意文件访问或危险外部调用
- `medium`：存在安全弱点，但需要特定条件才能利用
- `low`：规范性问题或低影响隐患

## Confidence

- `high`：代码证据明确，基本不依赖推测
- `medium`：证据较强，但仍需少量上下文验证
- `low`：仅为候选风险，需要人工继续确认

## Needs Manual Review

以下问题通常不能仅靠源码直接证明：

- TLS / network / WAF / ingress
- MFA
- account lockout
- runtime secret platform
- object storage policy
- infrastructure hardening
