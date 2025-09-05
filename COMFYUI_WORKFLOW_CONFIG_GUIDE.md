# ComfyUI 工作流配置完整指南

## 📋 目录

1. [快速开始](#快速开始)
2. [配置示例](#配置示例)
3. [参数结构详解](#参数结构详解)
4. [默认参数详解](#默认参数详解)
5. [实用模板](#实用模板)
6. [常见问题](#常见问题)

---

## 🚀 快速开始

### 基本配置流程

1. 进入管理面板 → 设置 → ComfyUI
2. 点击"添加工作流"
3. 填写基本信息（名称、描述、UUID等）
4. 配置"参数结构"和"默认参数"两个JSON字段
5. 保存并测试

---

## 💡 配置示例

### SUPIR图像放大工作流

**工作流信息：**

- 名称：SUPIR图像放大
- 模板UUID：`4df2efa0f18d46dc9758803e478eb51c`
- 工作流UUID：`3e54edc7d52b4fa49644bfa92ad06c13`

**参数结构 (Parameter Schema)：**

```json
{
	"fields": [
		{
			"id": "image",
			"name": "image",
			"paramName": "image",
			"displayName": "图像",
			"type": "IMAGE",
			"controlType": "imageUpload",
			"required": true,
			"defaultValue": "img/84cd9ecbef5b4333afb1125200e50242/2b04302c9011b28337a6c992faa62c9447d64de71f41ea6a19e741d9873e1d4d.png",
			"image_upload": true,
			"isMaskImage": false,
			"accept": "image/*",
			"tooltip": "请上传需要放大的图片",
			"parentId": 2
		},
		{
			"id": "sdxl_model",
			"name": "sdxl_model",
			"paramName": "sdxl_model",
			"displayName": "SDXL模型",
			"type": "MODEL",
			"controlType": "text",
			"required": true,
			"defaultValue": 827118,
			"tooltip": "SDXL模型ID，用于图像放大处理",
			"parentId": 15
		},
		{
			"id": "steps",
			"name": "steps",
			"paramName": "steps",
			"displayName": "步数",
			"type": "INT",
			"controlType": "number",
			"required": true,
			"defaultValue": 45,
			"min": 3,
			"max": 4096,
			"step": 1,
			"tooltip": "生成步数，影响图像质量和处理时间",
			"parentId": 15
		}
	]
}
```

**默认参数 (Default Params)：**

```json
{
	"2": {
		"class_type": "LoadImage",
		"inputs": {
			"image": "https://liblibai-tmp-image.liblib.cloud/img/84cd9ecbef5b4333afb1125200e50242/2b04302c9011b28337a6c992faa62c9447d64de71f41ea6a19e741d9873e1d4d.png"
		}
	},
	"15": {
		"class_type": "SUPIR_Upscale",
		"inputs": {
			"sdxl_model": 827118,
			"steps": 45
		}
	},
	"workflowUuid": "3e54edc7d52b4fa49644bfa92ad06c13"
}
```

---

## 📖 参数结构详解

### fields数组中每个字段的属性

| 属性名         | 必填 | 类型    | 说明                                                       | 示例值                     |
| -------------- | ---- | ------- | ---------------------------------------------------------- | -------------------------- |
| `id`           | ✅   | string  | 参数唯一标识，直接使用参数名                               | `"image"`, `"steps"`       |
| `paramName`    | ✅   | string  | API参数名称                                                | `"image"`, `"steps"`       |
| `displayName`  | ✅   | string  | 用户界面显示的字段名                                       | `"上传图像"`, `"生成步数"` |
| `type`         | ✅   | string  | 数据类型：`STRING`, `INTEGER`, `FLOAT`, `IMAGE`, `BOOLEAN` | `"STRING"`                 |
| `controlType`  | ✅   | string  | 控件类型：`text`, `number`, `imageUpload`, `switch`        | `"text"`                   |
| `required`     | ❌   | boolean | 是否为必填字段                                             | `true`, `false`            |
| `defaultValue` | ❌   | any     | 默认值                                                     | `"默认文本"`, `42`         |
| `min`          | ❌   | number  | 最小值（仅数字类型）                                       | `1`                        |
| `max`          | ❌   | number  | 最大值（仅数字类型）                                       | `100`                      |
| `step`         | ❌   | number  | 步进值（仅数字类型）                                       | `0.1`                      |
| `tooltip`      | ❌   | string  | 字段提示信息                                               | `"请输入提示词"`           |
| `accept`       | ❌   | string  | 文件类型限制（仅文件上传）                                 | `"image/*"`                |
| `parentId`     | ❌   | number  | 对应的ComfyUI节点ID                                        | `2`, `15`                  |

### 控件类型说明

#### 1. `text` - 文本输入框

```json
{
	"id": "prompt",
	"displayName": "提示词",
	"type": "STRING",
	"controlType": "text",
	"defaultValue": "一张美丽的风景照片",
	"tooltip": "描述你想要生成的图像"
}
```

#### 2. `number` - 数字输入框

```json
{
	"id": "steps",
	"displayName": "生成步数",
	"type": "INTEGER",
	"controlType": "number",
	"defaultValue": 20,
	"min": 1,
	"max": 150,
	"step": 1
}
```

#### 3. `imageUpload` - 图片上传

```json
{
	"id": "input_image",
	"displayName": "输入图像",
	"type": "IMAGE",
	"controlType": "imageUpload",
	"required": true,
	"accept": "image/*",
	"tooltip": "请上传图片文件（最大5MB）"
}
```

#### 4. `switch` - 开关按钮

```json
{
	"id": "enable_highres",
	"displayName": "启用高分辨率",
	"type": "BOOLEAN",
	"controlType": "switch",
	"defaultValue": false,
	"label_on": "启用",
	"label_off": "禁用"
}
```

---

## 🔧 默认参数详解

### 基本结构

```json
{
	"节点ID": {
		"class_type": "节点类型名称",
		"inputs": {
			"参数名": "默认值"
		}
	},
	"templateUuid": "哩布模板UUID",
	"workflowUuid": "哩布工作流UUID"
}
```

### 参数映射规则

- **节点ID**：ComfyUI工作流中的节点编号
- **class_type**：节点的类型名称（如LoadImage, SUPIR_Upscale）
- **inputs**：该节点的输入参数
- **templateUuid**：哩布平台的模板UUID
- **workflowUuid**：哩布平台的工作流UUID

### 动态参数替换

当用户提交表单时，系统会：

1. 从表单获取用户输入的值
2. 根据parentId找到对应的节点
3. 替换默认参数中的对应值
4. 发送到哩布API执行

---

## 🎯 实用模板

### 1. 文本生图工作流

```json
// 参数结构
{
  "fields": [
    {
      "id": "prompt",
      "displayName": "正向提示词",
      "type": "STRING",
      "controlType": "text",
      "required": true,
      "defaultValue": "masterpiece, best quality, 1girl",
      "tooltip": "描述想要生成的图像内容"
    },
    {
      "id": "negative_prompt",
      "displayName": "负向提示词",
      "type": "STRING",
      "controlType": "text",
      "defaultValue": "lowres, bad anatomy, bad hands",
      "tooltip": "描述不想要的图像元素"
    },
    {
      "id": "steps",
      "displayName": "采样步数",
      "type": "INTEGER",
      "controlType": "number",
      "defaultValue": 20,
      "min": 1,
      "max": 150
    },
    {
      "id": "cfg_scale",
      "displayName": "提示词相关性",
      "type": "FLOAT",
      "controlType": "number",
      "defaultValue": 7.0,
      "min": 1.0,
      "max": 30.0,
      "step": 0.1
    }
  ]
}

// 默认参数
{
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "masterpiece, best quality, 1girl"
    }
  },
  "7": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "lowres, bad anatomy, bad hands"
    }
  },
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "steps": 20,
      "cfg": 7.0
    }
  },
  "templateUuid": "your-template-uuid",
  "workflowUuid": "your-workflow-uuid"
}
```

### 2. 图像修复工作流

```json
// 参数结构
{
	"fields": [
		{
			"id": "input_image",
			"displayName": "原始图像",
			"type": "IMAGE",
			"controlType": "imageUpload",
			"required": true,
			"accept": "image/*"
		},
		{
			"id": "mask_image",
			"displayName": "遮罩图像",
			"type": "IMAGE",
			"controlType": "imageUpload",
			"required": true,
			"accept": "image/*",
			"tooltip": "白色区域将被修复，黑色区域保持不变"
		},
		{
			"id": "denoise_strength",
			"displayName": "去噪强度",
			"type": "FLOAT",
			"controlType": "number",
			"defaultValue": 0.75,
			"min": 0.0,
			"max": 1.0,
			"step": 0.01,
			"tooltip": "值越高修改越大"
		}
	]
}
```

---

## ❓ 常见问题

### Q1: 工作流显示"暂无可配置参数"

**原因：** 参数结构JSON格式错误或fields数组为空
**解决：**

1. 检查JSON语法是否正确
2. 确保包含`fields`数组
3. 数组中至少包含一个字段对象

### Q2: 参数不生效，使用的还是默认值

**原因：** 参数映射关系配置错误
**解决：**

1. ⚠️ **重要：** 字段`id`应直接使用参数名，如`"steps"`、`"image"`
2. 检查`parentId`对应的节点ID在默认参数中存在
3. 验证节点的`class_type`是否正确
4. 确认`paramName`与默认参数中的参数名一致
5. 确保`name`字段与`paramName`一致（哩布规范要求）

### Q3: JSON格式验证失败

**解决方法：**

1. 使用在线JSON验证工具检查语法
2. 注意逗号、引号、括号的匹配
3. 字符串值必须用双引号包围
4. 数组最后一个元素后不要加逗号

### Q4: 图片上传失败

**原因：** 图片大小超限制或格式不支持
**解决：**

1. 图片大小不超过5MB
2. 使用常见格式：JPG, PNG, WebP
3. 检查网络连接是否稳定

### Q5: 工作流执行失败，返回"[-1]执行异常"

**可能原因：**

1. 模板UUID或工作流UUID错误
2. 节点参数类型不匹配
3. 必需参数缺失
4. 图片格式或大小问题

**解决步骤：**

1. 验证UUID的正确性
2. 检查参数类型匹配（STRING vs INTEGER）
3. 确认所有必填字段都有值
4. 查看后端日志获取详细错误信息

### Q6: 如何获取模板和工作流UUID？

1. 访问哩布AI开放平台
2. 找到对应的ComfyUI工作流
3. 从API文档或示例代码中获取UUID
4. 模板UUID通常较短，工作流UUID较长

---

## 🔗 相关链接

- [哩布AI开放平台](https://openapi.liblibai.cloud/)
- [ComfyUI官方文档](https://github.com/comfyanonymous/ComfyUI)
- [JSON在线验证工具](https://jsonlint.com/)

---

## 📝 更新日志

- **2025-09-01**: 初始版本发布
- 支持基本的文本、数字、图片上传、开关控件
- 提供SUPIR图像放大工作流完整示例
- 添加常见问题解答

---

**提示：** 如果遇到其他问题，请查看浏览器控制台和后端日志获取更详细的错误信息。
