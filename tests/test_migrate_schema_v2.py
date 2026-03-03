import json
from pathlib import Path

import scripts.migrate_schema_v2 as migrate_schema_v2
from lib.project_manager import ProjectManager


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestMigrateSchemaV2:
    def test_migrate_project_upgrades_schema_and_assets(self, tmp_path):
        pm = ProjectManager(tmp_path / "projects")
        pm.create_project("demo")
        pm.create_project_metadata("demo", "Demo", "Anime", "narration")
        project_dir = pm.get_project_path("demo")

        project = _read_json(project_dir / "project.json")
        project.pop("schema_version", None)
        (project_dir / "project.json").write_text(
            json.dumps(project, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        script = {
            "episode": 1,
            "title": "第一集",
            "content_mode": "narration",
            "summary": "摘要",
            "novel": {"title": "小说", "chapter": "1", "source_file": ""},
            "characters_in_episode": [],
            "clues_in_episode": [],
            "segments": [
                {
                    "segment_id": "E1S01",
                    "episode": 1,
                    "duration_seconds": 4,
                    "segment_break": False,
                    "novel_text": "原文1",
                    "characters_in_segment": [],
                    "clues_in_segment": [],
                    "image_prompt": {
                        "scene": "场景",
                        "composition": {
                            "shot_type": "Medium Shot",
                            "lighting": "暖光",
                            "ambiance": "薄雾",
                        },
                    },
                    "video_prompt": {
                        "action": "走路",
                        "camera_motion": "Static",
                        "ambiance_audio": "风声",
                        "dialogue": [],
                    },
                    "generated_assets": {
                        "storyboard_image": "storyboards/scene_E1S01.png",
                        "video_clip": "videos/scene_E1S01.mp4",
                        "video_uri": None,
                        "status": "completed",
                    },
                }
            ],
        }
        (project_dir / "scripts" / "episode_1.json").write_text(
            json.dumps(script, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (project_dir / "storyboards" / "scene_E1S01.png").write_bytes(b"png")
        (project_dir / "videos" / "scene_E1S01.mp4").write_bytes(b"mp4")
        (project_dir / "versions").mkdir(exist_ok=True)
        (project_dir / "versions" / "versions.json").write_text(
            json.dumps(
                {
                    "storyboards": {"E1S01": {"current_version": 1, "versions": []}},
                    "videos": {"E1S01": {"current_version": 1, "versions": []}},
                    "characters": {},
                    "clues": {},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        migrate_schema_v2.migrate_project("demo", pm, False)

        migrated_project = _read_json(project_dir / "project.json")
        migrated_script = _read_json(project_dir / "scripts" / "episode_1.json")
        item_uid = migrated_script["segments"][0]["item_uid"]

        assert migrated_project["schema_version"] == 2
        assert migrated_script["schema_version"] == 2
        assert item_uid.startswith("itm_")
        assert migrated_script["segments"][0]["generated_assets"]["storyboard_image"] == (
            f"storyboards/item_{item_uid}.png"
        )
        assert (project_dir / f"storyboards/item_{item_uid}.png").exists()
        versions = _read_json(project_dir / "versions" / "versions.json")
        assert item_uid in versions["storyboards"]
        assert item_uid in versions["videos"]

    def test_main_dry_run_does_not_modify_source_project(self, tmp_path, monkeypatch):
        projects_root = tmp_path / "projects"
        pm = ProjectManager(projects_root)
        pm.create_project("demo")
        pm.create_project_metadata("demo", "Demo", "Anime", "narration")
        project_dir = pm.get_project_path("demo")
        (project_dir / "scripts" / "episode_1.json").write_text(
            json.dumps(
                {
                    "episode": 1,
                    "title": "第一集",
                    "content_mode": "narration",
                    "summary": "摘要",
                    "novel": {"title": "小说", "chapter": "1", "source_file": ""},
                    "characters_in_episode": [],
                    "clues_in_episode": [],
                    "segments": [
                        {
                            "segment_id": "E1S01",
                            "episode": 1,
                            "duration_seconds": 4,
                            "segment_break": False,
                            "novel_text": "原文1",
                            "characters_in_segment": [],
                            "clues_in_segment": [],
                            "image_prompt": {
                                "scene": "场景",
                                "composition": {
                                    "shot_type": "Medium Shot",
                                    "lighting": "暖光",
                                    "ambiance": "薄雾",
                                },
                            },
                            "video_prompt": {
                                "action": "走路",
                                "camera_motion": "Static",
                                "ambiance_audio": "风声",
                                "dialogue": [],
                            },
                            "generated_assets": {
                                "storyboard_image": None,
                                "video_clip": None,
                                "video_uri": None,
                                "status": "pending",
                            },
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        before = (project_dir / "scripts" / "episode_1.json").read_text(encoding="utf-8")

        monkeypatch.setattr(migrate_schema_v2, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr("sys.argv", ["migrate_schema_v2.py", "--project", "demo", "--dry-run"])

        assert migrate_schema_v2.main() == 0
        after = (project_dir / "scripts" / "episode_1.json").read_text(encoding="utf-8")
        assert before == after
