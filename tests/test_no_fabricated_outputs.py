"""Offline regression tests: never import the live application or brokers."""
import ast
from pathlib import Path
from typing import Any, Dict

import pytest


ROOT = Path(__file__).resolve().parents[1]


def isolated_class(relative_path, class_name, methods, namespace=None):
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    node.body = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in methods]
    scope = {"Dict": Dict, "Any": Any, **(namespace or {})}
    exec(compile(ast.Module(body=[node], type_ignores=[]), relative_path, "exec"), scope)
    return scope[class_name]


def test_training_cannot_fabricate_metrics_or_change_settings():
    trainer = isolated_class("services/trainer/bot_trainer.py", "BotTrainer", {"train_bot"})()
    result = trainer.train_bot()
    assert result["applied_to_live_settings"] is False
    assert result["backtest_performance"] is None
    assert result["scenarios_tested"] == 0


def test_lab_does_not_fabricate_trades():
    lab = isolated_class("services/engine/autonomous_lab.py", "AutonomousAlgorithmLab",
                         {"run_autonomous_experiment_pool"})()
    result = lab.run_autonomous_experiment_pool()
    assert result["status"] == "UNAVAILABLE"
    assert result["trials_ledger"] == []
    assert result["equity_curve"] == []
    assert result["win_rate"] is None
    assert result["net_total_pnl"] is None
    assert lab.last_run_result == result


@pytest.mark.parametrize("filename,names", [
    ("populate_memory.py", ["generate_synthetic_trades", "update_memory_file"]),
    ("active_scanner_injector.py", ["generate_ma_message", "inject_log", "inject_simulated_trade"]),
])
def test_injection_helpers_fail_before_side_effects(filename, names):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            assert isinstance(node.body[0], ast.Raise)


def test_initial_performance_is_unavailable():
    tree = ast.parse((ROOT / "services/trainer/bot_trainer.py").read_text(encoding="utf-8"))
    trainer = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    init = next(n for n in trainer.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    values = next(n.value for n in init.body if isinstance(n, ast.Assign))
    metrics = {k.value: v for k, v in zip(values.keys, values.values)}
    for key in ("win_rate", "sharpe_ratio", "max_drawdown"):
        assert isinstance(metrics[key], ast.Constant) and metrics[key].value is None