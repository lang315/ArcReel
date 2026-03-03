#!/usr/bin/env python3
"""
CLI wrapper for V2 script item edits.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib import PROJECT_ROOT as APP_ROOT
from lib.data_validator import DataValidator
from lib.project_manager import ProjectManager
from lib.script_item_service import (
    BadRequestError,
    ItemNotFoundError,
    MigrationRequiredError,
    OptimisticLockError,
    ScriptItemService,
    ScriptValidationError,
)


def load_payload(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"payload JSON 解析失败: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("payload 必须是 JSON object")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Edit V2 script items via service layer")
    parser.add_argument("project", help="项目名")
    parser.add_argument("script_file", help="剧本文件名")
    parser.add_argument("operation", choices=["insert", "update", "delete"])
    parser.add_argument("--item-uid", help="目标 item_uid")
    parser.add_argument("--base-updated-at", required=True, help="当前 script metadata.updated_at")
    parser.add_argument("--position", choices=["before", "after", "start", "end"])
    parser.add_argument("--anchor-item-uid")
    parser.add_argument("--payload", help="JSON payload")
    parser.add_argument("--reason", default="assistant_delete")
    args = parser.parse_args()

    pm = ProjectManager(APP_ROOT / "projects")
    service = ScriptItemService(pm, DataValidator(pm.projects_root))

    payload = load_payload(args.payload)

    try:
        if args.operation == "insert":
            if not args.position:
                raise SystemExit("insert 必须提供 --position")
            result = service.insert_item(
                project_name=args.project,
                script_file=args.script_file,
                base_updated_at=args.base_updated_at,
                position=args.position,
                anchor_item_uid=args.anchor_item_uid,
                item=payload,
            )
        elif args.operation == "update":
            if not args.item_uid:
                raise SystemExit("update 必须提供 --item-uid")
            result = service.update_item(
                project_name=args.project,
                script_file=args.script_file,
                item_uid=args.item_uid,
                base_updated_at=args.base_updated_at,
                updates=payload,
            )
        else:
            if not args.item_uid:
                raise SystemExit("delete 必须提供 --item-uid")
            result = service.delete_item(
                project_name=args.project,
                script_file=args.script_file,
                item_uid=args.item_uid,
                base_updated_at=args.base_updated_at,
                reason=args.reason,
            )
    except (
        BadRequestError,
        ItemNotFoundError,
        MigrationRequiredError,
        OptimisticLockError,
        ScriptValidationError,
        FileNotFoundError,
    ) as exc:
        print(json.dumps({"success": False, "detail": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
