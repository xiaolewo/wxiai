如果每个应用的工作流都不一样，用户端的控件怎么办，比如现在这一个是可以上传两个图的，但是设想另外一个只能上传一个图。这如何解决，我先给你提供一个哩布哩布的某个工作流的参数，你看看怎么才能配置添加工作流应用合适：

第一个：
API参考：
API开放平台
API接口文档
以下参数来自快捷应用：高清换脸-在线生图
接口请求：
POSThttps://openapi.liblibai.cloud/api/generate/comfyui/app
参数示例
JSON
复制
{
"templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
"generateParams": {
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
"image": "https://liblibai-tmp-image.liblib.cloud/img/ab7d75d067294d3b84a7583f9d551f71/d3a9fd5622587b1d2b4873e44d0b1c5738f749f1dd150a87124d3ec8cec2c988.jpg"
}
},
"49": {
"class_type": "LoadImage",
"inputs": {
"image": "https://liblibai-tmp-image.liblib.cloud/img/84cd9ecbef5b4333afb1125200e50242/8705b03e7de6aaafdfd0c806e7b8864f437d4b2d2f1ddc34e94f6335d6c7c6cf.png"
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
}
参数说明
节点ID 节点类型 节点名称 参数项 参数名称 参数说明
49 LoadImage 上传脸部图
image
图像
{
"name": "image",
"displayName": "图像",
"type": "IMAGE",
"defaultValue": "img/84cd9ecbef5b4333afb1125200e50242/8705b03e7de6aaafdfd0c806e7b8864f437d4b2d2f1ddc34e94f6335d6c7c6cf.png",
"image_upload": true,
"parentId": 49,
"id": "image",
"isMaskImage": false
}
40 LoadImage 上传海报图
image
图像
{
"name": "image",
"displayName": "图像",
"type": "IMAGE",
"defaultValue": "img/ab7d75d067294d3b84a7583f9d551f71/d3a9fd5622587b1d2b4873e44d0b1c5738f749f1dd150a87124d3ec8cec2c988.jpg",
"image_upload": true,
"parentId": 40,
"id": "image",
"isMaskImage": false
}
28 CLIPTextEncode CLIP文本编码器（正）
text
文本
{
"name": "text",
"displayName": "文本",
"type": "STRING",
"multiline": true,
"dynamicPrompts": true,
"tooltip": "The text to be encoded.",
"defaultValue": "Perfect skin",
"parentId": 28,
"id": "text"
}
27 CLIPTextEncode CLIP文本编码器（反）
text
文本
{
"name": "text",
"displayName": "文本",
"type": "STRING",
"multiline": true,
"dynamicPrompts": true,
"tooltip": "The text to be encoded.",
"defaultValue": "freckles",
"parentId": 27,
"id": "text"
}
271 LayerMask: PersonMaskUltra V2 人像遮罩 Ultra V2
face
面部
{
"name": "face",
"displayName": "面部",
"type": "BOOLEAN",
"defaultValue": true,
"label_on": "enabled",
"label_off": "disabled",
"parentId": 271,
"id": "face"
}
hair
头发
{
"name": "hair",
"displayName": "头发",
"type": "BOOLEAN",
"defaultValue": false,
"label_on": "enabled",
"label_off": "disabled",
"parentId": 271,
"id": "hair"
}
查询生图结果
POSThttps://openapi.liblibai.cloud/api/generate/comfy/status
查询结果示意
JSON
复制
{
"code": 0,
"data": {
"accountBalance": 199617897,
"generateStatus": 5,
"generateUuid": "99c937212cb445709cf8b5cd83c16b4b",
"images": [
{
"auditStatus": 3,
"imageUrl": "https://liblibai-tmp-image.liblib.cloud/img/360643a3d8414af8b99664b208bc9302/8926ff2decac4924d4f9860558336e5b305f9cc74f0ebaecc39f5c52e828dbd8.png",
"nodeId": "328",
"outputName": "SaveImage"
}
],
"percentCompleted": 1,
"pointsCost": 10,
"videos": []
},
"msg": ""
}}
返回值说明
参数 类型 备注
generateUuid string 生图任务uuid，使用该uuid查询生图进度
generateStatus int
生图任务的执行状态：
1：等待执行
2：执行中
3：已生图
4：审核中
5：任务成功
6：任务失败
percentCompleted float 生图进度，0到1之间的浮点数
generateMsg string 生图信息，提供附加信息，如生图失败信息
images []object 图片列表，只提供审核通过的图片
images.0.imageUrl string 图片地址，可直接访问，地址有时效性：7天
images.0.auditStatus int
审核状态：
1：待审核
2：审核中
3：审核通过
4：审核拦截
5：审核失败
videos []object 图片列表，只提供审核通过的图片
videos.0.videoUrl string 视频列表，只提供审核通过的视频
videos.0.coverPath string 视频地址，可直接访问，地址有时效性：7天
videos.0.nodeId string 输出视频的节点ID（可忽略）
videos.0.outputName string 输出视频的节点名称
videos.0.auditStatus int
审核状态：
1：待审核
2：审核中
3：审核通过
4：审核拦截
5：审核失败

第二个：
API参考：
API开放平台
API接口文档
以下参数来自快捷应用：supir高清放大-在线生图
接口请求：
POSThttps://openapi.liblibai.cloud/api/generate/comfyui/app
参数示例
JSON
复制
{
"templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
"generateParams": {
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
}
参数说明
节点ID 节点类型 节点名称 参数项 参数名称 参数说明
2 LoadImage 加载图像
image
图像
{
"name": "image",
"displayName": "图像",
"type": "IMAGE",
"defaultValue": "img/84cd9ecbef5b4333afb1125200e50242/2b04302c9011b28337a6c992faa62c9447d64de71f41ea6a19e741d9873e1d4d.png",
"image_upload": true,
"id": "image",
"isMaskImage": false,
"parentId": 2
}
15 SUPIR_Upscale SUPIR放大
sdxl_model
SDXL模型
{
"name": "sdxl_model",
"displayName": "SDXL模型",
"type": "MODEL",
"defaultValue": 827118,
"id": "sdxl_model",
"parentId": 15
}
steps
步数
{
"name": "steps",
"displayName": "步数",
"type": "INT",
"defaultValue": 45,
"min": 3,
"max": 4096,
"step": 1,
"id": "steps",
"parentId": 15
}
查询生图结果
POSThttps://openapi.liblibai.cloud/api/generate/comfy/status
查询结果示意
JSON
复制
{
"code": 0,
"data": {
"accountBalance": 199617284,
"generateStatus": 5,
"generateUuid": "f5cec07d3bd04c5ba16a1eba741926f3",
"images": [
{
"auditStatus": 3,
"imageUrl": "https://liblibai-tmp-image.liblib.cloud/img/360643a3d8414af8b99664b208bc9302/92fcd48d4efc9480b18faea831aa89389cea3e7ab8cb46fd70a6fdb0e3b4fbe5.png",
"nodeId": "29",
"outputName": "SaveImage"
}
],
"percentCompleted": 1,
"pointsCost": 16,
"videos": []
},
"msg": ""
}}
返回值说明
参数 类型 备注
generateUuid string 生图任务uuid，使用该uuid查询生图进度
generateStatus int
生图任务的执行状态：
1：等待执行
2：执行中
3：已生图
4：审核中
5：任务成功
6：任务失败
percentCompleted float 生图进度，0到1之间的浮点数
generateMsg string 生图信息，提供附加信息，如生图失败信息
images []object 图片列表，只提供审核通过的图片
images.0.imageUrl string 图片地址，可直接访问，地址有时效性：7天
images.0.auditStatus int
审核状态：
1：待审核
2：审核中
3：审核通过
4：审核拦截
5：审核失败
videos []object 图片列表，只提供审核通过的图片
videos.0.videoUrl string 视频列表，只提供审核通过的视频
videos.0.coverPath string 视频地址，可直接访问，地址有时效性：7天
videos.0.nodeId string 输出视频的节点ID（可忽略）
videos.0.outputName string 输出视频的节点名称
videos.0.auditStatus int
审核状态：
1：待审核
2：审核中
3：审核通过
4：审核拦截
5：审核失败
