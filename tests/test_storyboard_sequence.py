from pathlib import Path

from lib.storyboard_sequence import (
    build_storyboard_dependency_plan,
    get_storyboard_items,
    resolve_previous_storyboard_path,
)


class TestStoryboardSequence:
    def test_get_storyboard_items_supports_narration_and_drama(self):
        narration = {"content_mode": "narration", "segments": [{"item_uid": "itm_111111111111", "segment_id": "E1S01"}]}
        drama = {"content_mode": "drama", "scenes": [{"item_uid": "itm_222222222222", "scene_id": "E1S01"}]}

        narration_items = get_storyboard_items(narration)
        drama_items = get_storyboard_items(drama)

        assert narration_items[1:] == (
            "item_uid",
            "characters_in_segment",
            "clues_in_segment",
        )
        assert drama_items[1:] == (
            "item_uid",
            "characters_in_scene",
            "clues_in_scene",
        )

    def test_resolve_previous_storyboard_path_respects_first_item_and_segment_break(self, tmp_path: Path):
        project_path = tmp_path / "demo"
        (project_path / "storyboards").mkdir(parents=True)
        previous_path = project_path / "storyboards" / "item_itm_111111111111.png"
        previous_path.write_bytes(b"png")

        items = [
            {"item_uid": "itm_111111111111", "segment_id": "E1S01", "segment_break": False},
            {"item_uid": "itm_222222222222", "segment_id": "E1S02", "segment_break": False},
            {"item_uid": "itm_333333333333", "segment_id": "E1S03", "segment_break": True},
        ]

        assert resolve_previous_storyboard_path(project_path, items, "item_uid", "itm_111111111111") is None
        assert resolve_previous_storyboard_path(project_path, items, "item_uid", "itm_222222222222") == previous_path
        assert resolve_previous_storyboard_path(project_path, items, "item_uid", "itm_333333333333") is None

    def test_resolve_previous_storyboard_path_does_not_backtrack(self, tmp_path: Path):
        project_path = tmp_path / "demo"
        (project_path / "storyboards").mkdir(parents=True)
        (project_path / "storyboards" / "item_itm_111111111111.png").write_bytes(b"png")

        items = [
            {"item_uid": "itm_111111111111", "segment_id": "E1S01", "segment_break": False},
            {"item_uid": "itm_222222222222", "segment_id": "E1S02", "segment_break": False},
            {"item_uid": "itm_333333333333", "segment_id": "E1S03", "segment_break": False},
        ]

        assert resolve_previous_storyboard_path(project_path, items, "item_uid", "itm_333333333333") is None

    def test_build_storyboard_dependency_plan_groups_contiguous_ranges(self):
        items = [
            {"item_uid": "itm_111111111111", "segment_id": "E1S01", "segment_break": False},
            {"item_uid": "itm_222222222222", "segment_id": "E1S02", "segment_break": False},
            {"item_uid": "itm_333333333333", "segment_id": "E1S03", "segment_break": True},
            {"item_uid": "itm_444444444444", "segment_id": "E1S04", "segment_break": False},
            {"item_uid": "itm_555555555555", "segment_id": "E1S05", "segment_break": False},
        ]

        plans = build_storyboard_dependency_plan(
            items,
            "item_uid",
            ["itm_111111111111", "itm_222222222222", "itm_333333333333", "itm_444444444444"],
            "episode_1.json",
        )

        assert [(plan.resource_id, plan.dependency_resource_id, plan.dependency_index) for plan in plans] == [
            ("itm_111111111111", None, 0),
            ("itm_222222222222", "itm_111111111111", 1),
            ("itm_333333333333", None, 0),
            ("itm_444444444444", "itm_333333333333", 1),
        ]
        assert plans[0].dependency_group == plans[1].dependency_group
        assert plans[2].dependency_group == plans[3].dependency_group
        assert plans[0].dependency_group != plans[2].dependency_group

    def test_build_storyboard_dependency_plan_starts_new_group_when_selection_has_gap(self):
        items = [
            {"item_uid": "itm_111111111111", "scene_id": "E1S01", "segment_break": False},
            {"item_uid": "itm_222222222222", "scene_id": "E1S02", "segment_break": False},
            {"item_uid": "itm_333333333333", "scene_id": "E1S03", "segment_break": False},
            {"item_uid": "itm_444444444444", "scene_id": "E1S04", "segment_break": False},
        ]

        plans = build_storyboard_dependency_plan(
            items,
            "item_uid",
            ["itm_111111111111", "itm_333333333333", "itm_444444444444"],
            "episode_1.json",
        )

        assert [(plan.resource_id, plan.dependency_resource_id) for plan in plans] == [
            ("itm_111111111111", None),
            ("itm_333333333333", None),
            ("itm_444444444444", "itm_333333333333"),
        ]
