"""
海螺（MiniMax Hailuo）视频生成 API 路由
"""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse

from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.hailuo import (
    HailuoConfig,
    HailuoTask,
    HailuoConfigForm,
    HailuoGenerateRequest,
)
from open_webui.utils.hailuo import (
    HailuoApiClient,
    monitor_hailuo_task,
    process_hailuo_generation,
)


router = APIRouter(prefix="/hailuo", tags=["hailuo"])
logger = logging.getLogger(__name__)


@router.get("/config")
async def get_hailuo_config_admin(user=Depends(get_admin_user)):
    cfg = HailuoConfig.get_config()
    if not cfg:
        # default preview
        tmp = HailuoConfig()
        return {
            "enabled": False,
            "base_url": tmp.base_url,
            "api_key": "",
            "default_model": tmp.default_model,
            "default_duration": tmp.default_duration,
            "default_resolution": tmp.default_resolution,
            "prompt_optimizer": tmp.prompt_optimizer,
            "max_concurrent_tasks": tmp.max_concurrent_tasks,
            "task_timeout_ms": tmp.task_timeout_ms,
            "query_interval_ms": tmp.query_interval_ms,
            "model_credits_config": tmp.get_default_credits_config(),
        }
    return {
        "enabled": cfg.enabled,
        "base_url": cfg.base_url,
        "api_key": cfg.api_key,
        "default_model": cfg.default_model,
        "default_duration": cfg.default_duration,
        "default_resolution": cfg.default_resolution,
        "prompt_optimizer": cfg.prompt_optimizer,
        "max_concurrent_tasks": cfg.max_concurrent_tasks,
        "task_timeout_ms": cfg.task_timeout_ms,
        "query_interval_ms": cfg.query_interval_ms,
        "model_credits_config": cfg.model_credits_config
        or cfg.get_default_credits_config(),
    }


@router.get("/config/user")
async def get_hailuo_config_user(user=Depends(get_verified_user)):
    cfg = HailuoConfig.get_config()
    if not cfg:
        tmp = HailuoConfig()
        return {
            "enabled": False,
            "default_model": tmp.default_model,
            "default_duration": tmp.default_duration,
            "default_resolution": tmp.default_resolution,
            "prompt_optimizer": tmp.prompt_optimizer,
        }
    return {
        "enabled": cfg.enabled,
        "default_model": cfg.default_model,
        "default_duration": cfg.default_duration,
        "default_resolution": cfg.default_resolution,
        "prompt_optimizer": cfg.prompt_optimizer,
    }


@router.post("/config")
async def update_hailuo_config(form: HailuoConfigForm, user=Depends(get_admin_user)):
    data = form.dict()
    if data.get("enabled") and (not data.get("base_url") or not data.get("api_key")):
        raise HTTPException(status_code=400, detail="启用时需要提供Base URL和API Key")
    cfg = HailuoConfig.save_config(data)
    return {
        "success": True,
        "config": {
            "enabled": cfg.enabled,
            "base_url": cfg.base_url,
            "default_model": cfg.default_model,
            "default_duration": cfg.default_duration,
            "default_resolution": cfg.default_resolution,
            "prompt_optimizer": cfg.prompt_optimizer,
            "max_concurrent_tasks": cfg.max_concurrent_tasks,
            "task_timeout_ms": cfg.task_timeout_ms,
            "query_interval_ms": cfg.query_interval_ms,
            "model_credits_config": cfg.model_credits_config
            or cfg.get_default_credits_config(),
        },
    }


@router.get("/test")
async def test_hailuo_connection(user=Depends(get_admin_user)):
    cfg = HailuoConfig.get_config()
    if not cfg or not cfg.enabled:
        return {"enabled": False, "status": "disabled"}
    try:
        client = HailuoApiClient(cfg)
        # basic ping via harmless GET (query non-existing id)
        res = await client.query_task("0")
        return {"enabled": True, "status": "ok", "http_ok": True}
    except Exception as e:
        return {"enabled": True, "status": f"error: {e}"}


@router.post("/generate")
async def generate_hailuo_video(
    request: HailuoGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    cfg = HailuoConfig.get_config()
    if not cfg or not cfg.enabled:
        raise HTTPException(status_code=400, detail="海螺服务未启用")

    try:
        task = await process_hailuo_generation(user.id, request)
        background_tasks.add_task(monitor_hailuo_task, task.id, cfg)
        return {"success": True, "task_id": task.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Hailuo task submission failed: %s", e)
        return JSONResponse(
            status_code=200,
            content={"success": False, "error": str(e) or "海螺任务提交失败"},
        )


@router.get("/task/{task_id}")
async def get_hailuo_task(task_id: str, user=Depends(get_verified_user)):
    t = HailuoTask.get_task_by_id(task_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    return t.to_dict()


@router.get("/credits")
async def get_hailuo_credits(user=Depends(get_verified_user)):
    try:
        from open_webui.models.credits import Credits

        credit_model = Credits.get_credit_by_user_id(user.id)
        balance = float(credit_model.credit) if credit_model else 0.0
        return {"balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_hailuo_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
):
    try:
        from sqlalchemy import desc
        from open_webui.internal.db import get_db

        with get_db() as db:
            q = db.query(HailuoTask).filter(HailuoTask.user_id == user.id)
            total = q.count()
            items = (
                q.order_by(desc(HailuoTask.created_at))
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )
            return {
                "data": [i.to_dict() for i in items],
                "total": total,
                "page": page,
                "limit": limit,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/task/{task_id}")
async def delete_hailuo_task(task_id: str, user=Depends(get_verified_user)):
    try:
        t = HailuoTask.get_task_by_id(task_id)
        if not t:
            raise HTTPException(status_code=404, detail="任务不存在")
        if t.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问")
        from open_webui.internal.db import get_db

        with get_db() as db:
            db.delete(t)
            db.commit()
        return {"message": "任务删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/user")
async def get_hailuo_user_stats(user=Depends(get_verified_user)):
    try:
        from open_webui.internal.db import get_db
        from sqlalchemy import func

        with get_db() as db:
            total = (
                db.query(func.count(HailuoTask.id))
                .filter(HailuoTask.user_id == user.id)
                .scalar()
                or 0
            )
            success = (
                db.query(func.count(HailuoTask.id))
                .filter(HailuoTask.user_id == user.id, HailuoTask.status == "succeed")
                .scalar()
                or 0
            )
            today = (
                db.query(func.count(HailuoTask.id))
                .filter(
                    func.date(HailuoTask.created_at) == func.date(func.now()),
                    HailuoTask.user_id == user.id,
                )
                .scalar()
                or 0
            )
            spent = (
                db.query(func.coalesce(func.sum(HailuoTask.credits_cost), 0))
                .filter(HailuoTask.user_id == user.id)
                .scalar()
                or 0
            )
            balance = 0
            try:
                from open_webui.models.credits import Credits

                c = Credits.get_user_credits(user.id)
                balance = int(c.credit) if c else 0
            except Exception:
                pass
            return {
                "total_tasks": total,
                "success_tasks": success,
                "today_tasks": today,
                "success_rate": round((success / total * 100), 2) if total else 0,
                "credit_balance": balance,
                "total_credits_spent": int(spent),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/cleanup")
async def admin_cleanup_hailuo(days: int = 30, user=Depends(get_admin_user)):
    try:
        from datetime import timedelta
        from open_webui.internal.db import get_db
        from sqlalchemy import func

        with get_db() as db:
            cutoff = func.datetime(func.now(), f"-{int(days)} days")
            # SQLite compatible generic; for Postgres replace with NOW() - interval
            deleted = (
                db.query(HailuoTask).filter(HailuoTask.created_at < cutoff).delete()
            )
            db.commit()
            return {"message": f"清理了 {deleted} 个旧任务（超过 {days} 天）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
