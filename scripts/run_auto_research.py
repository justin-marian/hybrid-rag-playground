from __future__ import annotations

import itertools
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.utils.io import read_yaml

load_dotenv()
config_path = Path(os.environ["AUTO_RESEARCH_CONFIG"])
run_rag = os.environ.get("RUN_RAG", "false").lower() == "true"

if not config_path.exists():
    raise FileNotFoundError(f"Missing auto research config: {config_path}")


def resolve_value(value: Any, context: dict[str, Any]) -> Any:
    """Resolve a {key} placeholder from the current context."""
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        return context[value[1:-1]]
    return value


def expand_matrix(matrix: dict[str, Any] | None, context: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a YAML matrix into concrete parameter dictionaries."""
    if not matrix:
        return [{}]

    keys = list(matrix.keys())
    values = []
    for key in keys:
        raw = resolve_value(matrix[key], context)
        values.append(raw if isinstance(raw, list) else [raw])

    return [dict(zip(keys, combo, strict=True)) for combo in itertools.product(*values)]


def cli_name(name: str) -> str:
    """Convert snake_case YAML keys into Click CLI flags."""
    return "--" + name.replace("_", "-")


def build_command(module: str, args: dict[str, Any], context: dict[str, Any]) -> list[str]:
    """Build a python -m command from module name and YAML args."""
    command = [sys.executable, "-m", module]

    for key, raw_value in args.items():
        value = resolve_value(raw_value, context)
        if value is None or value is False:
            continue

        flag = cli_name(key)
        if value is True:
            command.append(flag)
            continue

        if isinstance(value, list | tuple):
            for item in value:
                command.extend([flag, str(item)])
            continue

        command.extend([flag, str(value)])

    return command


def should_skip_stage(stage: dict[str, Any]) -> bool:
    """Return whether a stage should be skipped."""
    if not stage.get("enabled", True):
        return True

    module = str(stage["module"])
    is_rag_stage = "rag_demo" in module or "run_single" in module
    return is_rag_stage and not run_rag


def run_command(command: list[str], log_path: Path, stop_on_failure: bool) -> int:
    """Run a command while teeing output to a log file."""
    print(f"\n$ {shlex.join(command)}")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)

        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log.write(line)

        return_code = process.wait()

    if return_code != 0 and stop_on_failure:
        raise SystemExit(return_code)

    return return_code


def main():
    """Run all enabled stages from the auto research YAML plan."""
    cfg = read_yaml(config_path)
    defaults = cfg.get("defaults", {})
    execution = cfg.get("execution", {})
    stages = cfg.get("stages", [])

    stop_on_failure = bool(execution.get("stop_on_failure", False))
    log_dir = Path(execution.get("log_dir", "logs/auto_research"))
    failures: list[tuple[str, int]] = []

    for stage in stages:
        if should_skip_stage(stage):
            print(f"Skipping stage: {stage.get('name', '<unnamed>')}")
            continue

        stage_name = str(stage["name"])
        module = str(stage["module"])
        base_args = stage.get("args")
        commands = stage.get("commands")

        print(f"\n=== Stage: {stage_name} ===")

        if commands:
            for index, command_cfg in enumerate(commands, start=1):
                context = {**defaults}
                args = command_cfg.get("args", {})
                command = build_command(module, args, context)
                code = run_command(command, log_dir / f"{stage_name}_{index}.log", stop_on_failure)
                if code != 0:
                    failures.append((f"{stage_name}_{index}", code))
            continue

        for index, matrix_values in enumerate(expand_matrix(stage.get("matrix"), defaults), start=1):
            context = {**defaults, **matrix_values}
            command = build_command(module, base_args or {}, context)
            suffix = "_".join(f"{key}-{value}" for key, value in matrix_values.items())
            run_name = f"{stage_name}_{suffix or index}"
            code = run_command(command, log_dir / f"{run_name}.log", stop_on_failure)
            if code != 0:
                failures.append((run_name, code))

    if not failures:
        print("\nAll enabled auto research stages completed successfully.")
        return

    print("\nFailed experiment runs:")
    for name, code in failures:
        print(f"  - {name}: exit code {code}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
