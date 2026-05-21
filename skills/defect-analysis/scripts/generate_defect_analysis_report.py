#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


BASE_URL = "https://open.teambition.com/api"
ROOT = Path(__file__).resolve().parents[1]
AUTH_ENV = ROOT / "assets" / "teambition-auth.env"
MAPPING_JSON = ROOT / "assets" / "teambition-id-mapping.json"

DATE_BASE_FIELDS = {"created", "updated", "accomplishTime"}
OPEN_STATUS_KEYWORDS = ("待", "处理中", "修复中", "进行中", "待验证", "重新打开", "打开")
DEFERRED_STATUS_KEYWORDS = ("延期", "后续迭代", "暂不处理")
CLOSED_STATUS_KEYWORDS = ("关闭", "已解决", "done", "已完成")

FIELD_PATTERNS = {
    "environment": ["缺陷所在环境", "发现环境", "环境", "environment", "env"],
    "severity": ["严重程度", "缺陷等级", "severity", "等级"],
    "classification": ["缺陷类型", "问题类型", "分类", "bug type", "issue type"],
    "cause_category": ["缺陷原因分类", "根因分类", "原因分类", "原因归属"],
    "cause_text": ["缺陷原因", "根因", "原因描述", "原因"],
    "test_plan": ["测试计划", "test plan"],
    "test_round": ["测试轮次", "轮次", "批次", "阶段"],
    "module": ["模块", "业务域", "domain", "所属模块", "归属模块"],
}

INFERRED_CAUSE_KEYWORDS = {
    "需求理解": ["需求", "规则", "文案", "业务"],
    "设计遗漏": ["设计", "异常场景", "边界", "交互"],
    "配置问题": ["配置", "参数", "环境变量"],
    "环境问题": ["环境", "uat", "生产", "测试环境", "发布"],
    "数据问题": ["数据", "导入", "同步", "映射"],
    "校验缺失": ["校验", "校对", "检查", "校验逻辑"],
    "接口联调": ["接口", "联调", "返回", "请求"],
    "权限控制": ["权限", "角色", "鉴权"],
    "模型或提示词": ["提示词", "模型", "翻译效果", "术语"],
}


def normalize(text: str) -> str:
    return re.sub(r"[\s（）()_\-]+", "", text or "").lower()


def load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def require_auth() -> dict[str, str]:
    env = load_env_file(AUTH_ENV)
    required = [
        "TEAMBITION_APP_ID",
        "TEAMBITION_APP_SECRET",
        "TEAMBITION_TENANT_ID",
        "TEAMBITION_TENANT_TYPE",
        "TEAMBITION_OPERATOR_ID",
    ]
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise SystemExit(f"鉴权文件缺少字段: {', '.join(missing)}")
    return env


def load_mapping() -> dict[str, Any]:
    if not MAPPING_JSON.exists():
        raise SystemExit(f"缺少映射文件: {MAPPING_JSON}")
    return json.loads(MAPPING_JSON.read_text(encoding="utf-8"))


class TBApiError(RuntimeError):
    def __init__(self, path: str, payload: dict[str, Any]) -> None:
        self.path = path
        self.payload = payload
        message = payload.get("errorMessage") or "未知错误"
        error_code = payload.get("errorCode") or ""
        required_scopes = ((payload.get("accessDeniedDetail") or {}).get("requiredScopes")) or []
        detail = f"{path} 返回错误 errorCode={error_code}, errorMessage={message}"
        if required_scopes:
            detail += f", requiredScopes={','.join(required_scopes)}"
        super().__init__(detail)


class TBClient:
    def __init__(self, auth: dict[str, str]) -> None:
        self.auth = auth
        self.token = self._get_token()

    def _get_token(self) -> str:
        payload = {
            "appId": self.auth["TEAMBITION_APP_ID"],
            "appSecret": self.auth["TEAMBITION_APP_SECRET"],
        }
        resp = requests.post(f"{BASE_URL}/appToken", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("appToken")
        if not token:
            raise SystemExit(f"获取 appToken 失败: {data}")
        return token

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": self.token,
            "X-Tenant-Id": self.auth["TEAMBITION_TENANT_ID"],
            "X-Tenant-Type": self.auth["TEAMBITION_TENANT_TYPE"],
            "X-Operator-Id": self.auth["TEAMBITION_OPERATOR_ID"],
            "Accept": "application/json",
        }

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = requests.get(f"{BASE_URL}{path}", headers=self.headers(), params=params or {}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("errorCode"):
            raise TBApiError(path, data)
        return data

    def paginate(self, path: str, params: dict[str, Any] | None = None, result_key: str = "result") -> list[dict[str, Any]]:
        current = dict(params or {})
        current.setdefault("pageSize", 1000)
        page_token = ""
        items: list[dict[str, Any]] = []
        while True:
            if page_token:
                current["pageToken"] = page_token
            data = self.get(path, params=current)
            items.extend(data.get(result_key) or [])
            page_token = data.get("nextPageToken") or ""
            if not page_token:
                break
        return items


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def iso_date(value: str | None) -> str:
    dt = parse_iso_datetime(value)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d") if dt else "未获取到"


def percent(numerator: int, denominator: int) -> str:
    if not denominator:
        return "0.00%"
    return f"{(numerator / denominator) * 100:.2f}%"


def customfield_values(task: dict[str, Any], cf_id: str) -> list[str]:
    for field in task.get("customfields") or []:
        if field.get("cfId") != cf_id:
            continue
        values = []
        for item in field.get("value") or []:
            title = item.get("title")
            if title:
                values.append(str(title))
        return values
    return []


def build_customfield_value_map(task: dict[str, Any], field_defs: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for field in task.get("customfields") or []:
        cf_id = field.get("cfId")
        if not cf_id:
            continue
        name = field_defs.get(cf_id, {}).get("name") or cf_id
        values = []
        for item in field.get("value") or []:
            title = item.get("title")
            if title is not None:
                values.append(str(title))
        result[name] = values
    return result


def find_field_ids(field_defs: dict[str, dict[str, Any]], patterns: list[str]) -> list[str]:
    ranked: list[tuple[int, str]] = []
    for cf_id, meta in field_defs.items():
        name = str(meta.get("name") or "")
        normalized_name = normalize(name)
        score = 0
        for pattern in patterns:
            normalized_pattern = normalize(pattern)
            if normalized_name == normalized_pattern:
                score = max(score, 100)
            elif normalized_pattern in normalized_name:
                score = max(score, 50)
        if score:
            ranked.append((score, cf_id))
    ranked.sort(reverse=True)
    return [cf_id for _, cf_id in ranked]


def extract_field_value(task: dict[str, Any], field_defs: dict[str, dict[str, Any]], purpose: str) -> list[str]:
    values: list[str] = []
    for cf_id in find_field_ids(field_defs, FIELD_PATTERNS[purpose]):
        values = customfield_values(task, cf_id)
        if values:
            return values
    if purpose == "environment":
        for field in task.get("customfields") or []:
            raw_values = [str(item.get("title")) for item in field.get("value") or [] if item.get("title")]
            guessed = [v for v in raw_values if any(k in v.lower() for k in ("uat", "生产", "测试环境", "sit", "环境"))]
            if guessed:
                return guessed
    return values


def resolve_project(project_name: str, mapping: dict[str, Any], client: TBClient) -> dict[str, Any]:
    projects = mapping.get("projects") or {}
    if project_name in projects and projects[project_name].get("project_id"):
        return projects[project_name]
    normalized = normalize(project_name)
    for data in projects.values():
        if data.get("normalized_name") == normalized and data.get("project_id"):
            return data
    results = client.paginate(
        "/v3/project/query",
        params={"name": project_name, "visible": "organization", "includeTemplate": "false"},
    )
    if not results:
        raise SystemExit(f"未找到项目: {project_name}")
    exact = [item for item in results if item.get("name") == project_name]
    candidates = exact or results
    candidates.sort(key=lambda item: item.get("updated") or "", reverse=True)
    chosen = candidates[0]
    return {
        "name": chosen["name"],
        "normalized_name": normalize(chosen["name"]),
        "project_id": chosen["id"],
        "tasklists": [],
        "stages": [],
        "sfc": [],
        "tfs": [],
    }


def choose_sprint(project_id: str, iteration_name: str, client: TBClient) -> dict[str, Any] | None:
    sprints = client.paginate(f"/v3/project/{project_id}/sprint/search", params={"q": iteration_name})
    if not sprints:
        sprints = client.paginate(f"/v3/project/{project_id}/sprint/search")
    if not sprints:
        return None
    normalized = normalize(iteration_name)
    exact = [item for item in sprints if item.get("name") == iteration_name]
    if exact:
        return exact[0]
    normalized_hits = [item for item in sprints if normalize(item.get("name", "")) == normalized]
    if normalized_hits:
        return normalized_hits[0]
    contains = [item for item in sprints if normalized in normalize(item.get("name", ""))]
    if contains:
        contains.sort(key=lambda item: item.get("updated") or "", reverse=True)
        return contains[0]
    return None


def get_bug_scenario(project_id: str, client: TBClient) -> dict[str, Any]:
    configs = client.paginate(f"/v3/project/{project_id}/scenariofieldconfig/search")
    candidates = []
    for item in configs:
        name = str(item.get("name") or "")
        icon = str(item.get("icon") or "")
        source = str(item.get("source") or "")
        score = 0
        if source == "application.bug":
            score += 100
        if icon == "bug":
            score += 50
        if "缺陷" in name or "bug" in name.lower():
            score += 20
        if score:
            candidates.append((score, item))
    if not candidates:
        raise SystemExit(f"项目 {project_id} 未识别到缺陷任务类型")
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def get_customfield_defs(project_id: str, client: TBClient) -> dict[str, dict[str, Any]]:
    fields = client.paginate(f"/v3/project/{project_id}/customfield/search")
    defs: dict[str, dict[str, Any]] = {}
    for item in fields:
        cf_id = item.get("id")
        if not cf_id:
            continue
        defs[cf_id] = {
            "id": cf_id,
            "name": item.get("name"),
            "type": item.get("type"),
            "choices": {choice.get("id"): choice.get("value") for choice in item.get("choices") or [] if choice.get("id")},
        }
    return defs


def get_status_map(project_id: str, taskflow_id: str | None, client: TBClient) -> dict[str, dict[str, str]]:
    statuses = client.paginate(f"/v3/project/{project_id}/taskflowstatus/search")
    result: dict[str, dict[str, str]] = {}
    for item in statuses:
        if taskflow_id and item.get("taskflowId") != taskflow_id:
            continue
        if item.get("id"):
            result[item["id"]] = {"name": item.get("name") or "", "kind": item.get("kind") or ""}
    return result


def get_bug_tasks(project_id: str, bug_sfc_id: str, client: TBClient) -> list[dict[str, Any]]:
    return client.paginate(
        f"/v3/project/{project_id}/task/query",
        params={"q": f'sfcId = "{bug_sfc_id}"', "includeArchived": "false"},
    )


def filter_by_date(tasks: list[dict[str, Any]], start_date: str | None, end_date: str | None, basis: str) -> list[dict[str, Any]]:
    if not start_date and not end_date:
        return tasks
    start = parse_date(start_date) if start_date else None
    end = parse_date(end_date) if end_date else None
    filtered = []
    for task in tasks:
        current = parse_iso_datetime(task.get(basis))
        if not current:
            continue
        current = current.astimezone(timezone.utc)
        if start and current < start:
            continue
        if end and current > end.replace(hour=23, minute=59, second=59):
            continue
        filtered.append(task)
    return filtered


def filter_by_iteration(
    tasks: list[dict[str, Any]],
    iteration_name: str | None,
    sprint: dict[str, Any] | None,
    field_defs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if not iteration_name:
        return tasks
    target_norm = normalize(iteration_name)
    sprint_id = sprint.get("id") if sprint else None
    sprint_name = sprint.get("name") if sprint else iteration_name
    filtered = []
    for task in tasks:
        if sprint_id and task.get("sprintId") == sprint_id:
            filtered.append(task)
            continue
        matched = False
        for purpose in ("test_plan", "test_round"):
            values = extract_field_value(task, field_defs, purpose)
            for value in values:
                value_norm = normalize(value)
                if value_norm == target_norm or target_norm in value_norm or value_norm in normalize(sprint_name):
                    matched = True
                    break
            if matched:
                break
        if matched:
            filtered.append(task)
    return filtered


def classify_status(status_name: str, status_kind: str = "") -> str:
    if status_kind == "end":
        return "closed"
    low = status_name.lower()
    if any(keyword in status_name for keyword in DEFERRED_STATUS_KEYWORDS):
        return "deferred"
    if any(keyword in status_name for keyword in CLOSED_STATUS_KEYWORDS) or low == "done":
        return "closed"
    return "open"


def infer_severity(task: dict[str, Any], field_defs: dict[str, dict[str, Any]]) -> str:
    values = extract_field_value(task, field_defs, "severity")
    if values:
        explicit = str(values[0]).strip().upper()
        if explicit in {"P0", "P1", "P2", "P3", "P4", "P5"}:
            if explicit in {"P0", "P1", "P2", "P3"}:
                return explicit
            return "P3"
    priority = task.get("priority")
    try:
        priority = int(priority)
    except Exception:
        return "未识别"
    # Clinical data analysis platform bug priority uses descending numeric levels:
    # 2 -> P0, 1 -> P1, 0 -> P2, negative values -> P3.
    if priority >= 2:
        return "P0"
    if priority == 1:
        return "P1"
    if priority == 0:
        return "P2"
    return "P3"


def infer_classification(task: dict[str, Any], field_defs: dict[str, dict[str, Any]]) -> str:
    values = extract_field_value(task, field_defs, "classification")
    return values[0] if values else "未识别"


def infer_environment(task: dict[str, Any], field_defs: dict[str, dict[str, Any]]) -> str:
    values = extract_field_value(task, field_defs, "environment")
    return " / ".join(values) if values else "未识别"


def infer_module(task: dict[str, Any], field_defs: dict[str, dict[str, Any]]) -> str:
    values = extract_field_value(task, field_defs, "module")
    return values[0] if values else "未识别"


def infer_iteration_label(task: dict[str, Any], sprint_name_by_id: dict[str, str], field_defs: dict[str, dict[str, Any]]) -> str:
    if task.get("sprintId") and sprint_name_by_id.get(task["sprintId"]):
        return sprint_name_by_id[task["sprintId"]]
    for purpose in ("test_plan", "test_round"):
        values = extract_field_value(task, field_defs, purpose)
        if values:
            return values[0]
    return "未识别"


def infer_cause_category(task: dict[str, Any], field_defs: dict[str, dict[str, Any]]) -> tuple[str, str]:
    values = extract_field_value(task, field_defs, "cause_category")
    if values:
        return values[0], "structured"

    note = str(task.get("note") or "")
    content = str(task.get("content") or "")
    combined = f"{content} {note}".lower()
    for label, keywords in INFERRED_CAUSE_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            return label, "inferred"
    return "未识别", "inferred"


def infer_cause_text(task: dict[str, Any], field_defs: dict[str, dict[str, Any]]) -> tuple[list[str], str]:
    values = extract_field_value(task, field_defs, "cause_text")
    if values:
        return values, "structured"
    candidates = []
    content = str(task.get("content") or "").strip()
    note = re.sub(r"\\\[[^]]+\\\]", " ", str(task.get("note") or "")).strip()
    if content:
        candidates.append(content)
    if note:
        candidates.append(note[:120])
    return candidates[:2], "inferred"


def collect_task_views(
    tasks: list[dict[str, Any]],
    field_defs: dict[str, dict[str, Any]],
    status_map: dict[str, dict[str, str]],
    sprint_name_by_id: dict[str, str],
    people_by_id: dict[str, str],
) -> list[dict[str, Any]]:
    views = []
    for task in tasks:
        status = status_map.get(task.get("tfsId", ""), {})
        status_name = status.get("name") or "未识别"
        status_kind = status.get("kind") or ""
        cause_category, cause_source = infer_cause_category(task, field_defs)
        cause_texts, cause_text_source = infer_cause_text(task, field_defs)
        views.append(
            {
                "id": task.get("id"),
                "content": task.get("content") or "",
                "status_name": status_name,
                "status_bucket": classify_status(status_name, status_kind),
                "severity": infer_severity(task, field_defs),
                "environment": infer_environment(task, field_defs),
                "classification": infer_classification(task, field_defs),
                "iteration": infer_iteration_label(task, sprint_name_by_id, field_defs),
                "module": infer_module(task, field_defs),
                "cause_category": cause_category,
                "cause_source": cause_source,
                "cause_texts": cause_texts,
                "cause_text_source": cause_text_source,
                "executor": people_by_id.get(task.get("executorId"), task.get("executorId")) if task.get("executorId") else "未分配",
                "created": task.get("created"),
                "updated": task.get("updated"),
                "accomplishTime": task.get("accomplishTime"),
            }
        )
    return views


def counter_to_rows(counter: Counter[str]) -> list[tuple[str, int, str]]:
    total = sum(counter.values())
    rows = []
    for key, value in counter.most_common():
        rows.append((key, value, percent(value, total)))
    return rows


def split_cause_category(cause_category: str) -> tuple[str, str]:
    parts = [part.strip() for part in re.split(r"\s*[\\/／]\s*", cause_category or "") if part.strip()]
    if not parts:
        return "未识别", "未细分"
    if len(parts) == 1:
        return parts[0], "未细分"
    return parts[0], " / ".join(parts[1:])


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    output = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        output.append("| " + " | ".join(row) + " |")
    return "\n".join(output)


def top_cause_details(cause_detail_counter: Counter[str], limit: int = 6) -> list[tuple[str, int, str]]:
    return counter_to_rows(cause_detail_counter)[:limit]


def process_stage_label(cause_level1: str) -> str:
    mapping = {
        "编码问题": "开发实现和自测",
        "环境问题": "部署准备和环境验收",
        "需求问题": "需求澄清和验收口径确认",
        "技术设计问题": "方案评审和异常场景设计",
        "数据问题": "测试数据准备和数据校验",
        "接口联调": "联调验证",
        "权限控制": "权限方案评审和角色验证",
    }
    return mapping.get(cause_level1, "缺陷处理流程")


def build_cause_analysis_lines(summary: dict[str, Any]) -> list[str]:
    total = summary["total"]
    cause_level1_rows = counter_to_rows(summary["cause_level1_counter"])
    cause_detail_rows = counter_to_rows(summary["cause_detail_counter"])
    if not total or not cause_level1_rows:
        return ["- 未获取到可用的原因分类数据。"]

    lines = []
    top_level_desc = "、".join(f"{name} {count}个（{ratio}）" for name, count, ratio in cause_level1_rows[:3])
    lines.append(f"- 一级原因主要集中在 {top_level_desc}。")

    top_level_name, top_level_count, top_level_ratio = cause_level1_rows[0]
    lines.append(
        f"- {top_level_name} 占比最高，为 {top_level_count} 个（{top_level_ratio}），问题主要落在{process_stage_label(top_level_name)}。"
    )

    detail_lines = []
    for name, count, ratio in cause_detail_rows[:3]:
        detail_lines.append(f"{name} {count}个（{ratio}）")
    if detail_lines:
        lines.append(f"- 细分原因以 {'、'.join(detail_lines)} 为主。")

    upstream_count = summary["cause_level1_counter"].get("需求问题", 0) + summary["cause_level1_counter"].get("技术设计问题", 0)
    if upstream_count:
        lines.append(
            f"- 需求和设计类问题合计 {upstream_count} 个（{percent(upstream_count, total)}），需要把规则澄清和异常场景评审前移。"
        )

    if summary["structured_cause_count"] < total:
        lines.append(
            f"- 有 {total - summary['structured_cause_count']} 条缺陷原因来自文本归纳，归因结论需要人工复核。"
        )
    return lines


def build_optimization_lines(summary: dict[str, Any]) -> list[str]:
    cause_level1_rows = counter_to_rows(summary["cause_level1_counter"])
    if not cause_level1_rows:
        return ["- 缺少结构化原因分类，暂时无法给出稳定的优化方向。"]

    action_map = {
        "编码问题": "补边界条件、默认值、状态切换、自测回归清单；对高频问题模块补充回归用例。",
        "环境问题": "补环境基线检查、部署后验证、依赖和配置核对清单，避免发布后才暴露环境问题。",
        "需求问题": "把业务规则、验收口径、反例场景写进需求评审和测试用例，减少理解偏差。",
        "技术设计问题": "在方案评审中补异常场景、失败回退、默认值和兼容处理检查项。",
        "数据问题": "补测试数据准备和数据映射校验，提测前先跑关键数据链路核对。",
        "接口联调": "把关键接口的请求参数、返回值和失败分支纳入联调清单。",
        "权限控制": "补角色矩阵和权限边界校验，覆盖越权、缺权和默认角色场景。",
    }

    lines = []
    for name, count, ratio in cause_level1_rows[:3]:
        action = action_map.get(name, "补对应环节的检查项和回归用例，避免同类问题重复进入测试。")
        lines.append(f"- {name}（{count}个，{ratio}）：{action}")
    return lines


def summarize(task_views: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(task_views)
    status_counter = Counter(item["status_name"] for item in task_views)
    status_bucket_counter = Counter(item["status_bucket"] for item in task_views)
    severity_counter = Counter(item["severity"] for item in task_views)
    env_counter = Counter(item["environment"] for item in task_views)
    class_counter = Counter(item["classification"] for item in task_views)
    iteration_counter = Counter(item["iteration"] for item in task_views)
    module_counter = Counter(item["module"] for item in task_views)
    cause_counter = Counter(item["cause_category"] for item in task_views)
    cause_level1_counter = Counter()
    cause_detail_counter = Counter()
    for item in task_views:
        cause_level1, cause_level2 = split_cause_category(item["cause_category"])
        cause_level1_counter[cause_level1] += 1
        detail_label = cause_level1 if cause_level2 == "未细分" else f"{cause_level1} / {cause_level2}"
        cause_detail_counter[detail_label] += 1

    focus_defects = [item for item in task_views if item["severity"] in {"P0", "P1"}]
    focus_defects.sort(key=lambda item: (item["severity"], item["status_name"], item["id"]))

    high_risk_open = [item for item in focus_defects if item["status_bucket"] != "closed"]

    structured_cause_count = sum(1 for item in task_views if item["cause_source"] == "structured")
    return {
        "total": total,
        "closed": status_bucket_counter.get("closed", 0),
        "open": status_bucket_counter.get("open", 0),
        "deferred": status_bucket_counter.get("deferred", 0),
        "close_rate": percent(status_bucket_counter.get("closed", 0), total),
        "status_counter": status_counter,
        "severity_counter": severity_counter,
        "env_counter": env_counter,
        "class_counter": class_counter,
        "iteration_counter": iteration_counter,
        "module_counter": module_counter,
        "cause_counter": cause_counter,
        "cause_level1_counter": cause_level1_counter,
        "cause_detail_counter": cause_detail_counter,
        "focus_defects": focus_defects[:10],
        "high_risk_open": high_risk_open[:10],
        "structured_cause_count": structured_cause_count,
    }


def summarize_scope(iteration: str | None, start_date: str | None, end_date: str | None, basis: str) -> tuple[str, str, str]:
    if iteration and start_date and end_date:
        return f"迭代 {iteration}，日期 {start_date} 至 {end_date}", basis, "项目 + 迭代 + 日期范围"
    if iteration:
        return f"迭代 {iteration}", basis, "项目 + 迭代"
    return f"日期 {start_date} 至 {end_date}", basis, "项目 + 日期范围"


def report_time() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def render_report(
    project_name: str,
    scope_text: str,
    time_basis: str,
    task_views: list[dict[str, Any]],
    summary: dict[str, Any],
    limits: list[str],
) -> str:
    status_table = render_table(
        ["状态", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in counter_to_rows(summary["status_counter"])],
    )
    severity_table = render_table(
        ["缺陷等级", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in counter_to_rows(summary["severity_counter"])],
    )
    env_table = render_table(
        ["环境", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in counter_to_rows(summary["env_counter"])],
    )
    class_table = render_table(
        ["缺陷分类", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in counter_to_rows(summary["class_counter"])],
    )
    iteration_table = render_table(
        ["迭代", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in counter_to_rows(summary["iteration_counter"])],
    )
    module_table = render_table(
        ["模块或业务域", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in counter_to_rows(summary["module_counter"])],
    )
    cause_level1_table = render_table(
        ["一级原因分类", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in counter_to_rows(summary["cause_level1_counter"])],
    )
    cause_detail_table = render_table(
        ["一级+二级原因分类", "数量", "占比"],
        [[name, str(count), ratio] for name, count, ratio in top_cause_details(summary["cause_detail_counter"])],
    )

    high_risk_rows = []
    for item in summary["focus_defects"]:
        risk_note = "P0/P1 缺陷"
        if item["status_bucket"] != "closed":
            risk_note = "未关闭 P0/P1 缺陷"
        high_risk_rows.append(
            [
                item["content"],
                item["id"] or "",
                item["iteration"],
                item["status_name"],
                item["severity"],
                item["environment"],
                item["executor"],
                risk_note,
            ]
        )
    if not high_risk_rows:
        high_risk_rows.append(["未发现", "", "", "", "", "", "", ""])
    high_risk_table = render_table(
        ["缺陷标题", "编号", "所属迭代", "状态", "缺陷等级", "环境", "责任人", "风险说明"],
        high_risk_rows,
    )
    top_level_causes = [name for name, _, _ in counter_to_rows(summary["cause_level1_counter"])[:3]]
    cause_analysis_lines = build_cause_analysis_lines(summary)
    optimization_lines = build_optimization_lines(summary)
    current_risks = []
    if summary["high_risk_open"]:
        current_risks.append(f"存在 {len(summary['high_risk_open'])} 个高风险未关闭缺陷")
    if summary["deferred"]:
        current_risks.append(f"存在 {summary['deferred']} 个延期缺陷")
    if not current_risks:
        current_risks.append("当前未发现高风险未关闭缺陷")

    limits_text = "\n".join(f"- {item}" for item in limits) if limits else "- 未发现明显数据局限"

    return f"""# {project_name}_缺陷分析报告

## 1. 报告信息
- 项目名称：{project_name}
- 分析范围：{scope_text}
- 时间基准：{time_basis}
- 数据来源：Teambition OpenAPI
- 报告时间：{report_time()}

## 2. 分析范围说明
- 纳入范围：已识别为“缺陷”任务类型的项目任务
- 排除范围：归档任务、非缺陷任务类型、无法匹配时间基准的记录
- 数据口径说明：关闭率按当前分析范围内缺陷计算

## 3. 缺陷总体概况
- 缺陷总数：{summary['total']}
- 已关闭：{summary['closed']}
- 未关闭：{summary['open']}
- 延期：{summary['deferred']}
- 关闭率：{summary['close_rate']}
- 高风险未关闭缺陷数：{len(summary['high_risk_open'])}
- 当前主要风险：{'；'.join(current_risks)}

## 4. 缺陷分布分析
### 4.1 按状态分布
{status_table}

### 4.2 按缺陷等级分布
{severity_table}

### 4.3 按环境分布
{env_table}

### 4.4 按缺陷分类分布
{class_table}

### 4.5 按迭代分布
{iteration_table}

### 4.6 按模块或业务域分布
{module_table}

## 5. 重点缺陷分析
{high_risk_table}

## 6. 缺陷原因分析
### 6.1 一级原因分类占比
{cause_level1_table}

### 6.2 一级+二级原因分类占比
{cause_detail_table}

### 6.3 归因分析
{chr(10).join(cause_analysis_lines)}

### 6.4 可优化方向
{chr(10).join(optimization_lines)}

## 7. 风险评估
- 当前遗留风险：{'；'.join(current_risks)}
- 发布风险：{'高' if summary['high_risk_open'] else '中'}
- 回归风险：{'高' if summary['open'] > 0 else '中'}
- 环境或数据风险：{summary['env_counter'].most_common(1)[0][0] if summary['env_counter'] else '未识别'}

## 8. 结论摘要
- 主要结论：本次范围内共识别 {summary['total']} 个缺陷，一级原因主要集中在 {'、'.join(top_level_causes) if top_level_causes else '未识别'}
- 是否建议进入下一阶段：{'否，存在高风险未关闭缺陷' if summary['high_risk_open'] else '需结合测试结论人工确认'}
- 需重点跟踪事项：{'；'.join(current_risks)}

## 9. 数据局限
{limits_text}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Teambition defect analysis report")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--iteration", help="迭代名称")
    parser.add_argument("--start-date", help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--date-basis", default="created", choices=sorted(DATE_BASE_FIELDS), help="日期过滤字段")
    parser.add_argument("--output", help="输出文件路径")
    args = parser.parse_args()

    if not args.iteration and not (args.start_date and args.end_date):
        raise SystemExit("必须提供 --iteration 或同时提供 --start-date 和 --end-date")
    if (args.start_date and not args.end_date) or (args.end_date and not args.start_date):
        raise SystemExit("--start-date 和 --end-date 必须同时提供")

    auth = require_auth()
    mapping = load_mapping()
    client = TBClient(auth)

    project = resolve_project(args.project, mapping, client)
    project_id = project["project_id"]
    bug_scenario = get_bug_scenario(project_id, client)
    field_defs = get_customfield_defs(project_id, client)
    status_map = get_status_map(project_id, bug_scenario.get("taskflowId"), client)
    sprint = choose_sprint(project_id, args.iteration, client) if args.iteration else None
    all_sprints = client.paginate(f"/v3/project/{project_id}/sprint/search")
    sprint_name_by_id = {item["id"]: item.get("name", "") for item in all_sprints if item.get("id")}
    tasks = get_bug_tasks(project_id, bug_scenario["id"], client)
    tasks = filter_by_date(tasks, args.start_date, args.end_date, args.date_basis)
    tasks = filter_by_iteration(tasks, args.iteration, sprint, field_defs)

    people_by_id = mapping.get("people_by_id", {})
    task_views = collect_task_views(tasks, field_defs, status_map, sprint_name_by_id, people_by_id)
    summary = summarize(task_views)

    scope_text, time_basis, _ = summarize_scope(args.iteration, args.start_date, args.end_date, args.date_basis)
    limits = []
    if not args.iteration and not (args.start_date and args.end_date):
        limits.append("未指定迭代或日期范围")
    if summary["structured_cause_count"] == 0:
        limits.append("缺少结构化原因分类字段，已退回到文本语义归纳")
    if sprint is None and args.iteration:
        limits.append(f"未匹配到原生 sprint，迭代过滤已退回到测试计划或测试轮次字段：{args.iteration}")

    report = render_report(args.project, scope_text, time_basis, task_views, summary, limits)
    range_slug = args.iteration or f"{args.start_date}_{args.end_date}"
    output = Path(args.output) if args.output else Path.cwd() / "outputs" / "defect-analysis" / f"{args.project}_{range_slug}_缺陷分析报告.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "project": args.project,
                "projectId": project_id,
                "iteration": args.iteration,
                "sprintId": sprint.get("id") if sprint else None,
                "dateBasis": args.date_basis,
                "startDate": args.start_date,
                "endDate": args.end_date,
                "bugScenarioId": bug_scenario["id"],
                "bugScenarioName": bug_scenario.get("name"),
                "output": str(output),
                "summary": {
                    "total": summary["total"],
                    "closed": summary["closed"],
                    "open": summary["open"],
                    "deferred": summary["deferred"],
                    "closeRate": summary["close_rate"],
                    "highRiskOpen": len(summary["high_risk_open"]),
                },
                "limits": limits,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
