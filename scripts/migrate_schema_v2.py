#!/usr/bin/env python3
"""
Migrate ArcReel projects to script schema v2.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.data_validator import DataValidator
from lib.project_manager import ProjectManager
from lib.script_item_service import (
    SCHEMA_VERSION,
    build_asset_relative_path,
    create_generated_assets,
    generate_item_uid,
    items_field_for_mode,
    renumber_script_items,
    recalculate_script_metadata,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return deepcopy(default)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_recycle_bin(project_dir: Path) -> Path:
    recycle_dir = project_dir / "recycle_bin"
    (recycle_dir / "storyboards").mkdir(parents=True, exist_ok=True)
    (recycle_dir / "videos").mkdir(parents=True, exist_ok=True)
    manifest_path = recycle_dir / "manifest.json"
    if not manifest_path.exists():
        save_json(manifest_path, {"entries": []})
    return manifest_path


def append_manifest(manifest_path: Path, entry: dict[str, Any]) -> None:
    payload = load_json(manifest_path, {"entries": []})
    entries = payload.get("entries")
    if not isinstance(entries, list):
        entries = []
        payload["entries"] = entries
    entries.append(entry)
    save_json(manifest_path, payload)


def build_display_id_mapping(script: dict[str, Any]) -> dict[str, str]:
    content_mode = str(script.get("content_mode") or "narration")
    items = script.get(items_field_for_mode(content_mode), [])
    display_field = "segment_id" if content_mode == "narration" else "scene_id"
    mapping: dict[str, str] = {}
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        display_id = str(item.get(display_field) or "").strip()
        if not display_id:
            continue
        if display_id in mapping:
            raise ValueError(f"映射歧义：重复展示编号 {display_id}")
        mapping[display_id] = str(item.get("item_uid") or "")
    return mapping


def migrate_script(
    project_dir: Path,
    script_file: str,
    manifest_path: Path,
    dry_run: bool,
) -> dict[str, str]:
    script_path = project_dir / "scripts" / script_file
    script = load_json(script_path, {})
    if not isinstance(script, dict):
        raise ValueError(f"无法加载剧本: {script_path}")

    content_mode = str(script.get("content_mode") or "narration")
    items_key = items_field_for_mode(content_mode)
    items = script.get(items_key, [])
    if not isinstance(items, list) or not items:
        raise ValueError(f"剧本为空: {script_file}")

    display_field = "segment_id" if content_mode == "narration" else "scene_id"
    mapping: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        old_display_id = str(item.get(display_field) or "").strip()
        item_uid = str(item.get("item_uid") or generate_item_uid())
        item["item_uid"] = item_uid
        mapping[old_display_id] = item_uid

        assets = item.get("generated_assets")
        if not isinstance(assets, dict):
            assets = create_generated_assets()
            item["generated_assets"] = assets
        else:
            normalized = create_generated_assets()
            normalized.update(assets)
            assets = normalized
            item["generated_assets"] = assets

        for field, resource_type in (
            ("storyboard_image", "storyboards"),
            ("video_clip", "videos"),
        ):
            current_rel = str(assets.get(field) or "").strip()
            if not current_rel:
                continue
            source_path = project_dir / current_rel
            target_rel = build_asset_relative_path(resource_type, item_uid)
            target_path = project_dir / target_rel
            if not dry_run and source_path.exists() and source_path != target_path:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(target_path))
            assets[field] = target_rel

    script["schema_version"] = SCHEMA_VERSION
    renumber_script_items(script)
    recalculate_script_metadata(script)
    metadata = script.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        script["metadata"] = metadata
    metadata["updated_at"] = utc_now_iso()
    metadata.setdefault("created_at", metadata["updated_at"])

    if not dry_run:
        save_json(script_path, script)
    return mapping


def migrate_versions(
    project_dir: Path,
    item_uid_by_display_id: dict[str, str],
    manifest_path: Path,
    dry_run: bool,
) -> None:
    versions_path = project_dir / "versions" / "versions.json"
    versions = load_json(versions_path, {"storyboards": {}, "videos": {}, "characters": {}, "clues": {}})
    if not isinstance(versions, dict):
        versions = {"storyboards": {}, "videos": {}, "characters": {}, "clues": {}}

    for resource_type in ("storyboards", "videos"):
        resource_map = versions.get(resource_type, {})
        if not isinstance(resource_map, dict):
            continue
        migrated_map: dict[str, Any] = {}
        for resource_id, payload in resource_map.items():
            item_uid = item_uid_by_display_id.get(resource_id)
            if not item_uid:
                append_manifest(
                    manifest_path,
                    {
                        "item_uid": resource_id,
                        "script_file": "",
                        "content_mode": "",
                        "episode": 0,
                        "last_display_id": resource_id,
                        "deleted_at": utc_now_iso(),
                        "reason": f"orphan_{resource_type}_version_key",
                        "snapshot": None,
                        "archived_assets": {
                            "storyboard_image": None,
                            "video_clip": None,
                        },
                    },
                )
                continue
            migrated_map[item_uid] = payload
        versions[resource_type] = migrated_map

    if not dry_run:
        save_json(versions_path, versions)


def archive_orphan_current_assets(
    project_dir: Path,
    item_uid_by_display_id: dict[str, str],
    manifest_path: Path,
    dry_run: bool,
) -> None:
    for resource_type, extension in (("storyboards", ".png"), ("videos", ".mp4")):
        directory = project_dir / resource_type
        if not directory.exists():
            continue
        for path in directory.glob(f"scene_*{extension}"):
            legacy_id = path.stem.replace("scene_", "", 1)
            if legacy_id in item_uid_by_display_id:
                continue
            target_rel = f"recycle_bin/{resource_type}/legacy_{path.name}"
            target_path = project_dir / target_rel
            if not dry_run:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target_path))
            append_manifest(
                manifest_path,
                {
                    "item_uid": legacy_id,
                    "script_file": "",
                    "content_mode": "",
                    "episode": 0,
                    "last_display_id": legacy_id,
                    "deleted_at": utc_now_iso(),
                    "reason": f"orphan_{resource_type}_current_asset",
                    "snapshot": None,
                    "archived_assets": {
                        "storyboard_image": target_rel if resource_type == "storyboards" else None,
                        "video_clip": target_rel if resource_type == "videos" else None,
                    },
                },
            )


def migrate_project(project_name: str, pm: ProjectManager, dry_run: bool) -> None:
    project_dir = pm.get_project_path(project_name)
    project_path = project_dir / "project.json"
    project = load_json(project_path, {})
    if not isinstance(project, dict):
        raise ValueError(f"无法加载 project.json: {project_path}")

    manifest_path = ensure_recycle_bin(project_dir)
    global_mapping: dict[str, str] = {}

    for script_name in pm.list_scripts(project_name):
        mapping = migrate_script(project_dir, script_name, manifest_path, dry_run)
        overlap = set(global_mapping) & set(mapping)
        if overlap:
            raise ValueError(f"映射歧义：重复展示编号 {sorted(overlap)}")
        global_mapping.update(mapping)

    migrate_versions(project_dir, global_mapping, manifest_path, dry_run)
    archive_orphan_current_assets(project_dir, global_mapping, manifest_path, dry_run)

    project["schema_version"] = SCHEMA_VERSION
    metadata = project.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        project["metadata"] = metadata
    metadata["updated_at"] = utc_now_iso()
    metadata.setdefault("created_at", metadata["updated_at"])
    if not dry_run:
        save_json(project_path, project)

    result = DataValidator(pm.projects_root).validate_project_tree(project_dir)
    if not result.valid:
        raise ValueError("\n".join(result.errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="迁移项目到 schema v2")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", type=str, help="单个项目名")
    group.add_argument("--all", action="store_true", help="迁移全部项目")
    parser.add_argument("--dry-run", action="store_true", help="仅验证，不写文件")
    args = parser.parse_args()

    pm = ProjectManager(PROJECT_ROOT / "projects")
    project_names = [args.project] if args.project else pm.list_projects()

    for project_name in project_names:
        print(f"==> 迁移项目: {project_name}")
        if args.dry_run:
            with tempfile.TemporaryDirectory(prefix="arcreel-migrate-v2-") as temp_dir:
                temp_root = Path(temp_dir) / "projects"
                temp_root.mkdir(parents=True, exist_ok=True)
                shutil.copytree(pm.get_project_path(project_name), temp_root / project_name)
                migrate_project(project_name, ProjectManager(temp_root), False)
        else:
            migrate_project(project_name, pm, False)
        print(f"✅ 完成: {project_name}{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
