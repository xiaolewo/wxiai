"""
ComfyUI API工具类
处理哩布ComfyUI API的签名认证、请求发送、响应处理等功能
"""

import hmac
import hashlib
import base64
import time
import uuid
import json
import logging
from typing import Dict, Any, Optional, Tuple
import requests
from datetime import datetime

from open_webui.models.comfyui import (
    ComfyUIConfig,
    ComfyUITask,
    ComfyUIWorkflow,
    get_comfyui_config,
)

logger = logging.getLogger(__name__)


class ComfyUISignatureAuth:
    """ComfyUI签名认证工具"""

    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key

    def generate_signature(self, uri: str) -> Dict[str, str]:
        """生成哩布API签名"""
        # 当前毫秒时间戳
        timestamp = str(int(time.time() * 1000))
        # 随机字符串
        signature_nonce = str(uuid.uuid4())

        # 原文 = URL地址 + "&" + 毫秒时间戳 + "&" + 随机字符串
        content = f"{uri}&{timestamp}&{signature_nonce}"

        # 用SecretKey加密原文，使用hmacsha1算法
        digest = hmac.new(
            self.secret_key.encode(), content.encode(), hashlib.sha1
        ).digest()

        # 生成url安全的base64签名
        signature = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

        return {
            "AccessKey": self.access_key,
            "Signature": signature,
            "Timestamp": timestamp,
            "SignatureNonce": signature_nonce,
        }

    def get_signed_url(self, base_url: str, uri: str) -> str:
        """获取签名后的完整URL"""
        params = self.generate_signature(uri)
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}{uri}?{param_string}"


class ComfyUIAPIClient:
    """ComfyUI API客户端"""

    def __init__(self, config: Optional[ComfyUIConfig] = None):
        if config is None:
            config = get_comfyui_config()

        if not config or not config.enabled:
            raise ValueError("ComfyUI未配置或未启用")

        self.config = config
        self.auth = ComfyUISignatureAuth(config.access_key, config.secret_key)
        self.session = requests.Session()
        self.session.timeout = config.timeout

    def submit_workflow_task(
        self, template_uuid: str, generate_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提交工作流任务"""
        uri = "/api/generate/comfyui/app"

        # 构建请求体
        payload = {"templateUuid": template_uuid, "generateParams": generate_params}

        # 获取签名URL
        signed_url = self.auth.get_signed_url(self.config.base_url, uri)

        logger.info(f"提交ComfyUI任务: {template_uuid}")
        logger.info(f"🔍 请求URL: {signed_url}")
        logger.info(
            f"🔍 请求体结构: templateUuid={template_uuid}, generateParams包含节点: {list(generate_params.keys())}"
        )

        # 记录每个节点的结构以便调试
        for node_id, node_data in generate_params.items():
            if node_id != "workflowUuid":
                if isinstance(node_data, dict):
                    class_type = node_data.get("class_type", "MISSING")
                    inputs_keys = (
                        list(node_data.get("inputs", {}).keys())
                        if "inputs" in node_data
                        else []
                    )
                    logger.info(
                        f"🔍 节点{node_id}: class_type={class_type}, inputs={inputs_keys}"
                    )

        try:
            response = self.session.post(
                signed_url, json=payload, headers={"Content-Type": "application/json"}
            )

            # 记录响应状态
            logger.info(f"🔍 API响应状态: {response.status_code}")

            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ 任务提交成功: {result}")
            return result

        except requests.RequestException as e:
            logger.error(f"提交任务失败: {e}")
            raise

    def query_task_status(self, generate_uuid: str) -> Dict[str, Any]:
        """查询任务状态"""
        uri = "/api/generate/comfy/status"

        # 构建请求体
        payload = {"generateUuid": generate_uuid}

        # 获取签名URL
        signed_url = self.auth.get_signed_url(self.config.base_url, uri)

        logger.info(f"🔍 查询任务状态: {generate_uuid}")
        logger.info(f"🔍 查询URL: {signed_url}")

        try:
            response = self.session.post(
                signed_url, json=payload, headers={"Content-Type": "application/json"}
            )

            logger.info(f"🔍 查询响应状态: {response.status_code}")

            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ 任务状态查询成功: {generate_uuid}")
            return result

        except requests.RequestException as e:
            logger.error(f"❌ 查询任务状态失败: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"❌ 响应内容: {e.response.text}")
            raise


class ComfyUIParameterProcessor:
    """ComfyUI参数处理器"""

    @staticmethod
    def parse_workflow_schema(workflow_params: Dict[str, Any]) -> Dict[str, Any]:
        """解析工作流参数结构，生成前端表单配置"""
        schema = {"fields": [], "groups": {}, "validation": {}}

        for node_id, node_data in workflow_params.items():
            if node_id == "workflowUuid":
                continue

            if not isinstance(node_data, dict) or "inputs" not in node_data:
                continue

            class_type = node_data.get("class_type", "Unknown")
            inputs = node_data["inputs"]

            # 解析每个输入参数
            for param_name, param_value in inputs.items():
                field_info = ComfyUIParameterProcessor._create_field_info(
                    node_id, class_type, param_name, param_value
                )
                if field_info:
                    schema["fields"].append(field_info)

        return schema

    @staticmethod
    def _create_field_info(
        node_id: str, class_type: str, param_name: str, param_value: Any
    ) -> Optional[Dict[str, Any]]:
        """根据参数值创建字段信息"""
        field_info = {
            "nodeId": node_id,
            "className": class_type,
            "paramName": param_name,
            "id": f"{node_id}_{param_name}",
            "defaultValue": param_value,
        }

        # 根据节点类型和参数名称判断控件类型
        is_image_field = False

        # 检查是否是图像相关的节点和参数
        image_node_types = [
            "LoadImage",
            "SaveImage",
            "PreviewImage",
            "ImageUpscaleWithModel",
        ]
        image_param_names = [
            "image",
            "images",
            "input_image",
            "source_image",
            "target_image",
        ]

        if class_type in image_node_types or param_name.lower() in image_param_names:
            is_image_field = True
        elif isinstance(param_value, str):
            # 检查是否是图片URL
            if param_value.startswith("http") and any(
                ext in param_value.lower()
                for ext in [".jpg", ".png", ".jpeg", ".webp", ".gif"]
            ):
                is_image_field = True

        if is_image_field:
            field_info.update(
                {
                    "type": "IMAGE",
                    "controlType": "imageUpload",
                    "displayName": f"图像 ({param_name})",
                    "accept": "image/*",
                    "required": True,  # 图像字段通常是必填的
                }
            )
        elif isinstance(param_value, bool):
            field_info.update(
                {
                    "type": "BOOLEAN",
                    "controlType": "switch",
                    "displayName": f"开关 ({param_name})",
                }
            )
        elif isinstance(param_value, (int, float)):
            field_info.update(
                {
                    "type": "FLOAT" if isinstance(param_value, float) else "INTEGER",
                    "controlType": "number",
                    "displayName": f"数值 ({param_name})",
                    "min": 0,
                    "max": 100 if isinstance(param_value, float) else 1000,
                    "step": 0.1 if isinstance(param_value, float) else 1,
                }
            )
        elif isinstance(param_value, str):
            # 检查是否是文本输入字段
            if param_name.lower() in [
                "text",
                "prompt",
                "negative_prompt",
                "description",
            ]:
                field_info.update(
                    {
                        "type": "STRING",
                        "controlType": "textarea",
                        "displayName": f"文本 ({param_name})",
                        "rows": 3,
                    }
                )
            else:
                field_info.update(
                    {
                        "type": "STRING",
                        "controlType": "text",
                        "displayName": f"文本 ({param_name})",
                    }
                )

        else:
            # 未知类型，返回None
            return None

        return field_info

    @staticmethod
    async def build_generate_params(
        workflow: ComfyUIWorkflow,
        user_params: Dict[str, Any],
        user_id: str = None,
        task_id: str = None,
    ) -> Dict[str, Any]:
        """构建哩布API的generateParams"""
        generate_params = {}

        # 从工作流的默认参数开始，处理嵌套的generateParams结构
        if workflow.default_params:
            # 检查是否有嵌套的generateParams结构
            if "generateParams" in workflow.default_params:
                # 使用generateParams中的参数
                generate_params_source = workflow.default_params["generateParams"]
            else:
                # 直接使用default_params
                generate_params_source = workflow.default_params

            for key, value in generate_params_source.items():
                # templateUuid应该在请求体顶层，不在generateParams中
                if key not in ["templateUuid"]:
                    generate_params[key] = value

        # 解析参数结构，建立完整的参数映射
        field_map = {}
        if workflow.parameter_schema and "fields" in workflow.parameter_schema:
            for field in workflow.parameter_schema["fields"]:
                field_id = field.get("id")
                if field_id:
                    field_map[field_id] = field

        # 应用用户参数，根据parameter_schema进行正确映射
        logger.info(
            f"🔍 开始处理用户参数，共 {len(user_params)} 个参数: {list(user_params.keys())}"
        )
        logger.info(
            f"🔍 用户参数完整内容: {json.dumps(user_params, indent=2, ensure_ascii=False)}"
        )

        for field_id, value in user_params.items():
            logger.info(
                f"🔍 处理参数 {field_id}: 值类型={type(value)}, 长度={len(str(value)) if value else 0}"
            )

            if field_id not in field_map:
                logger.warning(f"⚠️ 跳过未知参数: {field_id}")
                continue

            field_info = field_map[field_id]
            logger.info(f"🔍 字段信息: {field_info}")

            # 支持哩布官方格式：
            # 1. 官方格式：使用 parentId 和 name，id为简单参数名
            # 2. 扩展格式：使用 nodeId 和 paramName
            node_id = field_info.get("parentId") or field_info.get("nodeId")
            param_name = (
                field_info.get("name") or field_info.get("paramName") or field_id
            )
            param_type = field_info.get("type", "STRING")

            # 如果没有明确的节点ID，尝试从field_id解析
            if not node_id and "_" in field_id:
                node_id = field_id.split("_")[0]

            if not node_id:
                logger.warning(f"⚠️ 无法确定参数 {field_id} 的节点ID")
                continue

            node_id = str(node_id)

            # 检查节点是否存在
            if node_id not in generate_params:
                logger.warning(f"⚠️ 跳过未知节点: {node_id}，该节点不在工作流默认参数中")
                logger.info(f"🔍 可用节点: {list(generate_params.keys())}")
                continue

            # 确保节点有inputs字段
            if "inputs" not in generate_params[node_id]:
                generate_params[node_id]["inputs"] = {}

            # 记录原始值
            original_value = generate_params[node_id]["inputs"].get(
                param_name, "未设置"
            )
            logger.info(f"🔄 节点{node_id}.{param_name} 原始值: {original_value}")

            # 根据参数类型处理值
            processed_value = await ComfyUIParameterProcessor._process_parameter_value(
                value, param_type, param_name, user_id, task_id
            )

            logger.info(
                f"📝 映射参数: {field_id} -> 节点{node_id}.{param_name} (类型: {param_type})"
            )
            logger.info(f"🔄 值变化: {original_value} -> {processed_value}")

            # 更新节点参数
            generate_params[node_id]["inputs"][param_name] = processed_value

        # 添加workflowUuid
        generate_params["workflowUuid"] = workflow.workflow_uuid

        logger.info(f"🚀 最终生成的参数结构: {list(generate_params.keys())}")

        # 特别检查sdxl_model参数
        for node_id, node_data in generate_params.items():
            if isinstance(node_data, dict) and "inputs" in node_data:
                inputs = node_data["inputs"]
                if "sdxl_model" in inputs:
                    logger.info(
                        f"🎯 节点{node_id}的sdxl_model参数: {inputs['sdxl_model']} (类型: {type(inputs['sdxl_model'])})"
                    )

        return generate_params

    @staticmethod
    async def _process_parameter_value(
        value: any, param_type: str, param_name: str, user_id: str, task_id: str
    ) -> any:
        """根据参数类型处理参数值"""
        if param_type == "IMAGE":
            # 图片类型参数，需要处理上传和云存储
            logger.info(
                f"🖼️ 处理图像参数: {param_name} = {value[:100] if isinstance(value, str) else value}..."
            )
            return await ComfyUIParameterProcessor._process_image_parameter(
                value, user_id, task_id
            )
        elif param_type == "INT":
            # 整数类型
            try:
                return int(value) if value is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"⚠️ 无法将值 {value} 转换为整数，使用默认值 0")
                return 0
        elif param_type == "FLOAT":
            # 浮点数类型
            try:
                return float(value) if value is not None else 0.0
            except (ValueError, TypeError):
                logger.warning(f"⚠️ 无法将值 {value} 转换为浮点数，使用默认值 0.0")
                return 0.0
        elif param_type == "BOOLEAN":
            # 布尔类型
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ["true", "1", "yes", "on"]
            else:
                return bool(value)
        elif param_type == "MODEL":
            # 模型类型，可能是字符串或数字
            if isinstance(value, (int, float)):
                return value
            elif isinstance(value, str):
                # 尝试转换为数字，如果失败则保持字符串
                try:
                    # 先尝试整数
                    return int(value)
                except ValueError:
                    try:
                        # 再尝试浮点数
                        return float(value)
                    except ValueError:
                        # 保持字符串
                        return value
            else:
                return value
        else:
            # 字符串类型或其他类型
            return str(value) if value is not None else ""

    @staticmethod
    async def _process_image_parameter(
        image_value: str, user_id: str, task_id: str
    ) -> str:
        """处理图片参数，如果是本地文件则上传到云存储"""
        if not image_value:
            return image_value

        # 如果已经是HTTP URL，直接返回
        if image_value.startswith("http"):
            return image_value

        # 如果是base64图片数据，检查大小并上传到云存储
        if image_value.startswith("data:image/"):
            # 检查base64图片大小（预估）
            base64_size = len(image_value)
            estimated_size_mb = (
                base64_size * 0.75 / (1024 * 1024)
            )  # base64大约比原始数据大33%
            logger.info(f"🔄 检测到base64图片，预估大小: {estimated_size_mb:.2f}MB")

            # 如果图片过大，记录警告但仍然尝试上传
            if estimated_size_mb > 5:
                logger.warning(
                    f"⚠️ 图片较大({estimated_size_mb:.2f}MB)，可能导致上传失败或API超时"
                )

            logger.info(f"🔄 开始上传base64图片到云存储，任务ID: {task_id}")
            try:
                from open_webui.utils.veo import upload_image_to_cloud

                cloud_url = await upload_image_to_cloud(image_value, user_id, task_id)
                if cloud_url:
                    logger.info(f"✅ 图片上传成功: {cloud_url}")
                    return cloud_url
                else:
                    logger.warning("⚠️ 图片上传失败，使用原始数据")
                    # 如果图片过大且上传失败，截断base64数据以避免API调用失败
                    if estimated_size_mb > 2:
                        logger.error("❌ 图片过大且上传失败，使用默认图片URL")
                        return "https://liblibai-online.liblib.cloud/img/081e9f07d9bd4c2ba090efde163518f9/aa1a1459986e5cc2b1236f7dc43a029119d6fe6ac26f1961a6639d21ca0b0bbe.png"
                    return image_value
            except Exception as e:
                import traceback

                logger.error(f"❌ 图片上传过程中出错: {e}")
                logger.error(f"详细错误堆栈: {traceback.format_exc()}")
                # 如果图片过大，使用默认图片而不是传递大数据
                if estimated_size_mb > 2:
                    logger.error("❌ 图片过大，使用默认图片URL")
                    return "https://liblibai-online.liblib.cloud/img/081e9f07d9bd4c2ba090efde163518f9/aa1a1459986e5cc2b1236f7dc43a029119d6fe6ac26f1961a6639d21ca0b0bbe.png"
                return image_value

        # 如果是 blob URL，记录警告并返回原值（前端修复后不会出现）
        if image_value.startswith("blob:"):
            logger.warning(f"⚠️ 检测到blob URL，前端应该已修复此问题: {image_value}")
            return image_value

        # 如果是本地文件路径，尝试转换为base64并上传
        if not image_value.startswith("http") and user_id and task_id:
            logger.info(f"检测到本地文件路径，尝试处理: {image_value}")
            # 这里可以添加本地文件处理逻辑
            # 目前先直接返回，让前端处理
            return image_value

        return image_value


class ComfyUITaskManager:
    """ComfyUI任务管理器"""

    def __init__(self):
        self.api_client = None

    def _get_api_client(self) -> ComfyUIAPIClient:
        """获取API客户端（每次重新加载以获取最新配置）"""
        # 每次都重新创建客户端以确保使用最新的配置
        return ComfyUIAPIClient()

    async def submit_task(self, task: ComfyUITask) -> Tuple[bool, Optional[str]]:
        """提交任务到哩布API"""
        try:
            # 获取工作流信息
            from open_webui.models.comfyui import ComfyUIWorkflows

            workflow = ComfyUIWorkflows.get_workflow_by_id(task.workflow_id)
            if not workflow:
                return False, "工作流不存在"

            # 构建API参数（支持图片上传到云存储）
            generate_params = await ComfyUIParameterProcessor.build_generate_params(
                workflow, task.input_params, task.user_id, task.id
            )

            # 记录最终发送的参数
            logger.info(f"🚀 最终发送给哩布API的参数:")
            logger.info(f"   Template UUID: {task.template_uuid}")
            logger.info(
                f"   Generate Params 详细内容: {json.dumps(generate_params, indent=2, ensure_ascii=False)}"
            )

            # 检查是否包含不可商用模型
            for node_id, node_data in generate_params.items():
                if isinstance(node_data, dict) and "inputs" in node_data:
                    for param_name, param_value in node_data["inputs"].items():
                        if (
                            isinstance(param_value, str)
                            and "juggernaut" in param_value.lower()
                        ):
                            logger.warning(
                                f"🚨 发现可能的不可商用模型: 节点{node_id}.{param_name} = {param_value}"
                            )
                        elif isinstance(param_value, str) and any(
                            keyword in param_value.lower()
                            for keyword in ["xl_v8", "rundiffusion"]
                        ):
                            logger.warning(
                                f"🚨 发现疑似限制模型: 节点{node_id}.{param_name} = {param_value}"
                            )

            # 提交任务
            api_client = self._get_api_client()
            result = api_client.submit_workflow_task(
                task.template_uuid, generate_params
            )

            # 检查API响应
            if "code" in result and result["code"] != 0:
                # API返回错误
                error_msg = result.get("msg", "未知错误")
                return False, f"哩布API错误: {error_msg}"

            # 更新任务信息
            if "data" in result and result["data"] and "generateUuid" in result["data"]:
                from open_webui.models.comfyui import ComfyUITasks

                generate_uuid = result["data"]["generateUuid"]
                ComfyUITasks.update_task_status(
                    task.id, "PENDING", generate_uuid=generate_uuid
                )
                return True, generate_uuid
            elif "generateUuid" in result:
                # 直接返回格式（兼容旧版本）
                from open_webui.models.comfyui import ComfyUITasks

                ComfyUITasks.update_task_status(
                    task.id, "PENDING", generate_uuid=result["generateUuid"]
                )
                return True, result["generateUuid"]
            else:
                return False, f"API返回格式异常: {result}"

        except Exception as e:
            import traceback

            logger.error(f"提交任务失败: {e}")
            logger.error(f"详细错误堆栈: {traceback.format_exc()}")
            return False, f"提交任务失败: {str(e)}"

    def check_task_status(self, task: ComfyUITask) -> bool:
        """检查任务状态"""
        if not task.generate_uuid:
            return False

        try:
            api_client = self._get_api_client()
            result = api_client.query_task_status(task.generate_uuid)

            logger.info(f"📊 收到任务状态查询响应: {result}")

            if "code" in result and result["code"] == 0 and "data" in result:
                # 更新任务状态
                logger.info(f"📊 更新任务状态，数据: {result['data']}")
                task.update_from_liblib_response(result["data"])

                # 保存到数据库
                from open_webui.internal.db import get_db

                with get_db() as db:
                    db.merge(task)  # 使用 merge 而不是 add，因为任务已存在
                    db.commit()

                logger.info(
                    f"📊 任务状态已更新: {task.status}, 进度: {task.percent_completed}%"
                )
                return True
            else:
                logger.warning(f"📊 任务状态查询失败: {result}")
                return False

        except Exception as e:
            logger.error(f"检查任务状态失败: {e}")
            return False


class ComfyUIWorkflowImporter:
    """ComfyUI工作流导入工具"""

    @staticmethod
    def import_from_liblib_example(
        example_data: Dict[str, Any], name: str, description: str = ""
    ) -> Dict[str, Any]:
        """从哩布示例数据导入工作流配置"""

        # 提取基本信息
        template_uuid = example_data.get(
            "templateUuid", "4df2efa0f18d46dc9758803e478eb51c"
        )
        generate_params = example_data.get("generateParams", {})
        workflow_uuid = generate_params.get("workflowUuid", "")

        # 解析参数结构
        parameter_schema = ComfyUIParameterProcessor.parse_workflow_schema(
            generate_params
        )

        # 构建工作流配置
        workflow_config = {
            "template_uuid": template_uuid,
            "workflow_uuid": workflow_uuid,
            "name": name,
            "description": description,
            "parameter_schema": parameter_schema,
            "default_params": generate_params,
            "base_credits": 10,
            "complexity_multiplier": 1.0,
            "enabled": True,
            "is_public": False,
            "sort_order": 0,
        }

        return workflow_config

    @staticmethod
    def create_sample_workflows():
        """创建示例工作流"""
        from open_webui.models.comfyui import ComfyUIWorkflows, ComfyUIWorkflowForm

        # 示例1：高清换脸工作流
        face_swap_example = {
            "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
            "generateParams": {
                "27": {"class_type": "CLIPTextEncode", "inputs": {"text": "freckles"}},
                "28": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": "Perfect skin"},
                },
                "40": {
                    "class_type": "LoadImage",
                    "inputs": {"image": "https://example.com/poster.jpg"},
                },
                "49": {
                    "class_type": "LoadImage",
                    "inputs": {"image": "https://example.com/face.jpg"},
                },
                "271": {
                    "class_type": "LayerMask: PersonMaskUltra V2",
                    "inputs": {"face": True, "hair": False},
                },
                "workflowUuid": "ae99b8cbe39a4d66a467211f45ddbda5",
            },
        }

        try:
            # 导入工作流配置
            config = ComfyUIWorkflowImporter.import_from_liblib_example(
                face_swap_example,
                "高清换脸",
                "将人脸替换到海报图像中，支持精确的面部识别和自然融合",
            )

            # 创建工作流
            form = ComfyUIWorkflowForm(**config)
            workflow = ComfyUIWorkflows.create_workflow(form)

            logger.info(f"示例工作流创建成功: {workflow.name}")
            return [workflow]

        except Exception as e:
            logger.error(f"创建示例工作流失败: {e}")
            return []


async def submit_comfyui_task(task_id: str) -> Tuple[bool, Optional[str]]:
    """提交ComfyUI任务的便捷函数"""
    from open_webui.models.comfyui import ComfyUITasks

    task = ComfyUITasks.get_task_by_id(task_id)
    if not task:
        return False, "任务不存在"

    # 每次创建新的任务管理器以获取最新配置
    task_manager = ComfyUITaskManager()
    return await task_manager.submit_task(task)


def check_comfyui_task_status(task_id: str) -> bool:
    """检查ComfyUI任务状态的便捷函数"""
    from open_webui.models.comfyui import ComfyUITasks

    task = ComfyUITasks.get_task_by_id(task_id)
    if not task:
        return False

    # 每次创建新的任务管理器以获取最新配置
    task_manager = ComfyUITaskManager()
    return task_manager.check_task_status(task)
