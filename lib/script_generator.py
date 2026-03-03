"""
script_generator.py - 剧本生成器

读取 Step 1/2 的 Markdown 中间文件，调用 Gemini 生成最终 JSON 剧本
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import ValidationError

from lib.gemini_client import GeminiClient
from lib.prompt_builders_script import (
    build_drama_prompt,
    build_narration_prompt,
)
from lib.script_models import (
    DramaEpisodeScript,
    NarrationEpisodeScript,
)
from lib.script_item_service import SCHEMA_VERSION, create_generated_assets, generate_item_uid

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """
    剧本生成器

    读取 Step 1/2 的 Markdown 中间文件，调用 Gemini 生成最终 JSON 剧本
    """

    MODEL = "gemini-3-flash-preview"

    def __init__(self, project_path: Union[str, Path]):
        """
        初始化生成器

        Args:
            project_path: 项目目录路径，如 projects/test0205
        """
        self.project_path = Path(project_path)
        self.client = GeminiClient()

        # 加载 project.json
        self.project_json = self._load_project_json()
        self.content_mode = self.project_json.get("content_mode", "narration")

    def generate(
        self,
        episode: int,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        生成剧集剧本

        Args:
            episode: 剧集编号
            output_path: 输出路径，默认为 scripts/episode_{episode}.json

        Returns:
            生成的 JSON 文件路径
        """
        # 1. 加载中间文件
        step1_md = self._load_step1(episode)

        # 2. 提取角色和线索（从 project.json）
        characters = self.project_json.get("characters", {})
        clues = self.project_json.get("clues", {})

        # 3. 构建 Prompt
        if self.content_mode == "narration":
            prompt = build_narration_prompt(
                project_overview=self.project_json.get("overview", {}),
                style=self.project_json.get("style", ""),
                style_description=self.project_json.get("style_description", ""),
                characters=characters,
                clues=clues,
                segments_md=step1_md,
            )
            schema = NarrationEpisodeScript.model_json_schema()
        else:
            prompt = build_drama_prompt(
                project_overview=self.project_json.get("overview", {}),
                style=self.project_json.get("style", ""),
                style_description=self.project_json.get("style_description", ""),
                characters=characters,
                clues=clues,
                scenes_md=step1_md,
            )
            schema = DramaEpisodeScript.model_json_schema()

        # 4. 调用 Gemini API
        logger.info("正在生成第 %d 集剧本...", episode)
        response_text = self.client.generate_text(
            prompt=prompt,
            model=self.MODEL,
            response_schema=schema,
        )

        # 5. 解析并验证响应
        script_data = self._parse_response(response_text, episode)
        self._validate_contract(script_data, episode)
        script_data = self._assign_v2_fields(script_data)

        # 6. 补充元数据
        script_data = self._add_metadata(script_data, episode)

        # 7. 保存文件
        if output_path is None:
            output_path = self.project_path / "scripts" / f"episode_{episode}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

        logger.info("剧本已保存至 %s", output_path)
        return output_path

    def build_prompt(self, episode: int) -> str:
        """
        构建 Prompt（用于 dry-run 模式）

        Args:
            episode: 剧集编号

        Returns:
            构建好的 Prompt 字符串
        """
        step1_md = self._load_step1(episode)
        characters = self.project_json.get("characters", {})
        clues = self.project_json.get("clues", {})

        if self.content_mode == "narration":
            return build_narration_prompt(
                project_overview=self.project_json.get("overview", {}),
                style=self.project_json.get("style", ""),
                style_description=self.project_json.get("style_description", ""),
                characters=characters,
                clues=clues,
                segments_md=step1_md,
            )
        else:
            return build_drama_prompt(
                project_overview=self.project_json.get("overview", {}),
                style=self.project_json.get("style", ""),
                style_description=self.project_json.get("style_description", ""),
                characters=characters,
                clues=clues,
                scenes_md=step1_md,
            )

    def _load_project_json(self) -> dict:
        """加载 project.json"""
        path = self.project_path / "project.json"
        if not path.exists():
            raise FileNotFoundError(f"未找到 project.json: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_step1(self, episode: int) -> str:
        """加载 Step 1 的 Markdown 文件，支持两种文件命名"""
        drafts_path = self.project_path / "drafts" / f"episode_{episode}"
        if self.content_mode == "narration":
            primary_path = drafts_path / "step1_segments.md"
            fallback_path = drafts_path / "step1_normalized_script.md"
        else:
            primary_path = drafts_path / "step1_normalized_script.md"
            fallback_path = drafts_path / "step1_segments.md"

        if not primary_path.exists():
            if fallback_path.exists():
                logger.warning("未找到 Step 1 文件: %s，改用 %s", primary_path, fallback_path)
                primary_path = fallback_path
            else:
                raise FileNotFoundError(f"未找到 Step 1 文件: {primary_path}")

        with open(primary_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_response(self, response_text: str, episode: int) -> dict:
        """
        解析并验证 Gemini 响应

        Args:
            response_text: API 返回的 JSON 文本
            episode: 剧集编号

        Returns:
            验证后的剧本数据字典
        """
        # 清理可能的 markdown 包装
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # 解析 JSON
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {e}")

        # Pydantic 验证
        try:
            if self.content_mode == "narration":
                validated = NarrationEpisodeScript.model_validate(data)
            else:
                validated = DramaEpisodeScript.model_validate(data)
            return validated.model_dump()
        except ValidationError as e:
            raise ValueError(f"Pydantic 校验失败: {e}") from e

    @staticmethod
    def _parse_markdown_table(markdown_text: str) -> list[dict[str, str]]:
        headers: list[str] | None = None
        rows: list[dict[str, str]] = []
        for raw_line in markdown_text.splitlines():
            line = raw_line.strip()
            if not line.startswith("|"):
                continue
            parts = [part.strip() for part in line.strip("|").split("|")]
            if not parts or all(not part for part in parts):
                continue
            if headers is None:
                headers = parts
                continue
            if all(set(part) <= {"-", ":"} for part in parts):
                continue
            if len(parts) < len(headers):
                parts.extend([""] * (len(headers) - len(parts)))
            rows.append(dict(zip(headers, parts)))
        return rows

    @staticmethod
    def _read_duration_seconds(value: Any) -> int:
        text = str(value or "").strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        if not digits:
            raise ValueError(f"无法解析 duration_seconds: {value}")
        return int(digits)

    @staticmethod
    def _read_segment_break(value: Any) -> bool:
        text = str(value or "").strip().lower()
        return text not in {"", "-", "否", "false", "0", "no", "n"}

    def _load_scene_manifest(self, episode: int) -> dict[str, Any]:
        manifest_path = (
            self.project_path
            / "drafts"
            / f"episode_{episode}"
            / "step2_scene_manifest.json"
        )
        if not manifest_path.exists():
            raise FileNotFoundError(f"未找到 Scene Manifest: {manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _extract_narration_contract(self, episode: int) -> list[dict[str, Any]]:
        rows = self._parse_markdown_table(self._load_step1(episode))
        contract: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            segment_id = (
                row.get("segment_id")
                or row.get("片段ID")
                or row.get("片段编号")
                or row.get("片段")
                or row.get("Segment ID")
            )
            novel_text = row.get("novel_text") or row.get("原文") or row.get("文本")
            duration_raw = row.get("duration_seconds") or row.get("时长")
            segment_break_raw = row.get("segment_break")
            if segment_break_raw is None:
                segment_break_raw = row.get("segment break")

            if not segment_id or novel_text is None or duration_raw is None:
                raise ValueError(f"step1_segments.md 第 {index + 1} 行缺少必要列")

            contract.append(
                {
                    "segment_id": str(segment_id).strip(),
                    "duration_seconds": self._read_duration_seconds(duration_raw),
                    "segment_break": self._read_segment_break(segment_break_raw),
                    "novel_text": str(novel_text),
                }
            )
        if not contract:
            raise ValueError("step1_segments.md 未解析出任何片段")
        return contract

    def _extract_drama_contract(self, episode: int) -> list[dict[str, Any]]:
        manifest = self._load_scene_manifest(episode)
        scenes = manifest.get("scenes", manifest if isinstance(manifest, list) else [])
        if not isinstance(scenes, list) or not scenes:
            raise ValueError("step2_scene_manifest.json 未包含 scenes")
        contract: list[dict[str, Any]] = []
        for index, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                raise ValueError(f"scene manifest 第 {index + 1} 项格式错误")
            scene_id = scene.get("scene_id")
            duration = scene.get("duration_seconds")
            scene_type = scene.get("scene_type")
            if not scene_id or duration is None or scene_type is None:
                raise ValueError(f"scene manifest 第 {index + 1} 项缺少必要字段")
            contract.append(
                {
                    "scene_id": str(scene_id).strip(),
                    "duration_seconds": int(duration),
                    "segment_break": bool(scene.get("segment_break")),
                    "scene_type": str(scene_type),
                }
            )
        return contract

    def _validate_contract(self, script_data: dict[str, Any], episode: int) -> None:
        if self.content_mode == "narration":
            contract = self._extract_narration_contract(episode)
            segments = script_data.get("segments", [])
            if len(segments) != len(contract):
                raise ValueError("narration 片段数量与 step1_segments.md 不一致")
            for index, (segment, expected) in enumerate(zip(segments, contract, strict=True), start=1):
                actual = {
                    "segment_id": segment.get("segment_id"),
                    "duration_seconds": segment.get("duration_seconds"),
                    "segment_break": segment.get("segment_break"),
                    "novel_text": segment.get("novel_text"),
                }
                if actual != expected:
                    raise ValueError(f"narration 契约校验失败：第 {index} 个片段不一致")
        else:
            contract = self._extract_drama_contract(episode)
            scenes = script_data.get("scenes", [])
            if len(scenes) != len(contract):
                raise ValueError("drama 场景数量与 step2_scene_manifest.json 不一致")
            for index, (scene, expected) in enumerate(zip(scenes, contract, strict=True), start=1):
                actual = {
                    "scene_id": scene.get("scene_id"),
                    "duration_seconds": scene.get("duration_seconds"),
                    "segment_break": scene.get("segment_break"),
                    "scene_type": scene.get("scene_type"),
                }
                if actual != expected:
                    raise ValueError(f"drama 契约校验失败：第 {index} 个场景不一致")

    def _assign_v2_fields(self, script_data: dict[str, Any]) -> dict[str, Any]:
        result = dict(script_data)
        result["schema_version"] = SCHEMA_VERSION
        items_key = "segments" if self.content_mode == "narration" else "scenes"
        items = result.get(items_key, [])
        if not isinstance(items, list):
            return result
        for item in items:
            if not isinstance(item, dict):
                continue
            item["item_uid"] = str(item.get("item_uid") or generate_item_uid())
            item["generated_assets"] = create_generated_assets()
        return result

    def _add_metadata(self, script_data: dict, episode: int) -> dict:
        """
        补充剧本元数据

        Args:
            script_data: 剧本数据
            episode: 剧集编号

        Returns:
            补充元数据后的剧本数据
        """
        # 确保基本字段存在
        script_data.setdefault("episode", episode)
        script_data.setdefault("content_mode", self.content_mode)
        script_data.setdefault("schema_version", SCHEMA_VERSION)

        # 添加小说信息
        if "novel" not in script_data:
            script_data["novel"] = {
                "title": self.project_json.get("title", ""),
                "chapter": f"第{episode}集",
                "source_file": "",
            }

        # 添加时间戳
        now = datetime.now().isoformat()
        script_data.setdefault("metadata", {})
        script_data["metadata"]["created_at"] = now
        script_data["metadata"]["updated_at"] = now
        script_data["metadata"]["generator"] = self.MODEL

        # 计算统计信息
        if self.content_mode == "narration":
            segments = script_data.get("segments", [])
            script_data["metadata"]["total_segments"] = len(segments)
            script_data["duration_seconds"] = sum(
                s.get("duration_seconds", 4) for s in segments
            )
        else:
            scenes = script_data.get("scenes", [])
            script_data["metadata"]["total_scenes"] = len(scenes)
            script_data["duration_seconds"] = sum(
                s.get("duration_seconds", 8) for s in scenes
            )

        return script_data
