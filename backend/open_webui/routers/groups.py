import os
from pathlib import Path
from typing import Optional
import logging

from open_webui.models.users import Users
from open_webui.models.groups import (
    Groups,
    GroupForm,
    GroupUpdateForm,
    GroupResponse,
    GroupAdminForm,
)
from open_webui.models.credits import Credits

from open_webui.config import CACHE_DIR
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, Request, status

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.env import SRC_LOG_LEVELS


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()

############################
# GetFunctions
############################


@router.get("/", response_model=list[GroupResponse])
async def get_groups(user=Depends(get_verified_user)):
    if user.role == "admin":
        return Groups.get_groups()
    else:
        return Groups.get_groups_by_member_id(user.id)


############################
# CreateNewGroup
############################


@router.post("/create", response_model=Optional[GroupResponse])
async def create_new_group(form_data: GroupForm, user=Depends(get_admin_user)):
    try:
        group = Groups.insert_new_group(user.id, form_data)
        if group:
            return group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error creating group"),
            )
    except Exception as e:
        log.exception(f"Error creating a new group: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# GetGroupById
############################


@router.get("/id/{id}", response_model=Optional[GroupResponse])
async def get_group_by_id(id: str, user=Depends(get_admin_user)):
    group = Groups.get_group_by_id(id)
    if group:
        return group
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# SetGroupAdmin
############################


@router.post("/id/{id}/set-admin", response_model=Optional[GroupResponse])
async def set_group_admin(
    id: str, form_data: GroupAdminForm, user=Depends(get_admin_user)
):
    """设置权限组管理员"""
    try:
        # 验证管理员ID是否有效
        admin_user = Users.get_user_by_id(form_data.admin_id)
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Invalid admin user ID"),
            )
        
        # 设置管理员并确保该用户只在这一个组内
        group = Groups.set_group_admin_by_id(id, form_data.admin_id)
        Groups.ensure_user_in_single_group(form_data.admin_id, id)
        
        if group:
            return group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error setting group admin"),
            )
    except Exception as e:
        log.exception(f"Error setting group admin for group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# GetGroupAdminCredit
############################


@router.get("/admin-credit", response_model=dict)
async def get_group_admin_credit(user=Depends(get_verified_user)):
    """获取用户所在权限组管理员的积分"""
    try:
        # 获取用户所在的权限组
        group = Groups.get_user_group(user.id)
        
        # 如果用户不在任何组内或组内没有设置管理员
        if not group or not group.admin_id:
            # 返回用户自己的积分
            user_credit = Credits.get_credit_by_user_id(user.id)
            return {
                "user_credit": user_credit.credit if user_credit else 0,
                "admin_credit": None,
                "admin_id": None,
                "admin_name": None,
                "group_id": None,
                "group_name": None,
            }
        
        # 获取管理员信息
        admin_user = Users.get_user_by_id(group.admin_id)
        admin_credit = Credits.get_credit_by_user_id(group.admin_id)
        user_credit = Credits.get_credit_by_user_id(user.id)
        
        return {
            "user_credit": user_credit.credit if user_credit else 0,
            "admin_credit": admin_credit.credit if admin_credit else 0,
            "admin_id": admin_user.id,
            "admin_name": admin_user.name,
            "group_id": group.id,
            "group_name": group.name,
        }
    except Exception as e:
        log.exception(f"Error getting group admin credit: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# UpdateGroupById - 修改现有方法确保用户只在一个组内
############################


@router.post("/id/{id}/update", response_model=Optional[GroupResponse])
async def update_group_by_id(
    id: str, form_data: GroupUpdateForm, user=Depends(get_admin_user)
):
    try:
        if form_data.user_ids:
            form_data.user_ids = Users.get_valid_user_ids(form_data.user_ids)
            
            # 确保每个用户只在这一个组内
            for user_id in form_data.user_ids:
                Groups.ensure_user_in_single_group(user_id, id)

        group = Groups.update_group_by_id(id, form_data)
        if group:
            return group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating group"),
            )
    except Exception as e:
        log.exception(f"Error updating group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# DeleteGroupById
############################


@router.delete("/id/{id}/delete", response_model=bool)
async def delete_group_by_id(id: str, user=Depends(get_admin_user)):
    try:
        result = Groups.delete_group_by_id(id)
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting group"),
            )
    except Exception as e:
        log.exception(f"Error deleting group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )
