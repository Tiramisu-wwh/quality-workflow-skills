#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "assets" / "teambition-id-mapping.json"


def normalize(text: str) -> str:
    return re.sub(r"[\s（）()_\-]+", "", text or "").lower()


def parse_people(lines: list[str], start: int) -> tuple[dict, int]:
    people: dict[str, list[str]] = {}
    i = start
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("## 项目级对照"):
            break
        if line.startswith("- "):
            m = re.match(r"-\s+(.+?):\s+(.+)", line)
            if m:
                name = m.group(1).strip()
                ids = re.findall(r"`([^`]+)`", m.group(2))
                if ids:
                    people[name] = ids
        i += 1
    return people, i


def parse_projects(lines: list[str], start: int) -> dict:
    projects: dict[str, dict] = {}
    i = start
    current: dict | None = None
    current_block: str | None = None

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("### "):
            name = line[4:].strip()
            current = {
                "name": name,
                "normalized_name": normalize(name),
                "project_id": None,
                "tasklists": [],
                "stages": [],
                "sfc": [],
                "tfs": [],
            }
            projects[name] = current
            current_block = None
            i += 1
            continue

        if current is None:
            i += 1
            continue

        stripped = line.strip()

        if stripped.startswith("- projectId:"):
            ids = re.findall(r"`([^`]+)`", stripped)
            if ids:
                current["project_id"] = ids[0]
        elif stripped.startswith("- tasklistId:"):
            current_block = "tasklist"
        elif stripped.startswith("- stageId:"):
            current_block = "stage"
        elif stripped.startswith("- sfcId:"):
            current_block = "sfc"
        elif stripped.startswith("- tfsId:"):
            current_block = "tfs"
        elif stripped.startswith("- ") and current_block == "tasklist":
            m = re.match(r"-\s+(.+?):\s+`([^`]+)`", stripped)
            if m:
                current["tasklists"].append({"name": m.group(1).strip(), "id": m.group(2).strip()})
        elif stripped.startswith("- ") and current_block == "stage":
            m = re.match(r"-\s+(.+?):\s+`([^`]+)`\s+\(tasklistId:\s+`([^`]+)`\)", stripped)
            if m:
                current["stages"].append(
                    {"name": m.group(1).strip(), "id": m.group(2).strip(), "tasklist_id": m.group(3).strip()}
                )
        elif stripped.startswith("- ") and current_block == "sfc":
            m = re.match(r"-\s+(.+?):\s+`([^`]+)`", stripped)
            if m:
                current["sfc"].append({"name": m.group(1).strip(), "id": m.group(2).strip()})
        elif stripped.startswith("- ") and current_block == "tfs":
            m = re.match(r"-\s+(.+?)\s+\[([^\]]+)\]:\s+`([^`]+)`", stripped)
            if m:
                current["tfs"].append(
                    {"name": m.group(1).strip(), "kind": m.group(2).strip(), "id": m.group(3).strip()}
                )
        i += 1
    return projects


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Teambition ID mapping JSON from a markdown source file.")
    parser.add_argument("--source", required=True, help="Markdown file containing people and project mappings")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Mapping source file not found: {source}")

    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        people_start = next(i for i, line in enumerate(lines) if line.startswith("## 人员对照")) + 1
        projects_start = next(i for i, line in enumerate(lines) if line.startswith("## 项目级对照")) + 1
    except StopIteration as exc:
        raise SystemExit(f"Could not find required sections in {source}") from exc

    people, _ = parse_people(lines, people_start)
    projects = parse_projects(lines, projects_start)

    data = {
        "generated_from": source.name,
        "projects": projects,
        "projects_by_normalized_name": {v["normalized_name"]: v["project_id"] for v in projects.values() if v["project_id"]},
        "people": people,
        "people_by_id": {user_id: name for name, ids in people.items() for user_id in ids},
    }

    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
