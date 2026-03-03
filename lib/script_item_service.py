"""
Script item V2 helpers and single-item editing service.
"""

from __future__ import annotations

import copy
import json
import re
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from lib.data_validator import DataValidator, ValidationResult
from lib.script_models import DramaScene, NarrationSegment

SCHEMA_VERSION = 2
ITEM_UID_PATTERN = re.compile(r"^itm_[0-9a-f]{12}$")
DISPLAY_ID_PATTERN = re.compile(r"^E\d+S\d+$")
InsertPosition = Literal["before", "after", "start", "end"]

ALLOWED_INSERT_FIELDS: dict[str, set[str]] = {
    "narration": {
        "duration_seconds",
        "segment_break",
        "novel_text",
        "characters_in_segment",
        "clues_in_segment",
        "image_prompt",
        "video_prompt",
        "transition_to_next",
    },
    "drama": {
        "duration_seconds",
        "segment_break",
        "scene_type",
        "characters_in_scene",
        "clues_in_scene",
        "image_prompt",
        "video_prompt",
        "transition_to_next",
    },
}

ALLOWED_UPDATE_FIELDS = copy.deepcopy(ALLOWED_INSERT_FIELDS)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_item_uid() -> str:
    return f"itm_{secrets.token_hex(6)}"


def create_generated_assets() -> dict[str, Any]:
    return {
        "storyboard_image": None,
        "video_clip": None,
        "video_uri": None,
        "status": "pending",
    }


def build_asset_relative_path(resource_type: Literal["storyboards", "videos"], item_uid: str) -> str:
    if resource_type == "storyboards":
        return f"storyboards/item_{item_uid}.png"
    return f"videos/item_{item_uid}.mp4"


def display_id_field_for_mode(content_mode: str) -> str:
    return "segment_id" if content_mode == "narration" else "scene_id"


def characters_field_for_mode(content_mode: str) -> str:
    return "characters_in_segment" if content_mode == "narration" else "characters_in_scene"


def clues_field_for_mode(content_mode: str) -> str:
    return "clues_in_segment" if content_mode == "narration" else "clues_in_scene"


def items_field_for_mode(content_mode: str) -> str:
    return "segments" if content_mode == "narration" else "scenes"


def iter_script_items(script: dict[str, Any]) -> list[dict[str, Any]]:
    content_mode = str(script.get("content_mode") or "narration")
    items = script.get(items_field_for_mode(content_mode), [])
    return items if isinstance(items, list) else []


def get_script_updated_at(script: dict[str, Any]) -> str:
    metadata = script.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("updated_at")
        if isinstance(value, str):
            return value
    return ""


def set_script_updated_at(script: dict[str, Any], updated_at: str | None = None) -> str:
    metadata = script.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        script["metadata"] = metadata
    value = updated_at or utc_now_iso()
    metadata["updated_at"] = value
    metadata.setdefault("created_at", value)
    return value


def build_display_id(episode: int, index: int) -> str:
    return f"E{episode}S{index:02d}"


def ensure_schema_v2(script: dict[str, Any], project: dict[str, Any]) -> None:
    if int(project.get("schema_version") or 0) != SCHEMA_VERSION:
        raise MigrationRequiredError("migration_required")
    if int(script.get("schema_version") or 0) != SCHEMA_VERSION:
        raise MigrationRequiredError("migration_required")


def find_item_index_by_uid(items: list[dict[str, Any]], item_uid: str) -> int:
    for index, item in enumerate(items):
        if str(item.get("item_uid") or "") == item_uid:
            return index
    raise ItemNotFoundError(f"item_uid '{item_uid}' 不存在")


def get_item_by_uid(script: dict[str, Any], item_uid: str) -> tuple[dict[str, Any], int]:
    items = iter_script_items(script)
    index = find_item_index_by_uid(items, item_uid)
    return items[index], index


def get_display_id(item: dict[str, Any], content_mode: str) -> str:
    return str(item.get(display_id_field_for_mode(content_mode)) or "")


def renumber_script_items(script: dict[str, Any]) -> list[dict[str, str]]:
    content_mode = str(script.get("content_mode") or "narration")
    display_field = display_id_field_for_mode(content_mode)
    items = iter_script_items(script)
    episode = int(script.get("episode") or 1)
    renumbered: list[dict[str, str]] = []
    for index, item in enumerate(items, start=1):
        previous = str(item.get(display_field) or "")
        current = build_display_id(episode, index)
        item[display_field] = current
        renumbered.append(
            {
                "item_uid": str(item.get("item_uid") or ""),
                "previous_display_id": previous,
                "display_id": current,
            }
        )
    return renumbered


def recalculate_script_metadata(script: dict[str, Any]) -> None:
    items = iter_script_items(script)
    content_mode = str(script.get("content_mode") or "narration")
    default_duration = 4 if content_mode == "narration" else 8
    duration_seconds = sum(int(item.get("duration_seconds", default_duration)) for item in items)
    metadata = script.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        script["metadata"] = metadata
    metadata["total_scenes"] = len(items)
    metadata["estimated_duration_seconds"] = duration_seconds
    script["duration_seconds"] = duration_seconds


def invalidate_media_assets(item: dict[str, Any]) -> bool:
    assets = item.setdefault("generated_assets", create_generated_assets())
    if not isinstance(assets, dict):
        assets = create_generated_assets()
        item["generated_assets"] = assets
    had_media = bool(assets.get("storyboard_image") or assets.get("video_clip") or assets.get("video_uri"))
    assets["storyboard_image"] = None
    assets["video_clip"] = None
    assets["video_uri"] = None
    assets["status"] = "pending"
    return had_media


class ScriptItemServiceError(RuntimeError):
    status_code: int = 400

    def __init__(self, detail: str, *, status_code: int | None = None):
        super().__init__(detail)
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code

    def __str__(self) -> str:
        return self.detail


class MigrationRequiredError(ScriptItemServiceError):
    status_code = 409


class OptimisticLockError(ScriptItemServiceError):
    status_code = 409


class ItemNotFoundError(ScriptItemServiceError):
    status_code = 404


class ScriptValidationError(ScriptItemServiceError):
    status_code = 422


class BadRequestError(ScriptItemServiceError):
    status_code = 400


class ScriptItemService:
    def __init__(self, project_manager, validator: DataValidator | None = None):
        self.pm = project_manager
        self.validator = validator or DataValidator(self.pm.projects_root)

    def insert_item(
        self,
        *,
        project_name: str,
        script_file: str,
        base_updated_at: str,
        position: InsertPosition,
        anchor_item_uid: str | None,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        project_dir, project, script = self._load_context(project_name, script_file)
        self._validate_base_updated_at(script, base_updated_at)
        content_mode = str(script.get("content_mode") or project.get("content_mode") or "narration")
        items = iter_script_items(script)
        if position not in {"before", "after", "start", "end"}:
            raise BadRequestError("position 必须是 before/after/start/end")

        if position in {"before", "after"} and not anchor_item_uid:
            raise BadRequestError("before/after 必须提供 anchor_item_uid")
        if position in {"start", "end"} and anchor_item_uid:
            raise BadRequestError("start/end 不允许提供 anchor_item_uid")

        new_item = self._build_insert_item(script, content_mode, item)
        index = self._resolve_insert_index(items, position, anchor_item_uid)
        items.insert(index, new_item)
        renumbered = renumber_script_items(script)
        recalculate_script_metadata(script)
        updated_at = set_script_updated_at(script)
        self._validate_candidate(project_dir, project, script, script_file)
        self.pm.save_script(project_name, script, script_file)

        return {
            "success": True,
            "action": "insert",
            "script_file": script_file,
            "updated_at": updated_at,
            "created_item_uid": new_item["item_uid"],
            "inserted_display_id": get_display_id(new_item, content_mode),
            "renumbered_items": renumbered,
        }

    def update_item(
        self,
        *,
        project_name: str,
        script_file: str,
        item_uid: str,
        base_updated_at: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        project_dir, project, script = self._load_context(project_name, script_file)
        self._validate_base_updated_at(script, base_updated_at)
        content_mode = str(script.get("content_mode") or project.get("content_mode") or "narration")
        items = iter_script_items(script)
        index = find_item_index_by_uid(items, item_uid)
        original_item = copy.deepcopy(items[index])
        updated_item = copy.deepcopy(items[index])

        self._apply_updates(script, content_mode, updated_item, updates)
        media_invalidated = invalidate_media_assets(updated_item)
        items[index] = updated_item
        renumber_script_items(script)
        recalculate_script_metadata(script)
        updated_at = set_script_updated_at(script)
        self._validate_candidate(project_dir, project, script, script_file)
        self.pm.save_script(project_name, script, script_file)

        if media_invalidated:
            self._archive_item_assets(
                project_dir=project_dir,
                script_file=script_file,
                script=script,
                item_snapshot=original_item,
                reason="update_invalidated_media",
            )

        return {
            "success": True,
            "action": "update",
            "script_file": script_file,
            "updated_at": updated_at,
            "item_uid": item_uid,
            "display_id": get_display_id(updated_item, content_mode),
            "media_invalidated": media_invalidated,
        }

    def delete_item(
        self,
        *,
        project_name: str,
        script_file: str,
        item_uid: str,
        base_updated_at: str,
        reason: str,
    ) -> dict[str, Any]:
        project_dir, project, script = self._load_context(project_name, script_file)
        self._validate_base_updated_at(script, base_updated_at)
        content_mode = str(script.get("content_mode") or project.get("content_mode") or "narration")
        items = iter_script_items(script)
        if len(items) <= 1:
            raise BadRequestError("script 至少保留一个 item")

        index = find_item_index_by_uid(items, item_uid)
        deleted_item = copy.deepcopy(items.pop(index))
        renumbered = renumber_script_items(script)
        recalculate_script_metadata(script)
        updated_at = set_script_updated_at(script)
        self._validate_candidate(project_dir, project, script, script_file)
        self.pm.save_script(project_name, script, script_file)
        self._archive_item_assets(
            project_dir=project_dir,
            script_file=script_file,
            script=script,
            item_snapshot=deleted_item,
            reason=reason or "deleted",
        )

        return {
            "success": True,
            "action": "delete",
            "script_file": script_file,
            "updated_at": updated_at,
            "deleted_item_uid": item_uid,
            "deleted_display_id": get_display_id(deleted_item, content_mode),
            "renumbered_items": renumbered,
        }

    def _load_context(
        self,
        project_name: str,
        script_file: str,
    ) -> tuple[Path, dict[str, Any], dict[str, Any]]:
        project_dir = self.pm.get_project_path(project_name)
        project = self.pm.load_project(project_name)
        script = self.pm.load_script(project_name, script_file)
        ensure_schema_v2(script, project)
        return project_dir, project, script

    def _validate_base_updated_at(self, script: dict[str, Any], base_updated_at: str) -> None:
        current = get_script_updated_at(script)
        if not current:
            raise OptimisticLockError("script 缺少 updated_at")
        if current != base_updated_at:
            raise OptimisticLockError("base_updated_at 冲突")

    def _resolve_insert_index(
        self,
        items: list[dict[str, Any]],
        position: InsertPosition,
        anchor_item_uid: str | None,
    ) -> int:
        if position == "start":
            return 0
        if position == "end":
            return len(items)

        if not anchor_item_uid:
            raise BadRequestError("缺少 anchor_item_uid")
        anchor_index = find_item_index_by_uid(items, anchor_item_uid)
        return anchor_index if position == "before" else anchor_index + 1

    def _build_insert_item(
        self,
        script: dict[str, Any],
        content_mode: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise BadRequestError("item 必须是对象")
        unknown_fields = set(payload) - ALLOWED_INSERT_FIELDS[content_mode]
        if unknown_fields:
            raise BadRequestError(f"item 包含不允许字段: {sorted(unknown_fields)}")

        item_uid = generate_item_uid()
        draft = {
            **payload,
            "item_uid": item_uid,
            display_id_field_for_mode(content_mode): build_display_id(int(script.get("episode") or 1), 1),
            "generated_assets": create_generated_assets(),
        }
        if content_mode == "narration":
            draft["episode"] = int(script.get("episode") or 1)
            validated = NarrationSegment.model_validate(draft).model_dump()
        else:
            validated = DramaScene.model_validate(draft).model_dump()
        validated["generated_assets"] = create_generated_assets()
        return validated

    def _apply_updates(
        self,
        script: dict[str, Any],
        content_mode: str,
        item: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        if not isinstance(updates, dict) or not updates:
            raise BadRequestError("updates 不能为空")
        unknown_fields = set(updates) - ALLOWED_UPDATE_FIELDS[content_mode]
        if unknown_fields:
            raise BadRequestError(f"updates 包含不允许字段: {sorted(unknown_fields)}")

        for key, value in updates.items():
            item[key] = value

        if content_mode == "narration":
            validated = NarrationSegment.model_validate(
                {
                    **item,
                    "episode": int(script.get("episode") or item.get("episode") or 1),
                    display_id_field_for_mode(content_mode): get_display_id(item, content_mode)
                    or build_display_id(int(script.get("episode") or 1), 1),
                }
            ).model_dump()
        else:
            validated = DramaScene.model_validate(
                {
                    **item,
                    display_id_field_for_mode(content_mode): get_display_id(item, content_mode)
                    or build_display_id(int(script.get("episode") or 1), 1),
                }
            ).model_dump()

        item.clear()
        item.update(validated)

    def _validate_candidate(
        self,
        project_dir: Path,
        project: dict[str, Any],
        script: dict[str, Any],
        script_file: str,
    ) -> None:
        result = self.validator.validate_script_payload(
            project_dir=project_dir,
            project=project,
            script=script,
            script_file=script_file,
        )
        if not result.valid:
            raise ScriptValidationError("\n".join(result.errors))

    def _ensure_recycle_bin(self, project_dir: Path) -> Path:
        recycle_dir = project_dir / "recycle_bin"
        (recycle_dir / "storyboards").mkdir(parents=True, exist_ok=True)
        (recycle_dir / "videos").mkdir(parents=True, exist_ok=True)
        manifest_path = recycle_dir / "manifest.json"
        if not manifest_path.exists():
            manifest_path.write_text(
                json.dumps({"entries": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return manifest_path

    def _append_recycle_entry(self, manifest_path: Path, entry: dict[str, Any]) -> None:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {"entries": []}
        entries = payload.get("entries")
        if not isinstance(entries, list):
            entries = []
            payload["entries"] = entries
        entries.append(entry)
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _archive_item_assets(
        self,
        *,
        project_dir: Path,
        script_file: str,
        script: dict[str, Any],
        item_snapshot: dict[str, Any],
        reason: str,
    ) -> None:
        manifest_path = self._ensure_recycle_bin(project_dir)
        content_mode = str(script.get("content_mode") or "narration")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        item_uid = str(item_snapshot.get("item_uid") or "")
        assets = item_snapshot.get("generated_assets")
        if not isinstance(assets, dict):
            assets = {}

        archived_assets = {
            "storyboard_image": None,
            "video_clip": None,
        }
        for field, folder, extension in (
            ("storyboard_image", "storyboards", ".png"),
            ("video_clip", "videos", ".mp4"),
        ):
            source_rel = str(assets.get(field) or "")
            if not source_rel:
                continue
            source_path = project_dir / source_rel
            if not source_path.exists():
                continue
            target_rel = f"recycle_bin/{folder}/item_{item_uid}_{timestamp}{extension}"
            target_path = project_dir / target_rel
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(target_path))
            archived_assets[field] = target_rel

        self._append_recycle_entry(
            manifest_path,
            {
                "item_uid": item_uid,
                "script_file": script_file,
                "content_mode": content_mode,
                "episode": int(script.get("episode") or item_snapshot.get("episode") or 1),
                "last_display_id": get_display_id(item_snapshot, content_mode),
                "deleted_at": utc_now_iso(),
                "reason": reason,
                "snapshot": item_snapshot,
                "archived_assets": archived_assets,
            },
        )
