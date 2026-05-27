"""
OAuth统一鉴权路由

使用统一错误处理和标准化响应格式。
"""
from fastapi import APIRouter, Query, Depends
from typing import Any
from loguru import logger

from utils.errors import ApiError, ErrorCode, NotFoundError, ValidationError
from utils.responses import success_response
from .providers import get_oauth_provider

router = APIRouter()


# TODO: Replace with real database dependency later
async def get_db():
    yield None


VALID_PLATFORMS = {"douyin", "kuaishou", "pinduoduo", "xianyu"}


@router.get("/authorize/{platform}")
async def authorize_shop(
    platform: str,
    shop_id: str = Query(..., description="店铺ID"),
    redirect_uri: str = Query(..., description="回调地址"),
):
    """获取平台授权URL"""
    if platform not in VALID_PLATFORMS:
        raise ValidationError(
            message=f"无效的平台: {platform}",
            detail=f"支持的平台: {', '.join(VALID_PLATFORMS)}",
        )

    if not shop_id.strip():
        raise ValidationError(message="店铺ID不能为空")

    if not redirect_uri.strip():
        raise ValidationError(message="回调地址不能为空")

    try:
        provider = get_oauth_provider(platform)
        url = await provider.get_authorization_url(shop_id, redirect_uri)
        return success_response(
            data={"authorization_url": url, "platform": platform, "shop_id": shop_id},
            message="授权URL获取成功",
        )
    except Exception as e:
        logger.error(f"获取授权URL失败 platform={platform}: {e}")
        raise ApiError(
            code=ErrorCode.ADAPTER_AUTH_FAILED,
            message=f"获取 {platform} 授权URL失败",
            detail=str(e),
        )


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(..., description="授权码"),
    state: str = Query(..., description="状态参数（通常包含shop_id）"),
    redirect_uri: str = Query(..., description="回调地址"),
    db: Any = Depends(get_db),
):
    """处理OAuth回调，交换token"""
    if platform not in VALID_PLATFORMS:
        raise ValidationError(
            message=f"无效的平台: {platform}",
            detail=f"支持的平台: {', '.join(VALID_PLATFORMS)}",
        )

    if not code.strip():
        raise ValidationError(message="授权码不能为空")

    try:
        provider = get_oauth_provider(platform)
        token_data = await provider.exchange_code(code, redirect_uri)

        # TODO: 保存token到数据库
        # await db.execute("INSERT INTO shop_auth_tokens ...", token_data)

        logger.info(f"OAuth回调成功 platform={platform} shop_id={state}")
        return success_response(
            data={
                "platform": platform,
                "shop_id": state,
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in"),
            },
            message="授权成功",
        )
    except Exception as e:
        logger.error(f"OAuth回调处理失败 platform={platform}: {e}")
        raise ApiError(
            code=ErrorCode.ADAPTER_AUTH_FAILED,
            message=f"{platform} 授权回调处理失败",
            detail=str(e),
        )


@router.post("/refresh/{platform}")
async def refresh_shop_token(
    platform: str,
    shop_id: str = Query(..., description="店铺ID"),
    refresh_token: str = Query(..., description="刷新令牌"),
    db: Any = Depends(get_db),
):
    """刷新过期的access_token"""
    if platform not in VALID_PLATFORMS:
        raise ValidationError(
            message=f"无效的平台: {platform}",
            detail=f"支持的平台: {', '.join(VALID_PLATFORMS)}",
        )

    if not refresh_token.strip():
        raise ValidationError(message="刷新令牌不能为空")

    try:
        provider = get_oauth_provider(platform)
        new_token_data = await provider.refresh_token(refresh_token)

        # TODO: 更新数据库中的token
        # await db.execute("UPDATE shop_auth_tokens SET ... WHERE shop_id = ...", new_token_data)

        logger.info(f"Token刷新成功 platform={platform} shop_id={shop_id}")
        return success_response(
            data={
                "platform": platform,
                "shop_id": shop_id,
                "token_type": new_token_data.get("token_type", "bearer"),
                "expires_in": new_token_data.get("expires_in"),
            },
            message="Token刷新成功",
        )
    except Exception as e:
        logger.error(f"Token刷新失败 platform={platform}: {e}")
        raise ApiError(
            code=ErrorCode.ADAPTER_AUTH_FAILED,
            message=f"{platform} Token刷新失败",
            detail=str(e),
        )
