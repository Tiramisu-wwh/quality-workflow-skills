import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_defect_analysis_report.py"
SPEC = importlib.util.spec_from_file_location("generate_defect_analysis_report", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SummarizeFocusDefectsTest(unittest.TestCase):
    def test_focus_defects_include_closed_p1(self) -> None:
        task_views = [
            {
                "id": "BUG-1",
                "content": "closed p1 defect",
                "status_name": "关闭",
                "status_bucket": "closed",
                "severity": "P1",
                "environment": "测试环境",
                "classification": "功能",
                "iteration": "数据映射V1.0",
                "module": "未识别",
                "cause_category": "编码问题 / 业务逻辑错误",
                "cause_source": "structured",
                "cause_texts": ["业务逻辑错误"],
                "cause_text_source": "structured",
                "executor": "张三",
                "created": None,
                "updated": None,
                "accomplishTime": None,
            },
            {
                "id": "BUG-2",
                "content": "open p2 defect",
                "status_name": "修复中",
                "status_bucket": "open",
                "severity": "P2",
                "environment": "测试环境",
                "classification": "功能",
                "iteration": "数据映射V1.0",
                "module": "未识别",
                "cause_category": "编码问题 / 边界条件处理遗漏",
                "cause_source": "structured",
                "cause_texts": ["边界条件处理遗漏"],
                "cause_text_source": "structured",
                "executor": "李四",
                "created": None,
                "updated": None,
                "accomplishTime": None,
            },
        ]

        summary = MODULE.summarize(task_views)

        self.assertEqual([item["id"] for item in summary["focus_defects"]], ["BUG-1"])
        self.assertEqual(summary["high_risk_open"], [])

    def test_render_report_uses_compact_cause_analysis_sections(self) -> None:
        task_views = [
            {
                "id": "BUG-1",
                "content": "boundary issue",
                "status_name": "关闭",
                "status_bucket": "closed",
                "severity": "P1",
                "environment": "测试环境",
                "classification": "功能",
                "iteration": "数据映射V1.0",
                "module": "未识别",
                "cause_category": "编码问题 / 边界条件处理遗漏",
                "cause_source": "structured",
                "cause_texts": ["边界条件处理遗漏"],
                "cause_text_source": "structured",
                "executor": "张三",
                "created": None,
                "updated": None,
                "accomplishTime": None,
            },
            {
                "id": "BUG-2",
                "content": "env issue",
                "status_name": "关闭",
                "status_bucket": "closed",
                "severity": "P2",
                "environment": "测试环境",
                "classification": "功能",
                "iteration": "数据映射V1.0",
                "module": "未识别",
                "cause_category": "环境问题 / 部署问题",
                "cause_source": "structured",
                "cause_texts": ["部署问题"],
                "cause_text_source": "structured",
                "executor": "李四",
                "created": None,
                "updated": None,
                "accomplishTime": None,
            },
            {
                "id": "BUG-3",
                "content": "logic issue",
                "status_name": "修复中",
                "status_bucket": "open",
                "severity": "P2",
                "environment": "测试环境",
                "classification": "功能",
                "iteration": "数据映射V1.0",
                "module": "未识别",
                "cause_category": "编码问题 / 业务逻辑错误",
                "cause_source": "structured",
                "cause_texts": ["业务逻辑错误"],
                "cause_text_source": "structured",
                "executor": "王五",
                "created": None,
                "updated": None,
                "accomplishTime": None,
            },
        ]

        summary = MODULE.summarize(task_views)
        report = MODULE.render_report(
            project_name="临床数据分析平台",
            scope_text="迭代 数据映射V1.0",
            time_basis="created",
            task_views=task_views,
            summary=summary,
            limits=[],
        )

        self.assertIn("### 6.1 一级原因分类占比", report)
        self.assertIn("### 6.2 一级+二级原因分类占比", report)
        self.assertIn("### 6.3 归因分析", report)
        self.assertIn("### 6.4 可优化方向", report)
        self.assertNotIn("原因与缺陷等级分析", report)
        self.assertNotIn("原因文本归纳", report)


if __name__ == "__main__":
    unittest.main()
