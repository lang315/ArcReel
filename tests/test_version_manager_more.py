import pytest

from lib.version_manager import VersionManager, _get_versions_file_lock


class TestVersionManagerMore:
    def test_lock_is_reused_for_same_file(self, tmp_path):
        file_a = tmp_path / "a" / "versions.json"
        file_a.parent.mkdir(parents=True)
        lock1 = _get_versions_file_lock(file_a)
        lock2 = _get_versions_file_lock(file_a)
        assert lock1 is lock2

    def test_get_versions_invalid_type_and_helpers(self, tmp_path):
        project = tmp_path / "demo"
        vm = VersionManager(project)

        with pytest.raises(ValueError):
            vm.get_versions("bad", "x")

        assert vm.get_current_version("characters", "Alice") == 0
        assert vm.get_version_file_url("characters", "Alice", 1) is None
        assert vm.get_version_prompt("characters", "Alice", 1) is None
        assert vm.has_versions("characters", "Alice") is False

    def test_add_backup_restore_paths(self, tmp_path):
        project = tmp_path / "demo"
        vm = VersionManager(project)

        current = project / "characters" / "Alice.png"
        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_bytes(b"png-v1")

        assert vm.backup_current("characters", "Alice", current, "p1") == 1
        assert vm.ensure_current_tracked("characters", "Alice", current, "p2") is None

        # create v2
        current.write_bytes(b"png-v2")
        assert vm.add_version("characters", "Alice", "p2", source_file=current) == 2

        info = vm.get_versions("characters", "Alice")
        assert info["current_version"] == 2
        assert len(info["versions"]) == 2
        assert vm.get_version_file_url("characters", "Alice", 2)
        assert vm.get_version_prompt("characters", "Alice", 2) == "p2"
        assert vm.has_versions("characters", "Alice")

        restored = vm.restore_version("characters", "Alice", 1, current)
        assert restored["restored_version"] == 1
        assert restored["current_version"] == 1

        info = vm.get_versions("characters", "Alice")
        assert info["current_version"] == 1
        assert len(info["versions"]) == 2

        current.write_bytes(b"png-v3")
        assert vm.add_version("characters", "Alice", "p3", source_file=current) == 3

    def test_restore_errors_and_missing_current(self, tmp_path):
        project = tmp_path / "demo"
        vm = VersionManager(project)
        current = project / "characters" / "Alice.png"

        assert vm.backup_current("characters", "Alice", current, "p") is None
        assert vm.ensure_current_tracked("characters", "Alice", current, "p") is None

        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_bytes(b"png")
        with pytest.raises(ValueError):
            vm.ensure_current_tracked("bad", "Alice", current, "p")

        with pytest.raises(ValueError):
            vm.restore_version("characters", "missing", 1, current)

        # create record and delete version file to hit FileNotFoundError branch
        vm.add_version("characters", "Alice", "p", source_file=current)
        version_file = project / vm.get_versions("characters", "Alice")["versions"][0]["file"]
        version_file.unlink()

        with pytest.raises(FileNotFoundError):
            vm.restore_version("characters", "Alice", 1, current)

        with pytest.raises(ValueError):
            vm.restore_version("characters", "Alice", 99, current)

    def test_add_version_rejects_traversal_resource_id(self, tmp_path):
        """resource_id 包含路径穿越字符应被拒绝"""
        vm = VersionManager(tmp_path / "demo")
        with pytest.raises(ValueError, match="非法资源 ID"):
            vm.add_version("storyboards", "../../evil", "prompt")
        with pytest.raises(ValueError, match="非法资源 ID"):
            vm.add_version("characters", "foo/bar", "prompt")
        with pytest.raises(ValueError, match="非法资源 ID"):
            vm.add_version("characters", "foo\\bar", "prompt")

    def test_restore_version_rejects_escaped_file_path(self, tmp_path):
        """versions.json 中被篡改的 file 路径应被拒绝"""
        import json

        project = tmp_path / "demo"
        versions_dir = project / "versions"
        versions_dir.mkdir(parents=True)
        versions_file = versions_dir / "versions.json"
        versions_file.write_text(
            json.dumps(
                {
                    "storyboards": {
                        "E1S01": {
                            "current_version": 1,
                            "versions": [
                                {
                                    "version": 1,
                                    "file": "../../etc/passwd",
                                    "prompt": "p",
                                    "created_at": "2025-01-01T00:00:00",
                                }
                            ],
                        }
                    }
                }
            )
        )

        vm = VersionManager(project)
        current = project / "storyboards" / "scene_E1S01.png"
        current.parent.mkdir(parents=True, exist_ok=True)
        with pytest.raises(ValueError, match="版本文件路径非法"):
            vm.restore_version("storyboards", "E1S01", 1, current)
