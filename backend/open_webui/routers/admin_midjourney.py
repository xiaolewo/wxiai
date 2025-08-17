"""
Midjourney 管理员功能路由
包含用户积分管理、系统统计等管理员专用功能
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from open_webui.models.users import Users
from open_webui.utils.auth import get_admin_user
from open_webui.models.midjourney import MJTask
from open_webui.utils.midjourney import (
    admin_add_credits_to_user,
    admin_deduct_credits_from_user,
    get_system_mj_stats,
    get_user_mj_stats,
    cleanup_old_tasks,
)

router = APIRouter(prefix="/admin/midjourney", tags=["admin", "midjourney"])


class CreditActionRequest(BaseModel):
    user_id: str
    amount: int
    reason: Optional[str] = ""


class UserSearchRequest(BaseModel):
    query: str
    limit: int = 10


# ======================== 用户积分管理 ========================


@router.post("/credits/add")
async def admin_add_user_credits(
    request: CreditActionRequest, admin: dict = Depends(get_admin_user)
):
    """管理员给用户充值积分"""
    try:
        # 验证用户存在
        user = Users.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_balance = admin_add_credits_to_user(
            admin["id"], request.user_id, request.amount, request.reason
        )

        return {
            "message": f"Added {request.amount} credits to user {user.name}",
            "new_balance": new_balance,
            "user_id": request.user_id,
            "amount": request.amount,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add credits: {str(e)}")


@router.post("/credits/deduct")
async def admin_deduct_user_credits(
    request: CreditActionRequest, admin: dict = Depends(get_admin_user)
):
    """管理员扣除用户积分"""
    try:
        # 验证用户存在
        user = Users.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_balance = admin_deduct_credits_from_user(
            admin["id"], request.user_id, request.amount, request.reason
        )

        return {
            "message": f"Deducted {request.amount} credits from user {user.name}",
            "new_balance": new_balance,
            "user_id": request.user_id,
            "amount": request.amount,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to deduct credits: {str(e)}"
        )


@router.get("/credits/users")
async def get_users_with_credits(
    page: int = 1, limit: int = 20, admin: dict = Depends(get_admin_user)
):
    """获取有积分记录的用户列表"""
    try:
        from open_webui.internal.db import get_db
        from open_webui.models.credits import Credit, CreditLog
        from open_webui.utils.midjourney import get_user_credit_balance
        from sqlalchemy import func, distinct

        with get_db() as db:
            # 获取有积分记录的用户 - 从系统积分表查询
            offset = (page - 1) * limit

            # 获取所有有积分的用户
            credit_users = (
                db.query(Credit)
                .order_by(Credit.updated_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            # 获取用户信息
            result = []
            for credit_user in credit_users:
                user = Users.get_user_by_id(credit_user.user_id)
                if user:
                    # 获取用户的积分交易数量
                    transaction_count = (
                        db.query(CreditLog)
                        .filter(CreditLog.user_id == credit_user.user_id)
                        .count()
                    )

                    result.append(
                        {
                            "user_id": credit_user.user_id,
                            "username": user.name,
                            "email": user.email,
                            "balance": float(credit_user.credit),
                            "transaction_count": transaction_count,
                            "last_activity": (
                                credit_user.updated_at
                                if hasattr(credit_user, "updated_at")
                                else None
                            ),
                        }
                    )

            total = db.query(Credit).count()

            return {"users": result, "total": total, "page": page, "limit": limit}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")


@router.get("/credits/history/{user_id}")
async def get_user_credit_history(
    user_id: str, page: int = 1, limit: int = 50, admin: dict = Depends(get_admin_user)
):
    """获取用户积分历史"""
    try:
        from open_webui.internal.db import get_db
        from open_webui.models.credits import CreditLog
        import time

        # 验证用户存在
        user = Users.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        with get_db() as db:
            # 从系统积分日志查询
            offset = (page - 1) * limit
            records = (
                db.query(CreditLog)
                .filter(CreditLog.user_id == user_id)
                .order_by(CreditLog.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

        return {
            "records": [
                {
                    "id": record.id,
                    "amount": float(record.credit) if record.credit else 0,
                    "balance": float(record.credit) if record.credit else 0,
                    "reason": record.detail.get("desc", "") if record.detail else "",
                    "task_id": (
                        record.detail.get("api_params", {}).get("task_id", None)
                        if record.detail
                        else None
                    ),
                    "created_at": (
                        time.strftime(
                            "%Y-%m-%dT%H:%M:%S", time.localtime(record.created_at)
                        )
                        if record.created_at
                        else None
                    ),
                }
                for record in records
            ],
            "user_info": {
                "user_id": user_id,
                "username": user.name,
                "email": user.email,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get credit history: {str(e)}"
        )


# ======================== 系统统计 ========================


@router.get("/stats/system")
async def get_mj_system_stats(admin: dict = Depends(get_admin_user)):
    """获取系统MJ统计"""
    try:
        stats = get_system_mj_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/stats/user/{user_id}")
async def get_user_mj_stats(user_id: str, admin: dict = Depends(get_admin_user)):
    """获取用户MJ统计"""
    try:
        # 验证用户存在
        user = Users.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        stats = get_user_mj_stats(user_id)
        stats["user_info"] = {
            "user_id": user_id,
            "username": user.name,
            "email": user.email,
        }

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user stats: {str(e)}"
        )


@router.get("/tasks/recent")
async def get_recent_tasks(
    limit: int = 50, status: Optional[str] = None, admin: dict = Depends(get_admin_user)
):
    """获取最近的任务列表"""
    try:
        from open_webui.internal.db import get_db

        with get_db() as db:
            query = db.query(MJTask).order_by(MJTask.created_at.desc())

            if status:
                query = query.filter(MJTask.status == status)

            tasks = query.limit(limit).all()

            result = []
            for task in tasks:
                user = Users.get_user_by_id(task.user_id)
                task_data = task.to_dict()
                task_data["username"] = user.name if user else "Unknown"
                result.append(task_data)

            return {"tasks": result}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent tasks: {str(e)}"
        )


# ======================== 系统维护 ========================


@router.post("/maintenance/cleanup")
async def cleanup_old_mj_tasks(days: int = 30, admin: dict = Depends(get_admin_user)):
    """清理旧任务记录"""
    try:
        if days < 7:
            raise HTTPException(
                status_code=400, detail="Cannot cleanup tasks newer than 7 days"
            )

        deleted_count = cleanup_old_tasks(days)

        return {
            "message": f"Cleaned up {deleted_count} tasks older than {days} days",
            "deleted_count": deleted_count,
            "days": days,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup tasks: {str(e)}"
        )


@router.post("/users/search")
async def search_users(
    request: UserSearchRequest, admin: dict = Depends(get_admin_user)
):
    """搜索用户"""
    try:
        from open_webui.utils.midjourney import get_user_credit_balance

        users = Users.search_users(request.query, request.limit)

        result = []
        for user in users:
            # 获取用户积分余额（使用系统积分）
            balance = get_user_credit_balance(user.id)

            result.append(
                {
                    "user_id": user.id,
                    "username": user.name,
                    "email": user.email,
                    "balance": balance,
                    "created_at": (
                        user.created_at.isoformat() if user.created_at else None
                    ),
                }
            )

        return {"users": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")


# ======================== 批量操作 ========================


class BatchCreditRequest(BaseModel):
    user_ids: List[str]
    amount: int
    reason: str


@router.post("/credits/batch/add")
async def batch_add_credits(
    request: BatchCreditRequest, admin: dict = Depends(get_admin_user)
):
    """批量给用户充值积分"""
    try:
        results = []

        for user_id in request.user_ids:
            try:
                user = Users.get_user_by_id(user_id)
                if not user:
                    results.append(
                        {
                            "user_id": user_id,
                            "success": False,
                            "error": "User not found",
                        }
                    )
                    continue

                new_balance = admin_add_credits_to_user(
                    admin["id"], user_id, request.amount, request.reason
                )

                results.append(
                    {
                        "user_id": user_id,
                        "username": user.name,
                        "success": True,
                        "new_balance": new_balance,
                        "amount": request.amount,
                    }
                )

            except Exception as e:
                results.append({"user_id": user_id, "success": False, "error": str(e)})

        success_count = len([r for r in results if r["success"]])

        return {
            "message": f"Successfully added credits to {success_count}/{len(request.user_ids)} users",
            "results": results,
            "success_count": success_count,
            "total_count": len(request.user_ids),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to batch add credits: {str(e)}"
        )
