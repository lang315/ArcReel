"""
Bridge layer for reusing existing local skill scripts.
"""

import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SkillCommand:
    action: str
    args: list[str]


@dataclass
class SkillExecutionResult:
    action: str
    command: list[str]
    return_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.return_code == 0


class SkillBridge:
    SCRIPT_MAP = {
        "generate_character": ".claude/skills/generate-characters/scripts/generate_character.py",
        "generate_clue": ".claude/skills/generate-clues/scripts/generate_clue.py",
        "generate_script": ".claude/skills/generate-script/scripts/generate_script.py",
    }

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def parse_command(self, content: str) -> Optional[SkillCommand]:
        text = content.strip()
        if not text.startswith("/"):
            return None

        try:
            tokens = shlex.split(text)
        except ValueError as exc:
            raise ValueError(f"命令解析失败: {exc}") from exc

        if not tokens:
            return None

        cmd = tokens[0].lstrip("/")

        if cmd in ("generate-character", "generate_character"):
            if len(tokens) < 2:
                raise ValueError("用法: /generate-character <角色名>")
            return SkillCommand("generate_character", [" ".join(tokens[1:])])

        if cmd in ("generate-clue", "generate_clue"):
            if len(tokens) < 2:
                raise ValueError("用法: /generate-clue <线索名>")
            return SkillCommand("generate_clue", ["--clue", " ".join(tokens[1:])])

        if cmd in ("generate-clues", "generate_clues"):
            if len(tokens) != 2 or tokens[1] not in ("--all", "--list"):
                raise ValueError("用法: /generate-clues --all 或 /generate-clues --list")
            return SkillCommand("generate_clue", [tokens[1]])

        if cmd in ("generate-script", "generate_script"):
            episode_value: Optional[str] = None
            dry_run = False
            i = 1
            while i < len(tokens):
                token = tokens[i]
                if token in ("--episode", "-e"):
                    if i + 1 >= len(tokens):
                        raise ValueError("用法: /generate-script --episode <集数>")
                    episode_value = tokens[i + 1]
                    i += 2
                    continue
                if token == "--dry-run":
                    dry_run = True
                    i += 1
                    continue
                raise ValueError("用法: /generate-script --episode <集数> [--dry-run]")

            if not episode_value:
                raise ValueError("用法: /generate-script --episode <集数> [--dry-run]")

            args = ["--episode", episode_value]
            if dry_run:
                args.append("--dry-run")
            return SkillCommand("generate_script", args)

        raise ValueError("暂不支持的命令")

    def execute(self, project_name: str, skill_command: SkillCommand) -> SkillExecutionResult:
        script = self.SCRIPT_MAP.get(skill_command.action)
        if script is None:
            raise ValueError(f"unknown action: {skill_command.action}")

        script_path = self.project_root / script
        if not script_path.exists():
            return SkillExecutionResult(
                action=skill_command.action,
                command=[],
                return_code=127,
                stdout="",
                stderr=f"script not found: {script_path}",
            )

        command = [
            sys.executable,
            str(script_path),
            project_name,
            *skill_command.args,
        ]
        completed = subprocess.run(
            command,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return SkillExecutionResult(
            action=skill_command.action,
            command=command,
            return_code=completed.returncode,
            stdout=(completed.stdout or "").strip(),
            stderr=(completed.stderr or "").strip(),
        )

    @staticmethod
    def supported_commands() -> list[str]:
        return [
            "/generate-character <角色名>",
            "/generate-clue <线索名>",
            "/generate-clues --all",
            "/generate-clues --list",
            "/generate-script --episode <集数> [--dry-run]",
        ]

