# Public Release Notes

## 发布前检查

1. 确认新增内容属于可公开分发范围。
2. 检查 `skills/<skill-name>/SKILL.md` frontmatter 只包含：
   - `name`
   - `description`
3. 检查是否残留以下内容：
   - 本机绝对路径
   - access token、cookie、环境密钥
   - 内部项目名、真实映射 ID、私有链接
   - 本地测试产物、报告文件、运行输出
4. 删除 `node_modules`、`__pycache__`、`outputs`、`output`、`apifox-reports`。

## 验证建议

- Python skill：`python3 -m py_compile <script>`
- 有单测的 skill：`python3 -m unittest discover -s tests -v`
- Node skill：在对应目录执行 `npm install` 后跑最小脚本检查
- `SKILL.md`：确认 `description` 只描述触发条件，不写执行流程

## 发布步骤

1. 更新 `README.md`、`docs/quickstart.md` 和技能列表。
2. 提交代码：

```bash
git add .
git commit -m "feat: update public skills"
```

3. 打版本 tag：

```bash
git tag v0.1.0
```

4. 推送分支和 tag：

```bash
git push origin main
git push origin v0.1.0
```
