"""Lambda entry point. EventBridge Scheduler invokes it with {"command": "<main.COMMANDS key>"}."""

import main
from lib.logging import setup as setup_logging


def lambda_handler(event, context):
    setup_logging()
    command = (event or {}).get("command", "run")
    if command not in main.COMMANDS:
        raise ValueError(f"Unknown command: {command}")
    if not main._run_cli(command):
        raise RuntimeError(f"Command '{command}' failed")
    return {"command": command, "ok": True}
