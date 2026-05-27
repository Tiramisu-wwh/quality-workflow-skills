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


def normalize(text: str) -> str:
    return re.sub(r"[\s（）()_\-]+", "", text or "").lower()


def extract_match_tokens(text: str) -> set[str]:
    source = (text or "").lower()
    tokens = set(re.findall(r"v\d+(?:\.\d+)+", source))
    for keyword in ("uat", "sit", "prod", "fat", "测试", "发布"):
        if keyword in source:
            tokens.add(keyword)
    return tokens


def load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        data[key.strip()] = value
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
        raise SystemExit(f"缺少映射文件: {MAPPING_JSON}。先运行 scripts/build_teambition_mapping.py")
    return json.loads(MAPPING_JSON.read_text(encoding="utf-8"))


class TBApiError(RuntimeError):
    def __init__(self, path: str, payload: dict[str, Any]) -> None:
        self.path = path
        self.payload = payload
        code = payload.get("code")
        error_code = payload.get("errorCode") or ""
        message = payload.get("errorMessage") or "未知错误"
        required_scopes = ((payload.get("accessDeniedDetail") or {}).get("requiredScopes")) or []
        detail = f"{path} 返回错误 code={code}, errorCode={error_code}, errorMessage={message}"
        if required_scopes:
            detail += f", requiredScopes={','.join(required_scopes)}"
        super().__init__(detail)


class TBClient:
    def __init__(self, auth: dict[str, str]) -> None:
        self.auth = auth
        self.token = self.get_app_token()

    def get_app_token(self) -> str:
        payload = {
            "appId": self.auth["TEAMBITION_APP_ID"],
            "appSecret": self.auth["TEAMBITION_APP_SECRET"],
        }
        resp = requests.post(f"{BASE_URL}/appToken", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("appToken")
        if not token:
            raise RuntimeError(f"获取 appToken 失败: {data}")
        return token

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
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
        params = dict(params or {})
        params.setdefault("pageSize", 1000)
        page_token = ""
        items: list[dict[str, Any]] = []
        while True:
            if page_token:
                params["pageToken"] = page_token
            data = self.get(path, params=params)
            items.extend(data.get(result_key) or [])
            page_token = data.get("nextPageToken") or ""
            if not page_token:
                break
        return items


def resolve_project(project_name: str, mapping: dict[str, Any], client: TBClient) -> dict[str, Any]:
    projects = mapping["projects"]
    if project_name in projects and projects[project_name].get("project_id"):
        return projects[project_name]

    normalized = normalize(project_name)
    for data in projects.values():
        if data.get("normalized_name") == normalized and data.get("project_id"):
            return data

    data = client.paginate(
        "/v3/project/query",
        params={
            "name": project_name,
            "visible": "organization",
            "includeTemplate": "false",
        },
    )
    exact = [item for item in data if item.get("name") == project_name]
    candidates = exact or data
    if not candidates:
        raise SystemExit(f"未找到项目: {project_name}")
    candidates.sort(key=lambda item: item.get("updated") or "", reverse=True)
    return {
        "name": candidates[0]["name"],
        "normalized_name": normalize(candidates[0]["name"]),
        "project_id": candidates[0]["id"],
        "tasklists": [],
        "stages": [],
        "sfc": [],
        "tfs": [],
    }


def choose_sprint(project_id: str, iteration_name: str, client: TBClient) -> dict[str, Any]:
    sprints = client.paginate(
        f"/v3/project/{project_id}/sprint/search",
        params={"q": iteration_name},
    )
    if not sprints:
        sprints = client.paginate(f"/v3/project/{project_id}/sprint/search")
    if not sprints:
        raise SystemExit(f"项目 {project_id} 下没有迭代")

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
    names = ", ".join(item.get("name", "") for item in sprints[:10])
    raise SystemExit(f"未匹配到迭代: {iteration_name}。可选示例: {names}")


def choose_testplan(project_id: str, sprint: dict[str, Any], iteration_name: str, client: TBClient) -> dict[str, Any] | None:
    plans = client.get(f"/v3/project/{project_id}/testplan").get("result") or []
    if not plans:
        return None

    normalized = normalize(iteration_name)
    exact = [item for item in plans if item.get("name") == iteration_name]
    if exact:
        return exact[0]
    normalized_hits = [item for item in plans if normalize(item.get("name", "")) == normalized]
    if normalized_hits:
        return normalized_hits[0]

    iteration_tokens = extract_match_tokens(iteration_name)
    token_scored = []
    for item in plans:
        plan_tokens = extract_match_tokens(item.get("name", ""))
        score = len(iteration_tokens & plan_tokens)
        if score > 0:
            token_scored.append((score, item.get("updated") or "", item))
    if token_scored:
        token_scored.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        return token_scored[0][2]

    sprint_start = sprint.get("startDate")
    sprint_due = sprint.get("dueDate")
    overlap = []
    for item in plans:
        plan_start = item.get("startDate")
        plan_due = item.get("dueDate")
        if sprint_start and sprint_due and plan_start and plan_due:
            if plan_start <= sprint_due and plan_due >= sprint_start:
                overlap.append(item)
    if overlap:
        overlap.sort(key=lambda item: item.get("updated") or "", reverse=True)
        return overlap[0]

    fuzzy = [item for item in plans if normalized in normalize(item.get("name", ""))]
    if fuzzy:
        fuzzy.sort(key=lambda item: item.get("updated") or "", reverse=True)
        return fuzzy[0]
    return None


def map_statuses(project_id: str, client: TBClient) -> dict[str, str]:
    statuses = client.paginate(f"/v3/project/{project_id}/taskflowstatus/search")
    return {item["id"]: item.get("name", "") for item in statuses if item.get("id")}


def map_status_kinds(project_id: str, client: TBClient) -> dict[str, str]:
    statuses = client.paginate(f"/v3/project/{project_id}/taskflowstatus/search")
    return {item["id"]: item.get("kind", "") for item in statuses if item.get("id")}


def get_testcases(project_id: str, testplan_id: str, client: TBClient) -> list[dict[str, Any]]:
    return client.paginate(
        f"/v3/project/{project_id}/testcase/query",
        params={"testplanId": testplan_id},
    )


def classify_case_status(name: str) -> str:
    low = (name or "").lower()
    if "通过" in name or "pass" in low:
        return "pass"
    if "失败" in name or "fail" in low:
        return "fail"
    if "阻塞" in name or "block" in low:
        return "block"
    if "不适用" in name or low in {"na", "n/a"} or "n/a" in low:
        return "na"
    if "未执行" in name or "待执行" in name or "未开始" in name or "todo" in low:
        return "todo"
    return "other"


def summarize_testcases(testcases: list[dict[str, Any]], status_map: dict[str, str], people_by_id: dict[str, str]) -> dict[str, Any]:
    total = len([case for case in testcases if not case.get("isDeleted")])
    executed = 0
    grouped = Counter()
    raw_status = Counter()
    members = set()
    created_times = []
    finished_times = []

    for case in testcases:
        if case.get("isDeleted"):
            continue
        status_name = status_map.get(case.get("flowstatusId", ""), "")
        bucket = classify_case_status(status_name)
        raw_status[status_name or "未映射状态"] += 1
        if bucket != "todo" and (case.get("isDone") or case.get("accomplished") or bucket in {"pass", "fail", "block", "na", "other"}):
            executed += 1
        grouped[bucket] += 1
        for field in ("executorId", "creatorId"):
            if case.get(field):
                members.add(case[field])
        for member in case.get("involveMembers") or []:
            members.add(member)
        if case.get("created"):
            created_times.append(case["created"])
        if case.get("accomplished"):
            finished_times.append(case["accomplished"])
        elif case.get("updated"):
            finished_times.append(case["updated"])

    member_names = [people_by_id.get(mid, mid) for mid in sorted(members)]
    return {
        "total": total,
        "executed": executed,
        "passed": grouped["pass"],
        "failed": grouped["fail"],
        "blocked": grouped["block"],
        "not_applicable": grouped["na"],
        "other_status": grouped["other"],
        "raw_status_counter": dict(raw_status),
        "member_names": member_names,
        "earliest_created": min(created_times) if created_times else None,
        "latest_finished": max(finished_times) if finished_times else None,
    }


def identify_defect_sfc_ids(
    project_mapping: dict[str, Any],
    tasks: list[dict[str, Any]],
    status_map: dict[str, str],
) -> set[str]:
    mapped = {
        item["id"]
        for item in project_mapping.get("sfc", [])
        if "缺陷" in item.get("name", "") or "bug" in item.get("name", "").lower()
    }
    if mapped:
        return mapped

    title_matched = set()
    for task in tasks:
        title = task.get("content", "")
        if "缺陷" in title or "bug" in title.lower():
            if task.get("sfcId"):
                title_matched.add(task["sfcId"])
    if title_matched:
        return title_matched

    # Some project maps do not preserve the real SFC name for defect cards.
    # In that case, defect items can still be distinguished by bug-specific workflow statuses.
    bug_flow_keywords = ("修复中", "待验证", "重新打开", "无法复现", "设计如此", "关闭")
    workflow_matched = {
        task["sfcId"]
        for task in tasks
        if task.get("sfcId")
        and not task.get("parentTaskId")
        and any(keyword in status_map.get(task.get("tfsId", ""), "") for keyword in bug_flow_keywords)
    }
    if workflow_matched:
        return workflow_matched

    non_defect_ids = {
        item["id"]
        for item in project_mapping.get("sfc", [])
        if any(keyword in item.get("name", "").lower() for keyword in ("milestone", "项目任务", "需求", "story"))
    }
    inferred = {
        task["sfcId"]
        for task in tasks
        if task.get("sfcId")
        and not task.get("parentTaskId")
        and task["sfcId"] not in non_defect_ids
        and not str(task.get("content", "")).startswith("【")
    }
    if inferred:
        return inferred

    unidentified = {item["id"] for item in project_mapping.get("sfc", []) if item.get("name") == "未识别名称"}
    return unidentified


def classify_defect_status(name: str, kind: str = "") -> str:
    if kind == "end":
        return "closed"
    low = (name or "").lower()
    if "延期" in name or "后续迭代" in name or "暂不处理" in name:
        return "deferred"
    if "关闭" in name or "已解决" in name or low == "done":
        return "closed"
    return "open"


def severity_label_from_customfields(customfields: list[dict[str, Any]] | None) -> str | None:
    severity_map = {
        "P0": "P0",
        "P1": "P1",
        "P2": "P2",
        "P3": "P3",
        "P4": "P3",
        "P5": "P3",
    }
    for field in customfields or []:
        for value in field.get("value") or []:
            label = str(value.get("title") or "").strip().upper()
            if label in severity_map:
                return severity_map[label]
    return None


def severity_label(priority: Any) -> str:
    if priority is None:
        return "P3"
    try:
        value = int(priority)
    except Exception:
        return "P3"
    # This project stores bug priority as a descending numeric level:
    # 2 -> P0, 1 -> P1, 0 -> P2, negative values -> P3.
    if value >= 2:
        return "P0"
    if value == 1:
        return "P1"
    if value == 0:
        return "P2"
    return "P3"


def get_sprint_tasks(project_id: str, sprint_id: str, client: TBClient) -> list[dict[str, Any]]:
    return client.paginate(
        f"/v3/project/{project_id}/task/query",
        params={
            "q": f'sprintId = "{sprint_id}"',
            "includeArchived": "false",
            "pageSize": 100,
        },
    )


def summarize_defects(
    tasks: list[dict[str, Any]],
    defect_sfc_ids: set[str],
    status_map: dict[str, str],
    status_kind_map: dict[str, str],
) -> dict[str, Any]:
    defects = [
        task for task in tasks
        if task.get("sfcId") in defect_sfc_ids and not task.get("parentTaskId")
    ]
    severity = {
        level: {"closed": 0, "open": 0, "deferred": 0}
        for level in ("P0", "P1", "P2", "P3")
    }
    raw_status = Counter()
    high_open = []

    for task in defects:
        level = severity_label_from_customfields(task.get("customfields")) or severity_label(task.get("priority"))
        status_id = task.get("tfsId", "")
        status_name = status_map.get(status_id, "")
        status_kind = status_kind_map.get(status_id, "")
        bucket = classify_defect_status(status_name, status_kind)
        severity[level][bucket] += 1
        raw_status[status_name or "未映射状态"] += 1
        if bucket == "open" and level in {"P0", "P1"}:
            high_open.append(task)

    total = len(defects)
    closed = sum(item["closed"] for item in severity.values())
    deferred = sum(item["deferred"] for item in severity.values())
    return {
        "total": total,
        "effective_total": total,
        "closed_total": closed,
        "deferred_total": deferred,
        "fix_rate": round((closed / total) * 100, 2) if total else 0.0,
        "severity": severity,
        "raw_status_counter": dict(raw_status),
        "high_open": high_open,
    }


def fmt_date(value: str | None) -> str:
    if not value:
        return "未获取到"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return value


def percent(numerator: int, denominator: int) -> str:
    if not denominator:
        return "0.00"
    return f"{(numerator / denominator) * 100:.2f}"


def choose_period(testplan: dict[str, Any] | None, sprint: dict[str, Any], case_summary: dict[str, Any]) -> tuple[str, str]:
    start = None
    end = None
    if testplan:
        start = testplan.get("startDate") or start
        end = testplan.get("dueDate") or end
    start = start or sprint.get("startDate") or case_summary.get("earliest_created")
    end = end or sprint.get("dueDate") or case_summary.get("latest_finished")
    return fmt_date(start), fmt_date(end)


def render_report(
    project_name: str,
    sprint: dict[str, Any],
    testplan: dict[str, Any] | None,
    case_summary: dict[str, Any] | None,
    defect_summary: dict[str, Any],
    case_error: str | None = None,
) -> str:
    start_date, end_date = choose_period(testplan, sprint, case_summary or {})
    version = sprint.get("name") or "需人工确认"
    members = "、".join((case_summary or {}).get("member_names", [])) or "需人工补充"
    execution_rate = percent((case_summary or {}).get("executed", 0), (case_summary or {}).get("total", 0))
    pass_rate = percent((case_summary or {}).get("passed", 0), (case_summary or {}).get("executed", 0))
    severity = defect_summary["severity"]
    high_risk_lines = []
    for task in defect_summary["high_open"][:10]:
        high_risk_lines.append(f"- {task.get('content', '')}（{task.get('id', '')}）")
    if not high_risk_lines:
        high_risk_lines.append("- 未发现高优先级未关闭缺陷")
    if case_error:
        high_risk_lines.append(f"- 测试用例执行数据未拉取成功：{case_error}")
    elif not testplan:
        high_risk_lines.append("- 未获取到匹配测试计划，测试用例执行统计需人工补充")

    if defect_summary["high_open"]:
        conclusion = "□ 不建议发布，需修复后复测项：存在高优先级未关闭缺陷。"
    elif case_error or not testplan:
        conclusion = "□ 测试计划或测试用例执行数据不完整，需人工补充后再判断是否发布。"
    elif (case_summary or {}).get("failed", 0) > 0 or (case_summary or {}).get("blocked", 0) > 0:
        conclusion = "□ 存在未关闭缺陷或风险，有条件发布（条件：失败或阻塞用例需补充说明与处置结果）。"
    else:
        conclusion = "□ 当前版本满足 Must 项与约定性能/安全要求，建议发布。"

    testcase_summary_line = "测试计划下用例执行统计已完成汇总。"
    if case_error:
        testcase_summary_line = f"测试用例执行数据未拉取成功，原因：{case_error}"
    elif not testplan:
        testcase_summary_line = "未获取到匹配测试计划，测试用例执行统计需人工补充。"

    case_total = str((case_summary or {}).get("total", 0))
    case_executed = str((case_summary or {}).get("executed", 0))
    case_passed = str((case_summary or {}).get("passed", 0))
    case_failed = str((case_summary or {}).get("failed", 0))
    case_blocked = str((case_summary or {}).get("blocked", 0))
    case_na = str((case_summary or {}).get("not_applicable", 0))
    case_summary_text = f"本次功能测试执行率{execution_rate}%，通过率{pass_rate}%"
    if case_error or not testplan:
        case_total = "未获取"
        case_executed = "未获取"
        case_passed = "未获取"
        case_failed = "未获取"
        case_blocked = "未获取"
        case_na = "未获取"
        case_summary_text = "测试用例执行数据未拉取成功，未统计执行率和通过率。"

    return f"""# {project_name}_{version}_测试报告

# 引言

## 系统介绍

需人工补充

## 参考文档

| 文档名称 | 版本/日期 |
| --- | --- |
| 需人工补充 |  |
|  |  |

## 基本信息

| **项目名称** | {project_name} |
| --- | --- |
| **项目测试周期** | {start_date}-{end_date} |
| **项目测试投入工作量（人日）** | 需人工补充 |
| **项目开发组成员** | 需人工补充 |
| **项目测试成员** | {members} |

# 测试概要

## 测试环境

服务器

|  | **描述** | **数据库、应用服务器** |
| --- | --- | --- |
| **硬件环境** | CPU、内存、硬盘 | 需人工补充 |
| **软件环境** | 操作系统、中间件、数据库等 | 需人工补充 |

测试机

|  | **描述** | **测试机** |
| --- | --- | --- |
| **硬件环境** | CPU、内存、硬盘 | 需人工补充 |
| **软件环境** | 操作系统，IE | 需人工补充 |

网络及数据

| **网络环境** | 需人工补充 |
| --- | --- |
| **数据环境** | 需人工补充 |

# 功能测试

## 测试说明

| **版本** | **开始日期** | **结束日期** | **测试类型** |
| --- | --- | --- | --- |
| {version} | {start_date} | {end_date} | 功能测试 |

## 通过准则

1. Must 用例通过率 100%，或仅剩已批准的遗留缺陷且风险可接受；
2. 阻塞类缺陷（Blocker）为 0；
3. 性能指标在约定数据集规模下满足对应要求；
4. 安全/保密检查项无未关闭的高风险项。

## 功能缺陷汇总及分析

1. 缺陷汇总

| **严重程度** | **已关闭** | **打开** | **延期** |
| --- | --- | --- | --- |
| P0 | {severity['P0']['closed']} | {severity['P0']['open']} | {severity['P0']['deferred']} |
| P1 | {severity['P1']['closed']} | {severity['P1']['open']} | {severity['P1']['deferred']} |
| P2 | {severity['P2']['closed']} | {severity['P2']['open']} | {severity['P2']['deferred']} |
| P3 | {severity['P3']['closed']} | {severity['P3']['open']} | {severity['P3']['deferred']} |

共发现缺陷{defect_summary['total']}个，其中有效问题{defect_summary['effective_total']}个，截止到{end_date}最终发布/UAT，延期处理问题{defect_summary['deferred_total']}个，缺陷修复率为{defect_summary['fix_rate']:.2f}%，统计口径为当前迭代顶层缺陷。

2. 功能测试分析

| **统计项** | **数量** |
| --- | --- |
| 用例总数 | {case_total} |
| 已执行 | {case_executed} |
| 通过 | {case_passed} |
| 失败 | {case_failed} |
| 阻塞（无法执行） | {case_blocked} |
| 不适用 | {case_na} |

总结：{case_summary_text}

备注：{case_error or ('未获取到匹配测试计划' if not testplan else '测试计划执行数据已按接口统计')}

3. 风险分析

{chr(10).join(high_risk_lines)}

## 测试结论

本次产品测试分别从界面易用性、功能、文档 3 个方面开展：

1. 易用性、功能性方面，缺陷处理情况详见上文缺陷汇总。
2. 用例文档方面，{testcase_summary_line}
3. 本次测试仅在以上所列举的测试环境开展，后续版本测试中将加大测试环境覆盖力度。

**结论（择一或组合说明）：**

* {conclusion}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Teambition test report")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--iteration", required=True, help="迭代名称")
    parser.add_argument("--output", help="输出文件路径")
    args = parser.parse_args()

    auth = require_auth()
    mapping = load_mapping()
    client = TBClient(auth)

    project_mapping = resolve_project(args.project, mapping, client)
    project_id = project_mapping["project_id"]
    if not project_id:
        raise SystemExit(f"项目 {args.project} 缺少 projectId 映射")

    sprint = choose_sprint(project_id, args.iteration, client)
    status_map = map_statuses(project_id, client)
    status_kind_map = map_status_kinds(project_id, client)
    testplan = choose_testplan(project_id, sprint, args.iteration, client)

    case_summary = None
    case_error = None
    if testplan:
        try:
            testcases = get_testcases(project_id, testplan["id"], client)
            case_summary = summarize_testcases(testcases, status_map, mapping.get("people_by_id", {}))
        except TBApiError as exc:
            case_error = str(exc)

    tasks = get_sprint_tasks(project_id, sprint["id"], client)
    defect_sfc_ids = identify_defect_sfc_ids(project_mapping, tasks, status_map)
    defect_summary = summarize_defects(tasks, defect_sfc_ids, status_map, status_kind_map)

    report = render_report(args.project, sprint, testplan, case_summary, defect_summary, case_error=case_error)

    output = Path(args.output) if args.output else Path.cwd() / "outputs" / "test-reports" / f"{args.project}_{args.iteration}_测试报告.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")

    summary = {
        "project": args.project,
        "projectId": project_id,
        "iteration": sprint.get("name"),
        "sprintId": sprint.get("id"),
        "testplan": testplan.get("name") if testplan else None,
        "testplanId": testplan.get("id") if testplan else None,
        "output": str(output),
        "caseSummary": case_summary,
        "caseError": case_error,
        "defectSummary": defect_summary,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
