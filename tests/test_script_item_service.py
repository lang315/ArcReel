import json
from pathlib import Path

import pytest

from lib.data_validator import DataValidator
from lib.project_manager import ProjectManager
from lib.script_item_service import (
    BadRequestError,
    OptimisticLockError,
    ScriptItemService,
)


def _image_prompt() -> dict:
    return {
        "scene": "雨夜街道",
        "composition": {
            "shot_type": "Medium Shot",
            "lighting": "暖光",
            "ambiance": "薄雾",
        },
    }


def _video_prompt() -> dict:
    return {
        "action": "角色慢慢转身",
        "camera_motion": "Static",
        "ambiance_audio": "风声",
        "dialogue": [],
    }


def _build_segment(item_uid: str, display_id: str, text: str) -> dict:
    return {
        "item_uid": item_uid,
        "segment_id": display_id,
        "episode": 1,
        "duration_seconds": 4,
        "segment_break": False,
        "novel_text": text,
        "characters_in_segment": [],
        "clues_in_segment": [],
        "image_prompt": _image_prompt(),
        "video_prompt": _video_prompt(),
        "transition_to_next": "cut",
        "generated_assets": {
            "storyboard_image": None,
            "video_clip": None,
            "video_uri": None,
            "status": "pending",
        },
    }


def _load_script(project_dir: Path) -> dict:
    return json.loads((project_dir / "scripts" / "episode_1.json").read_text(encoding="utf-8"))


class TestScriptItemService:
    def test_insert_update_delete_roundtrip(self, tmp_path):
        pm = ProjectManager(tmp_path / "projects")
        pm.create_project("demo")
        pm.create_project_metadata("demo", "Demo", "Anime", "narration")
        project_dir = pm.get_project_path("demo")

        script = {
            "schema_version": 2,
            "episode": 1,
            "title": "第一集",
            "content_mode": "narration",
            "summary": "摘要",
            "novel": {"title": "小说", "chapter": "1", "source_file": ""},
            "characters_in_episode": [],
            "clues_in_episode": [],
            "segments": [
                _build_segment("itm_111111111111", "E1S01", "原文1"),
                _build_segment("itm_222222222222", "E1S02", "原文2"),
            ],
        }
        pm.save_script("demo", script, "episode_1.json")

        service = ScriptItemService(pm, DataValidator(pm.projects_root))
        current = _load_script(project_dir)
        inserted = service.insert_item(
            project_name="demo",
            script_file="episode_1.json",
            base_updated_at=current["metadata"]["updated_at"],
            position="end",
            anchor_item_uid=None,
            item={
                "duration_seconds": 4,
                "segment_break": False,
                "novel_text": "新增原文",
                "characters_in_segment": [],
                "clues_in_segment": [],
                "image_prompt": _image_prompt(),
                "video_prompt": _video_prompt(),
                "transition_to_next": "cut",
            },
        )
        assert inserted["action"] == "insert"

        current = _load_script(project_dir)
        new_item = current["segments"][-1]
        assert new_item["segment_id"] == "E1S03"
        assert new_item["generated_assets"]["storyboard_image"] is None

        target = current["segments"][0]
        target_uid = target["item_uid"]
        storyboard_path = project_dir / f"storyboards/item_{target_uid}.png"
        video_path = project_dir / f"videos/item_{target_uid}.mp4"
        storyboard_path.write_bytes(b"png")
        video_path.write_bytes(b"mp4")
        target["generated_assets"]["storyboard_image"] = f"storyboards/item_{target_uid}.png"
        target["generated_assets"]["video_clip"] = f"videos/item_{target_uid}.mp4"
        target["generated_assets"]["status"] = "completed"
        pm.save_script("demo", current, "episode_1.json")
        current = _load_script(project_dir)

        updated = service.update_item(
            project_name="demo",
            script_file="episode_1.json",
            item_uid=target_uid,
            base_updated_at=current["metadata"]["updated_at"],
            updates={"novel_text": "修改后原文"},
        )
        assert updated["media_invalidated"] is True

        current = _load_script(project_dir)
        updated_item = current["segments"][0]
        assert updated_item["novel_text"] == "修改后原文"
        assert updated_item["generated_assets"]["storyboard_image"] is None
        assert not storyboard_path.exists()
        assert not video_path.exists()
        recycle_manifest = json.loads(
            (project_dir / "recycle_bin" / "manifest.json").read_text(encoding="utf-8")
        )
        assert recycle_manifest["entries"][-1]["item_uid"] == target_uid

        current = _load_script(project_dir)
        deleted_uid = current["segments"][1]["item_uid"]
        deleted = service.delete_item(
            project_name="demo",
            script_file="episode_1.json",
            item_uid=deleted_uid,
            base_updated_at=current["metadata"]["updated_at"],
            reason="test_delete",
        )
        assert deleted["action"] == "delete"
        current = _load_script(project_dir)
        assert [segment["segment_id"] for segment in current["segments"]] == ["E1S01", "E1S02"]

    def test_delete_last_item_rejected(self, tmp_path):
        pm = ProjectManager(tmp_path / "projects")
        pm.create_project("demo")
        pm.create_project_metadata("demo", "Demo", "Anime", "narration")
        pm.save_script(
            "demo",
            {
                "schema_version": 2,
                "episode": 1,
                "title": "第一集",
                "content_mode": "narration",
                "summary": "摘要",
                "novel": {"title": "小说", "chapter": "1", "source_file": ""},
                "characters_in_episode": [],
                "clues_in_episode": [],
                "segments": [_build_segment("itm_111111111111", "E1S01", "原文1")],
            },
            "episode_1.json",
        )
        script = pm.load_script("demo", "episode_1.json")
        service = ScriptItemService(pm, DataValidator(pm.projects_root))
        with pytest.raises(BadRequestError):
            service.delete_item(
                project_name="demo",
                script_file="episode_1.json",
                item_uid="itm_111111111111",
                base_updated_at=script["metadata"]["updated_at"],
                reason="test",
            )

    def test_base_updated_at_conflict(self, tmp_path):
        pm = ProjectManager(tmp_path / "projects")
        pm.create_project("demo")
        pm.create_project_metadata("demo", "Demo", "Anime", "narration")
        pm.save_script(
            "demo",
            {
                "schema_version": 2,
                "episode": 1,
                "title": "第一集",
                "content_mode": "narration",
                "summary": "摘要",
                "novel": {"title": "小说", "chapter": "1", "source_file": ""},
                "characters_in_episode": [],
                "clues_in_episode": [],
                "segments": [_build_segment("itm_111111111111", "E1S01", "原文1")],
            },
            "episode_1.json",
        )
        service = ScriptItemService(pm, DataValidator(pm.projects_root))
        with pytest.raises(OptimisticLockError):
            service.update_item(
                project_name="demo",
                script_file="episode_1.json",
                item_uid="itm_111111111111",
                base_updated_at="stale",
                updates={"novel_text": "修改"},
            )
