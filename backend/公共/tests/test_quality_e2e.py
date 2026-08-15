"""
A-05 单测：端到端验收脚本 quality_check.py。

覆盖：
  1. 纯逻辑：画像加载 / taxonomy 解析 / 难度映射 / 指标聚合 / 报告渲染 / 文本摊平
  2. 冒烟 e2e：3 组画像真实跑通协同流程（自包含模式，无外部依赖）
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.公共 import quality_check as qc
from backend.公共.errors import QualityError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REAL_PROFILES = PROJECT_ROOT / "backend" / "b_学情数据" / "test_profiles"
REAL_KB = PROJECT_ROOT / "backend" / "b_学情数据" / "kb"


# ============ 纯逻辑：画像加载 ============

class TestLoadProfiles:
    def test_load_real_profiles(self):
        """真实 B-07 画像目录：>= 3 组且带 _source_file。"""
        profiles = qc.load_profiles(REAL_PROFILES)
        assert len(profiles) >= 3
        for p in profiles:
            assert "profile_id" in p and "learnerProfile" in p
            assert p["_source_file"].startswith("profile_")

    def test_missing_dir_raises(self, tmp_path):
        with pytest.raises(QualityError):
            qc.load_profiles(tmp_path / "not_exist")

    def test_too_few_profiles_raises(self, tmp_path):
        for i in (1, 2):
            (tmp_path / f"profile_0{i}.json").write_text(
                json.dumps({"profile_id": f"p-00{i}", "learnerProfile": {}}),
                encoding="utf-8",
            )
        with pytest.raises(QualityError, match="B-07"):
            qc.load_profiles(tmp_path)

    def test_expected_outputs_not_loaded(self, tmp_path):
        """expected_outputs 子目录里的 JSON 不能被当作画像。"""
        for i in (1, 2, 3):
            (tmp_path / f"profile_0{i}.json").write_text(
                json.dumps({"profile_id": f"p-00{i}"}), encoding="utf-8"
            )
        eo = tmp_path / "expected_outputs"
        eo.mkdir()
        (eo / "profile_99_extra.json").write_text("{}", encoding="utf-8")
        assert len(qc.load_profiles(tmp_path)) == 3

    def test_invalid_json_raises(self, tmp_path):
        for i in (1, 2, 3):
            (tmp_path / f"profile_0{i}.json").write_text("{{{", encoding="utf-8")
        with pytest.raises(QualityError, match="解析失败"):
            qc.load_profiles(tmp_path)


# ============ 纯逻辑：taxonomy ============

class TestLoadTaxonomy:
    def test_load_real_taxonomy(self):
        kps = qc.load_taxonomy_kps(REAL_KB)
        # B-06 红线：叶子知识点 >= 30（实际 42）
        assert len(kps) >= 30
        assert "kp_root" not in kps
        assert not any(k.startswith("kp_module") for k in kps)
        assert len(kps) == len(set(kps))  # 无重复

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(QualityError):
            qc.load_taxonomy_kps(tmp_path)


# ============ 纯逻辑：难度映射 ============

class TestExpectedDifficulty:
    """与 B 区 diagnosis_agent 规则一致：>=80→5，60-79→3，<60→2，None→3。"""

    @pytest.mark.parametrize("score,expected", [
        (None, 3), (0, 2), (55, 2), (59, 2),
        (60, 3), (79, 3),
        (80, 5), (82, 5), (100, 5),
    ])
    def test_mapping(self, score, expected):
        assert qc.expected_difficulty_from_score(score) == expected


# ============ 纯逻辑：指标聚合 ============

def _detail(halluc: float = 0.0, match: float = 1.0) -> dict:
    return {"hallucination_rate": halluc, "match_accuracy": match}


class TestAggregateMetrics:
    def test_all_pass(self):
        m = qc.aggregate_metrics([_detail(), _detail(), _detail()])
        assert m["hallucination_rate"] == 0.0
        assert m["match_accuracy"] == 1.0
        assert m["hallucination_pass"] and m["match_accuracy_pass"]

    def test_hallucination_fail(self):
        m = qc.aggregate_metrics([_detail(0.2), _detail(), _detail()])
        assert not m["hallucination_pass"]  # 0.2/3 ≈ 6.7% > 5%
        assert abs(m["hallucination_rate"] - 0.2 / 3) < 1e-3

    def test_accuracy_fail_boundary(self):
        # 2/3 ≈ 66.7% < 85% → 不达标；3/3 = 100% 达标
        m = qc.aggregate_metrics([_detail(), _detail(match=0.0), _detail()])
        assert not m["match_accuracy_pass"]
        assert qc.aggregate_metrics([_detail()] * 3)["match_accuracy_pass"]

    def test_empty_raises(self):
        with pytest.raises(QualityError):
            qc.aggregate_metrics([])


# ============ 纯逻辑：文本摊平（口径与 C 区一致）============

class TestFlattenText:
    def test_extracts_natural_language_only(self):
        structured = {
            "title": "坐标系变换精讲",
            "kp_tags": ["kp12d", "kp_default"],
            "sections": [
                {"heading": "齐次变换矩阵", "body": "齐次矩阵描述平移与旋转。", "kp": "kp12"},
            ],
        }
        text = qc._flatten_text(structured)
        assert "坐标系变换精讲" in text
        assert "齐次矩阵描述平移与旋转。" in text
        assert "kp_default" not in text
        assert "kp12d" not in text

    def test_empty(self):
        assert qc._flatten_text({}) == ""
        assert qc._flatten_text({"kp_ids": ["kp01"]}) == ""


# ============ 纯逻辑：报告渲染 + 落盘 ============

def _fake_report() -> dict:
    details = [{
        "profile_id": "p-001", "label": "本科应届生", "elapsed_sec": 1.2,
        "resource_difficulty": 5, "expected_difficulty": 5,
        "match_accuracy": 1.0, "hallucination_rate": 0.04,
        "resource_vs_weak_coverage": 1.0, "audit_verdict": "pass",
    }]
    metrics = qc.aggregate_metrics(details)
    metrics.update(coverage=0.95, coverage_pass=True, passed=True)
    return {
        "generated_at": "2026-08-15 00:00:00", "mode": "self-contained",
        "profiles_dir": "x", "kb_dir": "y",
        "kb_taxonomy_total": 42, "kb_covered_kp_count": 40,
        "metrics": metrics, "details": details, "passed": True, "warnings": [],
    }


class TestReport:
    def test_render_contains_key_sections(self):
        md = qc.render_markdown_report(_fake_report())
        assert "# 质量报告" in md
        assert "幻觉率" in md and "4.00%" in md
        assert "画像-难度适配准确率" in md and "100.00%" in md
        assert "核心知识点覆盖率" in md and "95.00%" in md
        assert "全部达标" in md
        assert "算法说明" in md

    def test_render_failed_report(self):
        report = _fake_report()
        report["passed"] = False
        report["metrics"]["hallucination_pass"] = False
        md = qc.render_markdown_report(report)
        assert "未达标" in md

    def test_write_reports_creates_three_files(self, tmp_path):
        report = _fake_report()
        md, js, latest = qc.write_reports(tmp_path, report)
        assert md.exists() and js.exists() and latest.exists()
        assert md.name.startswith("quality_report_") and md.suffix == ".md"
        # latest.json 内容与归档 JSON 一致
        assert json.loads(latest.read_text(encoding="utf-8"))["passed"] is True


# ============ 冒烟 e2e：3 组画像真实协同流程 ============

@pytest.mark.asyncio
async def test_quality_check_smoke(tmp_path):
    """自包含模式一键跑通：3 项指标全部达标 + 报告落盘。

    跳过 D-06 audit 阶段（单测聚焦硬指标管线；audit 有独立单测）。
    """
    report = await qc.quality_check(
        profiles_path=REAL_PROFILES,
        kb_path=REAL_KB,
        output_dir=tmp_path,
        include_audit=False,
    )
    m = report["metrics"]
    assert report["passed"] is True
    assert 0.0 <= m["hallucination_rate"] < qc.HALLUCINATION_MAX
    assert m["match_accuracy"] >= qc.MATCH_ACCURACY_MIN
    assert m["coverage"] >= qc.COVERAGE_MIN
    assert len(report["details"]) == 3
    assert (tmp_path / "latest.json").exists()


def test_quality_check_main_exit_codes(tmp_path, capsys):
    """main()：全达标 → 0（同步用例：main 内部自己 asyncio.run）。"""
    code = qc.main([
        "--profiles", str(REAL_PROFILES),
        "--kb", str(REAL_KB),
        "--out", str(tmp_path),
        "--no-audit",
    ])
    assert code == 0
    assert "全部达标" in capsys.readouterr().out
