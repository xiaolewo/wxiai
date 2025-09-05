# ComfyUI 工作流参数配置示例

## 配置说明

在管理员面板添加ComfyUI工作流时，需要正确配置两个重要字段：

### 1. 参数结构 (Parameter Schema)

定义前端表单的字段配置，格式如下：

```json
{
	"fields": [
		{
			"id": "27_text",
			"nodeId": "27",
			"paramName": "text",
			"type": "STRING",
			"controlType": "textarea",
			"displayName": "正向提示词",
			"required": true,
			"defaultValue": "freckles",
			"rows": 3
		},
		{
			"id": "28_text",
			"nodeId": "28",
			"paramName": "text",
			"type": "STRING",
			"controlType": "textarea",
			"displayName": "负向提示词",
			"required": false,
			"defaultValue": "Perfect skin",
			"rows": 3
		},
		{
			"id": "40_image",
			"nodeId": "40",
			"paramName": "image",
			"type": "IMAGE",
			"controlType": "imageUpload",
			"displayName": "背景图像",
			"required": true,
			"accept": "image/*"
		},
		{
			"id": "49_image",
			"nodeId": "49",
			"paramName": "image",
			"type": "IMAGE",
			"controlType": "imageUpload",
			"displayName": "人脸图像",
			"required": true,
			"accept": "image/*"
		},
		{
			"id": "271_face",
			"nodeId": "271",
			"paramName": "face",
			"type": "BOOLEAN",
			"controlType": "switch",
			"displayName": "检测人脸",
			"defaultValue": true
		},
		{
			"id": "271_hair",
			"nodeId": "271",
			"paramName": "hair",
			"type": "BOOLEAN",
			"controlType": "switch",
			"displayName": "检测头发",
			"defaultValue": false
		}
	]
}
```

### 2. 默认参数 (Default Params)

定义发送给哩布API的完整工作流参数，格式如下：

```json
{
	"27": {
		"class_type": "CLIPTextEncode",
		"inputs": {
			"text": "freckles"
		}
	},
	"28": {
		"class_type": "CLIPTextEncode",
		"inputs": {
			"text": "Perfect skin"
		}
	},
	"40": {
		"class_type": "LoadImage",
		"inputs": {
			"image": ""
		}
	},
	"49": {
		"class_type": "LoadImage",
		"inputs": {
			"image": ""
		}
	},
	"271": {
		"class_type": "LayerMask: PersonMaskUltra V2",
		"inputs": {
			"face": true,
			"hair": false
		}
	},
	"workflowUuid": "ae99b8cbe39a4d66a467211f45ddbda5"
}
```

## 字段类型说明

### 支持的字段类型 (type)

- **IMAGE**: 图像上传字段
- **STRING**: 文本字段
- **INTEGER**: 整数字段
- **FLOAT**: 浮点数字段
- **BOOLEAN**: 布尔开关字段

### 支持的控件类型 (controlType)

- **imageUpload**: 文件上传控件（用于IMAGE类型）
- **text**: 单行文本输入框
- **textarea**: 多行文本输入框
- **number**: 数字输入框
- **switch**: 开关控件（用于BOOLEAN类型）

## 参数映射规则

1. **字段ID格式**: `节点ID_参数名` (如: "27_text")
2. **nodeId**: 对应ComfyUI工作流中的节点ID
3. **paramName**: 对应节点inputs中的参数名
4. **用户提交的参数**: 会根据nodeId和paramName映射到对应的工作流节点

## 常用示例

### 文本输入字段

```json
{
	"id": "27_text",
	"nodeId": "27",
	"paramName": "text",
	"type": "STRING",
	"controlType": "textarea",
	"displayName": "输入提示词",
	"required": true,
	"defaultValue": "beautiful girl",
	"rows": 3
}
```

### 图像上传字段

```json
{
	"id": "40_image",
	"nodeId": "40",
	"paramName": "image",
	"type": "IMAGE",
	"controlType": "imageUpload",
	"displayName": "上传图片",
	"required": true,
	"accept": "image/*"
}
```

### 数值字段

```json
{
	"id": "25_steps",
	"nodeId": "25",
	"paramName": "steps",
	"type": "INTEGER",
	"controlType": "number",
	"displayName": "推理步数",
	"defaultValue": 20,
	"min": 1,
	"max": 50,
	"step": 1
}
```

### 开关字段

```json
{
	"id": "271_face",
	"nodeId": "271",
	"paramName": "face",
	"type": "BOOLEAN",
	"controlType": "switch",
	"displayName": "启用人脸检测",
	"defaultValue": true
}
```

## 注意事项

1. **字段ID唯一性**: 每个字段的id必须唯一
2. **节点存在性**: nodeId必须存在于默认参数中
3. **参数名匹配**: paramName必须与默认参数中节点的inputs参数名匹配
4. **必填字段**: 图像类型字段通常设为required: true
5. **默认值**: defaultValue会作为表单的初始值显示
