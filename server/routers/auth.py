"""
认证 API 路由

提供 OAuth2 登录和 token 验证接口。
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from lib.db import async_session_factory
from lib.db.models.user import User
from server.auth import CurrentUser, check_credentials, create_token
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 响应模型 ====================


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    language: str = "zh"


class VerifyResponse(BaseModel):
    valid: bool
    username: str
    language: str = "zh"


class LanguageRequest(BaseModel):
    language: str

SUPPORTED_LANGUAGES = {"zh", "en", "vi"}


# ==================== 路由 ====================


@router.post("/auth/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """用户登录

    使用 OAuth2 标准表单格式验证凭据，成功返回 access_token。
    """
    if not check_credentials(form_data.username, form_data.password):
        logger.warning("登录失败: 用户名或密码错误 (用户: %s)", form_data.username)
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token(form_data.username)
    logger.info("用户登录成功: %s", form_data.username)

    # Fetch user language preference from DB
    language = "zh"
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(User.language).where(User.username == form_data.username)
            )
            row = result.scalar_one_or_none()
            if row:
                language = row
    except Exception:
        logger.debug("Failed to fetch user language, using default")

    return TokenResponse(access_token=token, token_type="bearer", language=language)


@router.get("/auth/verify", response_model=VerifyResponse)
async def verify(
    current_user: CurrentUser,
):
    """验证 token 有效性

    使用 OAuth2 Bearer token 依赖自动提取和验证 token。
    """
    language = "zh"
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(User.language).where(User.username == current_user.sub)
            )
            row = result.scalar_one_or_none()
            if row:
                language = row
    except Exception:
        pass
    return VerifyResponse(valid=True, username=current_user.sub, language=language)


@router.patch("/auth/language")
async def update_language(
    body: LanguageRequest,
    current_user: CurrentUser,
):
    """Update user language preference."""
    if body.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {body.language}")

    async with async_session_factory() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(User.username == current_user.sub)
                .values(language=body.language)
            )
    return {"ok": True, "language": body.language}
