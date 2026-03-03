from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.routers import versions


class _FakePM:
    def __init__(self):
        self.updated = []

    def get_project_path(self, project_name):
        from pathlib import Path

        return Path("/tmp") / project_name

    def update_project_character_sheet(self, *args):
        self.updated.append(("character", args))

    def update_clue_sheet(self, *args):
        self.updated.append(("clue", args))

    def load_project(self, project_name):
        return {"schema_version": 2}

    def find_item_reference(self, project_name, item_uid):
        return "episode_1.json", {"schema_version": 2, "content_mode": "narration"}, {"item_uid": item_uid}

    def get_current_asset_path(self, project_name, script_filename, item_uid, resource_type):
        from pathlib import Path

        relative_path = (
            f"storyboards/item_{item_uid}.png"
            if resource_type == "storyboards"
            else f"videos/item_{item_uid}.mp4"
        )
        return {}, {}, Path("/tmp") / project_name / relative_path, relative_path

    def update_item_asset(self, *args, **kwargs):
        self.updated.append(("scene", args, kwargs))


class _FakeVM:
    def __init__(self, project_path=None):
        self.project_path = project_path

    def get_versions(self, resource_type, resource_id):
        if resource_type == "bad":
            raise ValueError("bad type")
        return {
            "current_version": 1,
            "versions": [{"version": 1, "file": f"versions/{resource_type}/{resource_id}.png"}],
        }

    def restore_version(self, resource_type, resource_id, version, current_file):
        if version == 404:
            raise FileNotFoundError("missing")
        if version == 400:
            raise ValueError("bad")
        return {
            "restored_version": version,
            "current_version": version,
            "prompt": "p",
        }


class _StoryboardSyncPM:
    def __init__(self, project_path):
        self.project_path = project_path
        self.update_calls = []

    def get_project_path(self, project_name):
        return self.project_path

    def load_project(self, project_name):
        return {"schema_version": 2}

    def find_item_reference(self, project_name, item_uid):
        return "c.json", {"schema_version": 2, "content_mode": "narration"}, {"item_uid": item_uid}

    def get_current_asset_path(self, project_name, script_filename, item_uid, resource_type):
        relative_path = f"storyboards/item_{item_uid}.png"
        return {}, {}, self.project_path / relative_path, relative_path

    def update_item_asset(self, project_name, script_filename, item_uid, asset_type, asset_path):
        self.update_calls.append(script_filename)


def _client(monkeypatch):
    fake_pm = _FakePM()
    monkeypatch.setattr(versions, "get_project_manager", lambda: fake_pm)
    monkeypatch.setattr(versions, "get_version_manager", lambda project_name: _FakeVM())

    app = FastAPI()
    app.include_router(versions.router, prefix="/api/v1")
    return TestClient(app), fake_pm


class TestVersionsRouter:
    def test_get_versions_and_restore(self, monkeypatch):
        client, fake_pm = _client(monkeypatch)
        with client:
            get_resp = client.get("/api/v1/projects/demo/versions/characters/Alice")
            assert get_resp.status_code == 200
            assert get_resp.json()["current_version"] == 1

            restore_resp = client.post("/api/v1/projects/demo/versions/characters/Alice/restore/1")
            assert restore_resp.status_code == 200
            assert restore_resp.json()["current_version"] == 1
            assert any(item[0] == "character" for item in fake_pm.updated)

    def test_restore_error_mapping(self, monkeypatch):
        client, _ = _client(monkeypatch)
        with client:
            bad_type = client.get("/api/v1/projects/demo/versions/bad/Alice")
            assert bad_type.status_code == 400

            not_found = client.post("/api/v1/projects/demo/versions/characters/Alice/restore/404")
            assert not_found.status_code == 404

            bad_value = client.post("/api/v1/projects/demo/versions/characters/Alice/restore/400")
            assert bad_value.status_code == 400

            unsupported = client.post("/api/v1/projects/demo/versions/unknown/Alice/restore/1")
            assert unsupported.status_code == 400

    def test_storyboard_restore_syncs_scripts_with_error_tolerance(self, tmp_path, monkeypatch):
        project_path = tmp_path / "demo"
        scripts_dir = project_path / "scripts"
        scripts_dir.mkdir(parents=True)
        for name in ("a.json", "b.json", "c.json"):
            (scripts_dir / name).write_text("{}", encoding="utf-8")

        fake_pm = _StoryboardSyncPM(project_path)
        monkeypatch.setattr(versions, "get_project_manager", lambda: fake_pm)
        monkeypatch.setattr(versions, "get_version_manager", lambda project_name: _FakeVM())

        app = FastAPI()
        app.include_router(versions.router, prefix="/api/v1")
        with TestClient(app) as client:
            resp = client.post("/api/v1/projects/demo/versions/storyboards/E1S01/restore/1")
            assert resp.status_code == 200
            assert resp.json()["file_path"] == "storyboards/item_E1S01.png"

        assert fake_pm.update_calls == ["c.json"]

    def test_get_versions_unexpected_error_maps_to_500(self, monkeypatch):
        fake_pm = _FakePM()
        monkeypatch.setattr(versions, "get_project_manager", lambda: fake_pm)
        monkeypatch.setattr(
            versions,
            "get_version_manager",
            lambda project_name: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        app = FastAPI()
        app.include_router(versions.router, prefix="/api/v1")
        with TestClient(app) as client:
            resp = client.get("/api/v1/projects/demo/versions/characters/Alice")
            assert resp.status_code == 500
            assert "boom" in resp.json()["detail"]
