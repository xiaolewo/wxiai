#!/usr/bin/env python3
"""
可灵对口型功能测试模块
用于验证所有API接口和业务逻辑的正确性
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import json
import base64

# 导入测试相关模块
from open_webui.main import app
from open_webui.internal.db import Base, get_db
from open_webui.models.kling_lip_sync import (
    KlingLipSyncConfig,
    KlingLipSyncTask,
    KlingLipSyncCredit,
    KlingLipSyncTable,
)
from open_webui.utils.kling_lip_sync import KlingLipSyncAPI, KlingLipSyncService


class TestKlingLipSyncDatabase:
    """测试数据库相关功能"""

    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        # 使用内存数据库进行测试
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        # 插入默认配置
        default_config = KlingLipSyncConfig(
            id="default",
            enabled=False,
            base_url="https://api.kling.com",
            api_key="",
            default_voice_id="genshin_vindi2",
            default_voice_language="zh",
            default_voice_speed=1.0,
            credits_cost=50,
        )
        session.add(default_config)
        session.commit()

        yield session
        session.close()

    def test_config_crud_operations(self, db_session):
        """测试配置的CRUD操作"""
        # 测试读取配置
        config = db_session.query(KlingLipSyncConfig).filter_by(id="default").first()
        assert config is not None
        assert config.enabled is False
        assert config.base_url == "https://api.kling.com"

        # 测试更新配置
        config.enabled = True
        config.api_key = "test-key"
        db_session.commit()

        updated_config = (
            db_session.query(KlingLipSyncConfig).filter_by(id="default").first()
        )
        assert updated_config.enabled is True
        assert updated_config.api_key == "test-key"

    def test_task_creation(self, db_session):
        """测试任务创建"""
        task = KlingLipSyncTask(
            id="test-task-123",
            user_id="user123",
            mode="text",
            text_content="测试文本",
            voice_id="genshin_vindi2",
            voice_language="zh",
            voice_speed=1.0,
            video_url="https://example.com/video.mp4",
            status="pending",
        )
        db_session.add(task)
        db_session.commit()

        saved_task = (
            db_session.query(KlingLipSyncTask).filter_by(id="test-task-123").first()
        )
        assert saved_task is not None
        assert saved_task.user_id == "user123"
        assert saved_task.mode == "text"
        assert saved_task.status == "pending"

    def test_credit_recording(self, db_session):
        """测试积分记录"""
        credit = KlingLipSyncCredit(
            id="credit-123",
            user_id="user123",
            task_id="test-task-123",
            credits_used=50,
            operation_type="deduct",
        )
        db_session.add(credit)
        db_session.commit()

        saved_credit = (
            db_session.query(KlingLipSyncCredit).filter_by(id="credit-123").first()
        )
        assert saved_credit is not None
        assert saved_credit.credits_used == 50
        assert saved_credit.operation_type == "deduct"


class TestKlingLipSyncAPI:
    """测试可灵API客户端"""

    @pytest.fixture
    def api_client(self):
        """创建API客户端"""
        return KlingLipSyncAPI(base_url="https://api.kling.com", api_key="test-key")

    @patch("aiohttp.ClientSession.post")
    async def test_text_to_lip_sync(self, mock_post, api_client):
        """测试文本转对口型"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "code": 0,
                "message": "success",
                "data": {"task_id": "test-task-123", "status": "submitted"},
            }
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await api_client.create_text_lip_sync(
            text="测试文本",
            voice_id="genshin_vindi2",
            voice_language="zh",
            voice_speed=1.0,
            video_url="https://example.com/video.mp4",
        )

        assert result["task_id"] == "test-task-123"
        assert result["status"] == "submitted"

    @patch("aiohttp.ClientSession.get")
    async def test_query_task_status(self, mock_get, api_client):
        """测试查询任务状态"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "code": 0,
                "message": "success",
                "data": {
                    "task_id": "test-task-123",
                    "status": "completed",
                    "result": {"video_url": "https://result.com/video.mp4"},
                },
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await api_client.query_task("test-task-123")

        assert result["task_id"] == "test-task-123"
        assert result["status"] == "completed"
        assert result["result"]["video_url"] == "https://result.com/video.mp4"


class TestKlingLipSyncService:
    """测试业务服务层"""

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return KlingLipSyncService(db_session)

    def test_get_config(self, service, db_session):
        """测试获取配置"""
        config = service.get_config()
        assert config is not None
        assert config.id == "default"

    def test_save_config(self, service, db_session):
        """测试保存配置"""
        config_data = {
            "enabled": True,
            "base_url": "https://api.kling.com",
            "api_key": "new-test-key",
            "default_voice_id": "genshin_vindi2",
            "default_voice_language": "zh",
            "default_voice_speed": 1.5,
            "credits_cost": 60,
        }

        result = service.save_config(config_data)
        assert result.enabled is True
        assert result.api_key == "new-test-key"
        assert result.default_voice_speed == 1.5
        assert result.credits_cost == 60


class TestKlingLipSyncEndpoints:
    """测试API端点"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """创建认证头"""
        return {"Authorization": "Bearer test-token"}

    def test_get_config_endpoint(self, client, auth_headers):
        """测试获取配置接口"""
        with patch("open_webui.utils.auth.decode_token") as mock_decode:
            mock_decode.return_value = {"id": "admin"}

            with patch(
                "open_webui.models.kling_lip_sync.KlingLipSyncTable.get_config"
            ) as mock_get:
                mock_config = Mock()
                mock_config.model_dump.return_value = {
                    "enabled": True,
                    "base_url": "https://api.kling.com",
                    "api_key": "***",
                    "credits_cost": 50,
                }
                mock_get.return_value = mock_config

                response = client.get(
                    "/api/v1/kling-lip-sync/config", headers=auth_headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["enabled"] is True

    def test_create_task_endpoint(self, client, auth_headers):
        """测试创建任务接口"""
        task_data = {
            "mode": "text",
            "text_content": "测试文本",
            "voice_id": "genshin_vindi2",
            "voice_language": "zh",
            "voice_speed": 1.0,
            "video_url": "https://example.com/video.mp4",
        }

        with patch("open_webui.utils.auth.decode_token") as mock_decode:
            mock_decode.return_value = {"id": "user123"}

            with patch(
                "open_webui.models.kling_lip_sync.KlingLipSyncTable.create_task"
            ) as mock_create:
                mock_task = Mock()
                mock_task.model_dump.return_value = {
                    "id": "test-task-123",
                    "status": "pending",
                }
                mock_create.return_value = mock_task

                response = client.post(
                    "/api/v1/kling-lip-sync/tasks", json=task_data, headers=auth_headers
                )
                assert response.status_code == 200


def test_voice_options_integrity():
    """测试音色选项完整性"""
    from open_webui.utils.kling_lip_sync import (
        CHINESE_VOICE_OPTIONS,
        ENGLISH_VOICE_OPTIONS,
    )

    # 验证中文音色数量
    assert (
        len(CHINESE_VOICE_OPTIONS) == 35
    ), f"中文音色数量应为35个，实际为{len(CHINESE_VOICE_OPTIONS)}个"

    # 验证英文音色数量
    assert (
        len(ENGLISH_VOICE_OPTIONS) == 27
    ), f"英文音色数量应为27个，实际为{len(ENGLISH_VOICE_OPTIONS)}个"

    # 验证音色选项结构
    for voice in CHINESE_VOICE_OPTIONS:
        assert "value" in voice, "音色选项必须包含value字段"
        assert "label" in voice, "音色选项必须包含label字段"
        assert isinstance(voice["value"], str), "value字段必须是字符串"
        assert isinstance(voice["label"], str), "label字段必须是字符串"

    for voice in ENGLISH_VOICE_OPTIONS:
        assert "value" in voice, "音色选项必须包含value字段"
        assert "label" in voice, "音色选项必须包含label字段"
        assert isinstance(voice["value"], str), "value字段必须是字符串"
        assert isinstance(voice["label"], str), "label字段必须是字符串"


class TestIntegrationScenarios:
    """集成测试场景"""

    def test_complete_text_lip_sync_workflow(self):
        """测试完整的文本对口型工作流程"""
        # 这里应该包含端到端的测试流程
        # 1. 用户提交任务
        # 2. 扣除积分
        # 3. 调用可灵API
        # 4. 轮询任务状态
        # 5. 更新任务结果
        # 6. 记录积分使用
        pass

    def test_error_handling_scenarios(self):
        """测试错误处理场景"""
        # 1. API密钥错误
        # 2. 积分不足
        # 3. 网络连接失败
        # 4. 文件上传失败
        # 5. 任务超时
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
