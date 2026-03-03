"""
版本管理 API 路由

处理版本查询和还原请求。
"""

import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

from lib import PROJECT_ROOT
from lib.project_change_hints import project_change_source
from lib.project_manager import ProjectManager
from lib.script_item_service import MigrationRequiredError, ensure_schema_v2
from lib.version_manager import VersionManager

router = APIRouter()

# 初始化项目管理器
pm = ProjectManager(PROJECT_ROOT / "projects")


def get_project_manager() -> ProjectManager:
    return pm


def get_version_manager(project_name: str) -> VersionManager:
    """获取项目的版本管理器"""
    project_path = get_project_manager().get_project_path(project_name)
    return VersionManager(project_path)


# ==================== 版本查询 ====================

@router.get("/projects/{project_name}/versions/{resource_type}/{resource_id}")
async def get_versions(
    project_name: str,
    resource_type: str,
    resource_id: str
):
    """
    获取资源的所有版本列表

    Args:
        project_name: 项目名称
        resource_type: 资源类型 (storyboards, videos, characters, clues)
        resource_id: 资源 ID
    """
    try:
        vm = get_version_manager(project_name)
        if resource_type in {"storyboards", "videos"}:
            manager = get_project_manager()
            script_file, script, _ = manager.find_item_reference(project_name, resource_id)
            project = manager.load_project(project_name)
            ensure_schema_v2(script, project)
        versions_info = vm.get_versions(resource_type, resource_id)

        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            **versions_info
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("请求处理失败")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 版本还原 ====================

@router.post("/projects/{project_name}/versions/{resource_type}/{resource_id}/restore/{version}")
async def restore_version(
    project_name: str,
    resource_type: str,
    resource_id: str,
    version: int
):
    """
    切换到指定版本

    会将指定版本复制到当前路径，并把当前版本指针切换到该版本。

    Args:
        project_name: 项目名称
        resource_type: 资源类型
        resource_id: 资源 ID
        version: 要还原的版本号
    """
    try:
        vm = get_version_manager(project_name)
        manager = get_project_manager()
        project_path = manager.get_project_path(project_name)

        # 确定当前文件路径
        if resource_type == "storyboards":
            script_file, script, _ = manager.find_item_reference(project_name, resource_id)
            project = manager.load_project(project_name)
            ensure_schema_v2(script, project)
            _, _, current_file, file_path = manager.get_current_asset_path(
                project_name,
                script_file,
                resource_id,
                "storyboards",
            )
        elif resource_type == "videos":
            script_file, script, _ = manager.find_item_reference(project_name, resource_id)
            project = manager.load_project(project_name)
            ensure_schema_v2(script, project)
            _, _, current_file, file_path = manager.get_current_asset_path(
                project_name,
                script_file,
                resource_id,
                "videos",
            )
        elif resource_type == "characters":
            current_file = project_path / "characters" / f"{resource_id}.png"
            file_path = f"characters/{resource_id}.png"
        elif resource_type == "clues":
            current_file = project_path / "clues" / f"{resource_id}.png"
            file_path = f"clues/{resource_id}.png"
        else:
            raise HTTPException(status_code=400, detail=f"不支持的资源类型: {resource_type}")

        # 执行还原
        result = vm.restore_version(
            resource_type=resource_type,
            resource_id=resource_id,
            version=version,
            current_file=current_file
        )

        # 同步元数据，确保引用指向统一的 PNG（避免 jpg/png 不一致导致 UI 仍显示旧图）
        if resource_type == "characters":
            try:
                with project_change_source("webui"):
                    get_project_manager().update_project_character_sheet(project_name, resource_id, file_path)
            except KeyError:
                pass
        elif resource_type == "clues":
            try:
                with project_change_source("webui"):
                    get_project_manager().update_clue_sheet(project_name, resource_id, file_path)
            except KeyError:
                pass
        elif resource_type == "storyboards":
            with project_change_source("webui"):
                get_project_manager().update_item_asset(
                    project_name=project_name,
                    script_filename=script_file,
                    item_uid=resource_id,
                    asset_type="storyboard_image",
                    asset_path=file_path,
                )
        elif resource_type == "videos":
            with project_change_source("webui"):
                get_project_manager().update_item_asset(
                    project_name=project_name,
                    script_filename=script_file,
                    item_uid=resource_id,
                    asset_type="video_clip",
                    asset_path=file_path,
                )

        return {
            "success": True,
            **result,
            "file_path": file_path,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MigrationRequiredError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("请求处理失败")
        raise HTTPException(status_code=500, detail=str(e))
