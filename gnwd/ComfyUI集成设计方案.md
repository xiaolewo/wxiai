# ComfyUI集成设计方案

## 概述

基于哩布ComfyUI API的集成方案，实现工作流管理、动态参数处理、积分扣除等功能，支持公开工作流广场和用户节点页面。

## 1. 数据库设计

### 1.1 comfyui_config - 配置表

```sql
CREATE TABLE comfyui_config (
    id VARCHAR(255) PRIMARY KEY,
    access_key TEXT NOT NULL COMMENT 'API访问凭证',
    secret_key TEXT NOT NULL COMMENT 'API访问密钥',
    base_url VARCHAR(500) DEFAULT 'https://openapi.liblibai.cloud' COMMENT 'API基础URL',
    enabled BOOLEAN DEFAULT FALSE COMMENT '启用状态',
    timeout INTEGER DEFAULT 300 COMMENT '请求超时时间（秒）',
    max_concurrent_tasks INTEGER DEFAULT 5 COMMENT '最大并发任务数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 1.2 comfyui_workflows - 工作流管理表

```sql
CREATE TABLE comfyui_workflows (
    id VARCHAR(255) PRIMARY KEY,
    template_uuid VARCHAR(255) NOT NULL COMMENT '模板UUID',
    workflow_uuid VARCHAR(255) NOT NULL COMMENT '工作流UUID',
    name VARCHAR(255) NOT NULL COMMENT '工作流名称',
    description TEXT COMMENT '工作流描述',
    category VARCHAR(100) COMMENT '分类',
    preview_image TEXT COMMENT '预览图URL',

    -- 参数配置
    parameter_schema JSON NOT NULL COMMENT '参数结构定义',
    default_params JSON COMMENT '默认参数值',

    -- 积分配置
    base_credits INTEGER DEFAULT 10 COMMENT '基础积分消耗',
    complexity_multiplier FLOAT DEFAULT 1.0 COMMENT '复杂度系数',

    -- 状态配置
    enabled BOOLEAN DEFAULT TRUE COMMENT '启用状态',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开显示',
    sort_order INTEGER DEFAULT 0 COMMENT '排序权重',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_workflows_public_enabled (is_public, enabled),
    INDEX idx_workflows_category (category)
);
```

### 1.3 comfyui_tasks - 任务执行表

```sql
CREATE TABLE comfyui_tasks (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL COMMENT '用户ID',
    workflow_id VARCHAR(255) NOT NULL COMMENT '工作流ID',
    generate_uuid VARCHAR(255) UNIQUE COMMENT '哩布API返回的任务UUID',

    -- 任务参数
    input_params JSON NOT NULL COMMENT '输入参数',
    template_uuid VARCHAR(255) NOT NULL COMMENT '模板UUID',
    workflow_uuid VARCHAR(255) NOT NULL COMMENT '工作流UUID',

    -- 任务状态
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '任务状态: PENDING,RUNNING,SUCCESS,FAILED',
    generate_status INTEGER COMMENT '哩布返回的状态码',
    percent_completed FLOAT DEFAULT 0 COMMENT '完成进度',

    -- 结果数据
    output_images JSON COMMENT '输出图片列表',
    output_videos JSON COMMENT '输出视频列表',
    cloud_images JSON COMMENT '云存储图片URLs',
    cloud_videos JSON COMMENT '云存储视频URLs',

    -- 消耗信息
    credits_cost INTEGER COMMENT '积分消耗',
    generation_time FLOAT COMMENT '生成耗时',

    -- 错误信息
    error_message TEXT COMMENT '错误信息',
    retry_count INTEGER DEFAULT 0 COMMENT '重试次数',
    liblib_response JSON COMMENT '哩布API原始响应',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME COMMENT '完成时间',

    INDEX idx_tasks_user_status (user_id, status),
    INDEX idx_tasks_workflow_status (workflow_id, status),
    INDEX idx_tasks_generate_uuid (generate_uuid),
    INDEX idx_tasks_created_at (created_at),

    FOREIGN KEY (workflow_id) REFERENCES comfyui_workflows(id)
);
```

### 1.4 comfyui_credits - 积分管理表

```sql
CREATE TABLE comfyui_credits (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL COMMENT '用户ID',
    credits_balance INTEGER DEFAULT 0 COMMENT '剩余积分',
    total_used INTEGER DEFAULT 0 COMMENT '已使用积分',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_credits_user_id (user_id)
);
```

## 2. 核心功能模块

### 2.1 签名认证模块

```python
class ComfyUISignature:
    def generate_signature(self, uri: str, access_key: str, secret_key: str) -> dict:
        """生成哩布API签名"""
        timestamp = str(int(time.time() * 1000))
        signature_nonce = str(uuid.uuid4())
        content = f"{uri}&{timestamp}&{signature_nonce}"

        # HMAC-SHA1加密
        digest = hmac.new(secret_key.encode(), content.encode(), hashlib.sha1).digest()
        signature = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

        return {
            "AccessKey": access_key,
            "Signature": signature,
            "Timestamp": timestamp,
            "SignatureNonce": signature_nonce
        }
```

### 2.2 动态参数处理模块

```python
class ParameterProcessor:
    def parse_workflow_schema(self, workflow_data: dict) -> dict:
        """解析工作流参数结构"""
        schema = {
            "parameters": [],
            "required": [],
            "groups": {}
        }

        # 解析节点参数
        for node_id, node_data in workflow_data.get("generateParams", {}).items():
            if node_id == "workflowUuid":
                continue

            class_type = node_data.get("class_type")
            inputs = node_data.get("inputs", {})

            for param_name, param_value in inputs.items():
                param_info = self.get_parameter_info(node_id, param_name, param_value)
                if param_info:
                    schema["parameters"].append(param_info)

        return schema

    def generate_form_config(self, parameter_schema: dict) -> dict:
        """生成前端表单配置"""
        form_config = {
            "fields": [],
            "groups": [],
            "validation": {}
        }

        for param in parameter_schema["parameters"]:
            field_config = self.create_field_config(param)
            form_config["fields"].append(field_config)

        return form_config
```

### 2.3 积分计算模块

```python
class CreditCalculator:
    def calculate_credits(self, workflow_id: str, params: dict) -> int:
        """计算积分消耗"""
        workflow = self.get_workflow(workflow_id)
        base_credits = workflow.base_credits
        multiplier = workflow.complexity_multiplier

        # 基于参数动态调整
        param_multiplier = 1.0

        # 图片尺寸影响
        if "width" in params and "height" in params:
            pixel_count = params["width"] * params["height"]
            param_multiplier *= (pixel_count / 512 / 512)

        # 生成数量影响
        if "num_images" in params:
            param_multiplier *= params["num_images"]

        # 推理步数影响
        if "steps" in params:
            param_multiplier *= (params["steps"] / 20)

        final_credits = int(base_credits * multiplier * param_multiplier)
        return max(final_credits, 1)  # 最少1积分
```

## 3. API接口设计

### 3.1 管理员接口

- `POST /api/v1/comfyui/config` - 保存配置
- `GET /api/v1/comfyui/config` - 获取配置
- `POST /api/v1/comfyui/workflows` - 添加工作流
- `PUT /api/v1/comfyui/workflows/{id}` - 更新工作流
- `DELETE /api/v1/comfyui/workflows/{id}` - 删除工作流

### 3.2 用户接口

- `GET /api/v1/comfyui/workflows/public` - 获取公开工作流列表
- `GET /api/v1/comfyui/workflows/{id}/schema` - 获取工作流参数结构
- `POST /api/v1/comfyui/tasks` - 提交生成任务
- `GET /api/v1/comfyui/tasks/{id}/status` - 查询任务状态
- `GET /api/v1/comfyui/tasks/history` - 获取历史任务

## 4. 前端界面设计

### 4.1 管理员配置页面

- API密钥配置区域
- 工作流管理表格（增删改查）
- 参数编辑器（可视化JSON编辑）
- 积分价格配置

### 4.2 用户广场页面

- 工作流网格卡片展示
- 分类筛选侧边栏
- 搜索功能
- 预览图和基本信息

### 4.3 工作流节点页面

- 动态表单渲染区域
- 实时参数预览
- 提交按钮和进度显示
- 历史任务结果展示

## 5. 集成策略

### 5.1 与现有系统集成

- 遵循WXIAI三表模式（config, tasks, credits）
- 使用统一的用户认证和权限系统
- 整合云存储自动上传功能
- 统一错误处理和日志记录

### 5.2 三层保护机制

1. **数据库迁移** - Alembic迁移文件创建表结构
2. **模型层检查** - 启动时自动检查表存在性
3. **运行时保护** - 操作前验证表结构完整性

### 5.3 扩展性考虑

- 参数类型可扩展（支持新的输入类型）
- 工作流模板可动态添加
- 积分计算规则可配置
- 支持多个ComfyUI提供商

## 6. 实现优先级

### 阶段1：基础功能

1. 数据库表创建和基础模型
2. 配置管理功能
3. 签名认证机制
4. 基础API接口

### 阶段2：核心功能

1. 工作流管理系统
2. 动态参数处理
3. 任务提交和状态跟踪
4. 积分计算和扣除

### 阶段3：用户界面

1. 管理员配置页面
2. 用户工作流广场
3. 节点编辑页面
4. 任务历史和结果展示

## 7. 技术难点解决

### 7.1 动态参数挑战

- **问题**：不同工作流参数结构差异很大
- **解决**：JSON Schema + 动态表单渲染系统

### 7.2 签名认证复杂性

- **问题**：HMAC-SHA1签名生成和URL安全编码
- **解决**：封装专用签名工具类

### 7.3 积分计算公平性

- **问题**：如何合理计算不同复杂度工作流的积分
- **解决**：基础积分 + 参数复杂度系数的组合模式

这个设计方案充分考虑了哩布ComfyUI的特性，既保持了系统的一致性，又具备了足够的灵活性来适应各种工作流需求。
