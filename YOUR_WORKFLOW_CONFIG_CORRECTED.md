# 你的工作流正确配置

基于你提供的工作流，这里是正确的配置格式：

## 1. 参数结构 (Parameter Schema)

```json
{
	"fields": [
		{
			"id": "2_image",
			"nodeId": "2",
			"paramName": "image",
			"name": "image",
			"displayName": "上传图像",
			"type": "IMAGE",
			"controlType": "imageUpload",
			"required": true,
			"accept": "image/*"
		},
		{
			"id": "15_sdxl_model",
			"nodeId": "15",
			"paramName": "sdxl_model",
			"name": "sdxl_model",
			"displayName": "SDXL模型",
			"type": "MODEL",
			"controlType": "select",
			"defaultValue": "e18fe70ddebd42a8b0fc9351c6469948"
		},
		{
			"id": "15_steps",
			"nodeId": "15",
			"paramName": "steps",
			"name": "steps",
			"displayName": "推理步数",
			"type": "INTEGER",
			"controlType": "number",
			"defaultValue": 45,
			"min": 3,
			"max": 4096,
			"step": 1,
			"required": true
		}
	]
}
```

## 2. 默认参数 (Default Params)

**注意**：不要包含 `templateUuid` 和 `generateParams` 嵌套结构，直接使用节点参数：

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
			"sdxl_model": "e18fe70ddebd42a8b0fc9351c6469948",
			"steps": 45
		}
	},
	"workflowUuid": "3e54edc7d52b4fa49644bfa92ad06c13"
}
```

## 修改说明

### 原配置的问题：

1. **字段ID不匹配**：你用了 `"id": "image"`，但应该是 `"id": "2_image"` 来明确映射到节点2
2. **嵌套结构**：默认参数不应该包含 `templateUuid` 和 `generateParams` 包装
3. **字段映射**：使用 `parentId` 是可以的，但推荐使用 `nodeId` 更清晰

### 修复后的效果：

- 用户上传的图像会正确映射到节点2的image参数
- 图像会先上传到云存储，然后传递云存储URL给哩布API
- 其他参数（模型和步数）也会正确映射

请使用修正后的配置重新保存工作流，然后测试图像上传功能。
