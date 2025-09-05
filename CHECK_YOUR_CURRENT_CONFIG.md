# 检查你当前的工作流配置

## 问题分析

根据日志和你提供的数据，问题可能有两个：

### 1. 字段ID映射问题

你的前端发送数据：

```json
{
	"image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABWcA…",
	"sdxl_model": "e18fe70ddebd42a8b0fc9351c6469948",
	"steps": 45
}
```

但你的参数结构配置是：

```json
{
	"id": "sdxl_model",
	"parentId": 15
}
```

**问题**：字段ID应该是 `"15_sdxl_model"`，这样后端才能正确映射到节点15。

### 2. Template UUID中的模型限制

Template UUID `4df2efa0f18d46dc9758803e478eb51c` 可能内部使用了不可商用的模型。

## 即时解决方案

### 选项1：修正参数结构配置（推荐）

将参数结构改为：

```json
{
	"fields": [
		{
			"id": "2_image", // 修正：使用节点ID前缀
			"nodeId": "2",
			"paramName": "image",
			"name": "image",
			"type": "IMAGE",
			"controlType": "imageUpload"
		},
		{
			"id": "15_sdxl_model", // 修正：使用节点ID前缀
			"nodeId": "15",
			"paramName": "sdxl_model",
			"name": "sdxl_model",
			"type": "MODEL",
			"defaultValue": "e18fe70ddebd42a8b0fc9351c6469948"
		},
		{
			"id": "15_steps", // 修正：使用节点ID前缀
			"nodeId": "15",
			"paramName": "steps",
			"name": "steps",
			"type": "INTEGER",
			"controlType": "number",
			"defaultValue": 45
		}
	]
}
```

### 选项2：寻找可商用的Template UUID

联系哩布官方，获取使用可商用模型的SUPIR模板UUID。

## 测试步骤

1. **更新参数结构配置**：使用上面的正确格式
2. **重新保存工作流**：在管理员面板重新保存
3. **测试参数映射**：查看后端日志确认用户参数正确映射到节点
4. **检查模型使用**：确认最终发送给哩布API的参数中使用的是哪个模型

## 临时workaround

如果模型问题仍然存在，可以尝试：

1. 将默认参数中的 `sdxl_model` 改为其他可商用模型ID
2. 或者使用不同的Template UUID

---

**下一步**：请按照选项1修正参数结构配置，然后重新测试，查看后端日志确认参数映射是否正确。
