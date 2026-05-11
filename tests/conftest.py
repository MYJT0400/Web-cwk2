"""Pytest configuration for local import paths."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


_DEMO_PASS_LINES = True


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--demo-pass-lines",
        action="store_true",
        default=True,
        help="Print one PASS line per successful test item.",
    )
    parser.addoption(
        "--demo-slow",
        action="store_true",
        default=True,
        help="Add a delay after each executed test item for demo recording.",
    )
    parser.addoption(
        "--demo-delay",
        action="store",
        default="2.0",
        help="Delay seconds used with --demo-slow (default: 2.0).",
    )


def pytest_configure(config: pytest.Config) -> None:
    global _DEMO_PASS_LINES
    _DEMO_PASS_LINES = bool(config.getoption("--demo-pass-lines"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item):
    outcome = yield
    if item.config.getoption("--demo-slow"):
        try:
            delay = float(item.config.getoption("--demo-delay"))
        except Exception:
            delay = 2.0
        if delay > 0:
            time.sleep(delay)
    return outcome


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when != "call":
        return
    if not report.passed:
        return
    if not _DEMO_PASS_LINES:
        return
    print(f"[PASS] {report.nodeid}", flush=True)
