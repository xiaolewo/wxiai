# 视频生成工作流配置

基于你提供的哩布节点示例，这里是完整的工作流配置：

## 工作流信息

- **名称**: 图像转视频生成
- **描述**: 从静态图像生成动态视频，支持自定义提示词和参数控制
- **模板UUID**: `4df2efa0f18d46dc9758803e478eb51c`
- **工作流UUID**: `0d6d523cb5664b2ea44f1d7221fc8270`
- **输出类型**: 视频（MP4格式）

## 1. 参数结构 (Parameter Schema)

```json
{
	"fields": [
		{
			"name": "image",
			"displayName": "上传图像",
			"type": "IMAGE",
			"id": "image",
			"parentId": 67,
			"image_upload": true,
			"isMaskImage": false,
			"required": true,
			"accept": "image/*",
			"tooltip": "上传要转换为视频的静态图像"
		},
		{
			"name": "text",
			"displayName": "视频描述提示词",
			"type": "STRING",
			"id": "text",
			"parentId": 137,
			"multiline": true,
			"rows": 8,
			"required": true,
			"defaultValue": "The camera zooms out to reveal a young girl's full body. Create a video from the given image featuring this young girl. Initially, she starts to spin gently in place, with her arms slightly out and her long hair swaying rhythmically.\nAs time progresses, her spinning speed increases at an abnormal and impossible rate that defies the laws of physics. Her clothes, made of light and flowing materials like cotton and linen, are affected by the intense centrifugal force.\nThe outer layers of her clothing, such as her shirt and pants, begin to flutter and then are gradually flung off. The process of the clothes being thrown away is shown in a short - term slow - motion, enabling viewers to clearly observe the swirling garments.\nAs she continues to spin at this super - fast speed, a magical transformation occurs. The young girl gradually morphs into a little girl. Eventually, when the spinning slows down, it's a little girl left wearing only a camisole bodysuit lingerie.\nUse a bright and vivid color scheme with a touch of a surreal filter to enhance the dreamy and otherworldly feel. The lighting should be soft and create a warm, glowing effect around the little girl. Add dynamic sound effects of wind and a faint, otherworldly musical tone to accompany her spinning. The video should have a seamless transition from the gentle start to the extremely fast spinning and the subsequent transformation, and maintain high - quality resolution and a smooth frame rate.",
			"tooltip": "详细描述要生成的视频内容、动作、风格等"
		},
		{
			"name": "value",
			"displayName": "最长边分辨率",
			"type": "INT",
			"id": "value",
			"parentId": 102,
			"defaultValue": 920,
			"min": 512,
			"max": 2048,
			"step": 8,
			"required": true,
			"tooltip": "视频输出的最长边分辨率，建议920-1280"
		},
		{
			"name": "Value",
			"displayName": "视频时长（秒）",
			"type": "FLOAT",
			"id": "Value",
			"parentId": 133,
			"defaultValue": 5,
			"min": 1,
			"max": 10,
			"step": 0.5,
			"required": true,
			"tooltip": "生成视频的时长，单位为秒"
		}
	]
}
```

## 2. 默认参数 (Default Params)

```json
{
	"67": {
		"class_type": "LoadImage",
		"inputs": {
			"image": "https://liblibai-tmp-image.liblib.cloud/img/7c60fd65c04146039ee50bc461afa80d/52721acc1691cc11db64b307c969ce3b5d401d554ec5e4ec4f8c3aa8e64bbedf.png"
		}
	},
	"102": {
		"class_type": "JWInteger",
		"inputs": {
			"value": 920
		}
	},
	"133": {
		"class_type": "DF_Integer",
		"inputs": {
			"Value": 5
		}
	},
	"137": {
		"class_type": "JjkText",
		"inputs": {
			"text": "The camera zooms out to reveal a young girl's full body. Create a video from the given image featuring this young girl. Initially, she starts to spin gently in place, with her arms slightly out and her long hair swaying rhythmically.\nAs time progresses, her spinning speed increases at an abnormal and impossible rate that defies the laws physics. Her clothes, made of light and flowing materials like cotton and linen, are affected by the intense centrifugal force.\nThe outer layers of her clothing, such as her shirt and pants, begin to flutter and then are gradually flung off. The process of the clothes being thrown away is shown in a short - term slow - motion, enabling viewers to clearly observe the swirling garments.\nAs she continues to spin at this super - fast speed, a magical transformation occurs. The young girl gradually morphs into a little girl. Eventually, when the spinning slows down, it's a little girl left wearing only a camisole bodysuit lingerie.\nUse a bright and vivid color scheme with a touch of a surreal filter to enhance the dreamy and otherworldly feel. The lighting should be soft and create a warm, glowing effect around the little girl. Add dynamic sound effects of wind and a faint, otherworldly musical tone to accompany her spinning. The video should have a seamless transition from the gentle start to the extremely fast spinning and the subsequent transformation, and maintain high - quality resolution and a smooth frame rate."
		}
	},
	"workflowUuid": "0d6d523cb5664b2ea44f1d7221fc8270"
}
```

## 3. 工作流基本设置

```json
{
	"template_uuid": "4df2efa0f18d46dc9758803e478eb51c",
	"workflow_uuid": "0d6d523cb5664b2ea44f1d7221fc8270",
	"name": "AI图像转视频",
	"description": "将静态图像转换为动态视频，支持自定义动作描述和视频参数",
	"category": "视频生成",
	"base_credits": 40,
	"complexity_multiplier": 1.0,
	"enabled": true,
	"is_public": true,
	"sort_order": 10
}
```

## 4. 节点说明

| 节点ID | 节点类型   | 功能说明         | 参数项                 |
| ------ | ---------- | ---------------- | ---------------------- |
| 67     | LoadImage  | 加载输入图像     | image - 用户上传的图片 |
| 137    | JjkText    | 多语言提示词处理 | text - 视频描述文本    |
| 102    | JWInteger  | 分辨率控制       | value - 最长边像素值   |
| 133    | DF_Integer | 时长控制         | Value - 视频秒数       |

## 5. 输出说明

- **输出类型**: 视频文件(.mp4)
- **输出路径**: `videos[0].videoUrl`
- **封面图**: `videos[0].coverPath`
- **预估积分消耗**: 40积分左右
- **处理时间**: 约2-5分钟

## 6. 使用建议

### 图像要求

- 格式: JPG, PNG
- 分辨率: 建议512x512以上
- 内容: 清晰的主体，适合动画化

### 提示词建议

- 详细描述动作和变化
- 包含视觉风格描述
- 指定转场效果
- 描述光线和色彩

### 参数调优

- **分辨率**: 920适合大多数场景，高质量可选1280
- **时长**: 3-6秒比较合适，太长可能质量下降

## 7. 注意事项

⚠️ **内容审核**: 生成的视频会经过审核，请确保内容符合平台规范
⚠️ **积分消耗**: 视频生成消耗较高，建议先用低分辨率测试
⚠️ **处理时间**: 视频生成比图像生成耗时更长，请耐心等待
