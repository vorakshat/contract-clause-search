import pytest

from clausesearch import evaluate as ev
from clausesearch import prepare, report
from clausesearch.config import load_config


def test_bootstrap_ci_brackets_the_mean():
    mean, low, high = report.bootstrap_ci([0.0, 1.0] * 50)
    assert mean == 0.5 and low < 0.5 < high
    assert report.bootstrap_ci([0.3, 0.3, 0.3]) == pytest.approx((0.3, 0.3, 0.3))


def test_compare_and_errors_render_from_saved_runs(tiny_project, tmp_path):
    assert prepare.main(["--config", tiny_project["config_path"]]) == 0
    cfg = load_config(tiny_project["config_path"])
    _, _, run_dir = ev.evaluate(cfg, "all", out_dir=tmp_path, progress=False)
    table = report.compare([str(run_dir), str(run_dir)])
    assert "bootstrap" in table and "absent_clause" in table and "not_in_corpus" in table
    assert "Question:" in report.errors(str(run_dir), per_bucket=1)
