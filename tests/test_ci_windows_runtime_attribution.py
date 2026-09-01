from __future__ import annotations

from types import SimpleNamespace

import scripts.ci_windows_runtime_attribution as attribution_module


def _report(nodeid: str, when: str, duration: float) -> SimpleNamespace:
    return SimpleNamespace(nodeid=nodeid, when=when, duration=duration)


def _clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(attribution_module, "perf_counter", lambda: now[0])
    return now


def test_phase_accumulation(monkeypatch):
    now = _clock(monkeypatch)
    attribution = attribution_module.RuntimeAttribution()
    attribution.pytest_sessionstart()
    nodeid = "tests/test_alpha.py::test_one"
    attribution.pytest_runtest_logstart(nodeid, ("tests/test_alpha.py", 1, "test_one"))
    attribution.pytest_runtest_logreport(_report(nodeid, "setup", 1.0))
    attribution.pytest_runtest_logreport(_report(nodeid, "call", 2.0))
    attribution.pytest_runtest_logreport(_report(nodeid, "teardown", 3.0))
    now[0] = 8.0
    attribution.pytest_sessionfinish(0)

    stats = attribution._groups["tests/test_alpha.py"]
    assert stats.setup_seconds == 1.0
    assert stats.call_seconds == 2.0
    assert stats.teardown_seconds == 3.0
    assert stats.phase_seconds == 6.0
    assert stats.wall_seconds == 8.0
    assert stats.unattributed_seconds == 2.0
    assert stats.completed == 1


def test_multiple_tests_same_module_accumulate(monkeypatch):
    now = _clock(monkeypatch)
    attribution = attribution_module.RuntimeAttribution()
    attribution.pytest_sessionstart()
    nodeid = "tests/test_alpha.py::test_one"
    attribution.pytest_runtest_logstart(nodeid, ("tests/test_alpha.py", 1, "test_one"))
    attribution.pytest_runtest_logreport(_report(nodeid, "call", 2.0))
    second = "tests/test_alpha.py::test_two"
    attribution.pytest_runtest_logstart(second, ("tests/test_alpha.py", 2, "test_two"))
    attribution.pytest_runtest_logreport(_report(second, "call", 3.0))
    now[0] = 7.0
    attribution.pytest_sessionfinish(0)

    stats = attribution._groups["tests/test_alpha.py"]
    assert stats.call_seconds == 5.0
    assert stats.completed == 2
    assert stats.wall_seconds == 7.0


def test_module_boundary_closes_previous_group_once(monkeypatch, capsys):
    now = _clock(monkeypatch)
    attribution = attribution_module.RuntimeAttribution()
    attribution.pytest_sessionstart()
    first = "tests/test_alpha.py::test_one"
    attribution.pytest_runtest_logstart(first, ("tests/test_alpha.py", 1, "test_one"))
    now[0] = 4.0
    second = "tests/test_beta.py::test_two"
    attribution.pytest_runtest_logstart(second, ("tests/test_beta.py", 1, "test_two"))
    now[0] = 7.0
    attribution.pytest_sessionfinish(0)

    output = capsys.readouterr().out.splitlines()
    alpha_end = [line for line in output if "GROUP_END" in line and "tests/test_alpha.py" in line]
    beta_end = [line for line in output if "GROUP_END" in line and "tests/test_beta.py" in line]
    assert len(alpha_end) == 1
    assert len(beta_end) == 1
    assert attribution._groups["tests/test_alpha.py"].wall_seconds == 4.0
    assert attribution._groups["tests/test_beta.py"].wall_seconds == 3.0


def test_only_call_phase_increments_completed(monkeypatch):
    now = _clock(monkeypatch)
    attribution = attribution_module.RuntimeAttribution()
    attribution.pytest_sessionstart()
    nodeid = "tests/test_alpha.py::test_one"
    attribution.pytest_runtest_logstart(nodeid, ("tests/test_alpha.py", 1, "test_one"))
    attribution.pytest_runtest_logreport(_report(nodeid, "setup", 1.0))
    attribution.pytest_runtest_logreport(_report(nodeid, "teardown", 1.0))
    assert attribution._groups["tests/test_alpha.py"].completed == 0
    attribution.pytest_runtest_logreport(_report(nodeid, "call", 1.0))
    now[0] = 2.0
    attribution.pytest_sessionfinish(0)
    assert attribution._groups["tests/test_alpha.py"].completed == 1


def test_unattributed_time_never_negative(monkeypatch):
    now = _clock(monkeypatch)
    attribution = attribution_module.RuntimeAttribution()
    attribution.pytest_sessionstart()
    nodeid = "tests/test_alpha.py::test_one"
    attribution.pytest_runtest_logstart(nodeid, ("tests/test_alpha.py", 1, "test_one"))
    attribution.pytest_runtest_logreport(_report(nodeid, "setup", 3.0))
    attribution.pytest_runtest_logreport(_report(nodeid, "call", 3.0))
    attribution.pytest_runtest_logreport(_report(nodeid, "teardown", 3.0))
    now[0] = 1.0
    attribution.pytest_sessionfinish(0)
    assert attribution._groups["tests/test_alpha.py"].unattributed_seconds >= 0.0


def test_group_total_equal_wall_time_uses_module_name_order(monkeypatch, capsys):
    now = _clock(monkeypatch)
    attribution = attribution_module.RuntimeAttribution()
    attribution.pytest_sessionstart()
    beta = "tests/test_beta.py::test_two"
    attribution.pytest_runtest_logstart(beta, ("tests/test_beta.py", 1, "test_two"))
    attribution.pytest_runtest_logreport(_report(beta, "call", 1.0))
    now[0] = 1.0
    alpha = "tests/test_alpha.py::test_one"
    attribution.pytest_runtest_logstart(alpha, ("tests/test_alpha.py", 1, "test_one"))
    attribution.pytest_runtest_logreport(_report(alpha, "call", 1.0))
    now[0] = 2.0
    attribution.pytest_sessionfinish(0)

    totals = [line for line in capsys.readouterr().out.splitlines() if "GROUP_TOTAL" in line]
    assert ["tests/test_alpha.py" in totals[0], "tests/test_beta.py" in totals[1]] == [True, True]


def test_hooks_are_observer_only():
    attribution = attribution_module.RuntimeAttribution()
    assert attribution.pytest_sessionstart() is None
    assert attribution.pytest_runtest_logstart("tests/test.py::test", ("tests/test.py", 1, "test")) is None
    assert attribution.pytest_runtest_logreport(_report("tests/test.py::test", "call", 0.1)) is None
    assert attribution.pytest_sessionfinish(0) is None

