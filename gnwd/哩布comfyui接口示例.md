8.1 ComfyUI工作流生图

- 接口：POST /api/generate/comfyui/app
- headers：
  header
  value
  备注
  Content-Type
  application/json

- 请求body：
  参数
  类型
  是否必需
  说明
  备注
  templateUuid
  string
  否
  默认模版：4df2efa0f18d46dc9758803e478eb51c

generateParams
object
是
生图参数，json结构
前端自动创建该工作流版本的API参数示例

1. 目前Lib已开放全站的可商用、可在线运行工作流供API使用，您可以在Lib站内工作流合集检索，https://www.liblib.art/workflows
   [图片]
2. 在工作流的详情页会出现【本工作流已提供API服务】，且可查看API相关参数。（详情页未出现API参数的工作流，暂不支持API调用）
   [图片]
   [图片]

- 返回值：
  参数
  类型
  备注
  generateUuid
  string
  生图任务uuid，使用该uuid查询生图进度
- 参数示例
  request_body ={
  "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
  "generateParams": {
  "12": {
  "class_type": "LoadImage",
  "inputs": {
  "image": "https://liblibai-tmp-image.liblib.cloud/img/baf2e419ce1cb06812314957efd2e067/af0c523d3d2b4092ab45c64c72e4deb76babb12e9b8a178eb524143c3b71bf85.png"
  }
  },
  "112": {
  "class_type": "ImageScale",
  "inputs": {
  "width": 768
  }
  },
  "136": {
  "class_type": "RepeatLatentBatch",
  "inputs": {
  "amount": 4
  }
  },
  "137": {
  "class_type": "LatentUpscaleBy",
  "inputs": {
  "scale_by": 1.5
  }
  },
  "workflowUuid": "2f22ab7ce4c044afb6d5eee2e61547f3"
  }
  }
- 参数说明示例（仅少量节点）
  节点ID
  节点类型
  节点名称
  参数项
  参数名称
  参数说明
  80

LoadImage

风格图像

image
图像

{
"parentId": 80,
"id": "image",
"name": "image",
"displayName": "图像",
"type": "IMAGE",
"defaultValue": "https://liblibai-online.liblib.cloud/img/081e9f07d9bd4c2ba090efde163518f9/aa1a1459986e5cc2b1236f7dc43a029119d6fe6ac26f1961a6639d21ca0b0bbe.png",
"image_upload": true,
"isMaskImage": false
}
79
ApplyIPAdapterFlux
风格设置

weight
风格强度

{
"parentId": 79
"id": "weight",
"name": "weight",
"displayName": "风格强度",
"type": "FLOAT",
"defaultValue": 0.75,
"min": -1,
"max": 5,
"step": 0.05  
}
76

SeargePromptCombiner
请描述要绘制的画面

prompt1
画面描述

{
"parentId": 76,
"id": "prompt1",
"name": "prompt1",
"displayName": "画面描述",
"type": "STRING",
"defaultValue": "Anime art, low angle shot back view silhouette of a boy standing on a building rooftop next to a telescope at night, looking up towards the glowing milky way and shooting stars in the starry night, gradient blue orange and pink night sky, dim lighting, dark lighting, highly detailed, ultra-high resolutions, 32K UHD, best quality, masterpiece\n",
},

8.2 查询生图结果

- 接口：POST /api/generate/comfy/status
- headers：
  header
  value
  备注
  Content-Type
  application/json

- 请求body：
  参数
  类型
  是否必需
  备注
  generateUuid
  string
  是
  生图任务uuid，发起生图任务时返回该字段
- 返回值：
  参数
  类型
  备注
  generateUuid
  string
  生图任务uuid，使用该uuid查询生图进度
  generateStatus
  int
  生图任务的执行状态：
- 1：等待执行
- 2：执行中
- 3：已生图
- 4：审核中
- 5：任务成功
- 6：任务失败
  percentCompleted
  float
  生图进度，0到1之间的浮点数，（暂未实现）
  generateMsg
  string
  生图信息，提供附加信息，如生图失败信息
  pointsCost
  int
  本次生图任务消耗积分数
  accountBalance
  int
  账户剩余积分数
  images
  []object
  图片列表，只提供审核通过的图片
  images.0.imageUrl
  string
  图片地址，可直接访问，地址有时效性：7天
  images.0.seed
  int
  随机种子值
  iamges.0.auditStatus
  int
  审核状态：
- 1：待审核
- 2：审核中
- 3：审核通过
- 4：审核拦截
- 5：审核失败
  videos
  []object
  图片列表，只提供审核通过的图片
  videos.0.videoUrl
  string
  视频列表，只提供审核通过的视频
  videos.0.coverPath
  string
  视频地址，可直接访问，地址有时效性：7天
  videos.0.nodeId
  string
  输出视频的节点ID（可忽略）
  videos.0.outputName
  string
  输出视频的节点名称
  videos.0.auditStatus
  int
  审核状态：
- 1：待审核
- 2：审核中
- 3：审核通过
- 4：审核拦截
- 5：审核失败
  示例：
  {
  "code": 0,
  "data": {
  "accountBalance": 91111,
  "generateStatus": 5,
  "generateUuid": "a996794faff8424a8ff56acb421e7305",
  "images": [
  {
  "auditStatus": 3,
  "imageUrl": "https://liblibai-tmp-image.liblib.cloud/img/360643a3d8414af8b99664b208bc9302/35801ecbf6e6ea8ad89c2606b68d30dfc9579713f5d917694d1616c57afe82fb.png",
  "nodeId": "91",
  "outputName": "SaveImage"
  }
  ],
  "percentCompleted": 1,
  "pointsCost": 10,
  "videos": []
  },
  "msg": ""
  }}

  8.3 部分工作流推荐
  全量请至https://www.liblib.art/workflows挑选。
  使用以下工作流时，只有inputs中的参数是需要自定义的，其他部分请不要动。
  功能方向
  链接
  API参数
  标准版*按分辨率缩放
  比较推荐，很快
  https://www.liblib.art/modelinfo/1bf585fa9ae7455395ee7a595c3920a3?from=personal_page&versionUuid=fa2e042e32fa4aabbbacc255b4ab2cca
  {
  "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
  "generateParams": {
  "workflowUuid": "fa2e042e32fa4aabbbacc255b4ab2cca",
  "30":
  {
  "class_type": "LoadImage",
  "inputs":
  {
  "image": "https://liblibai-online.liblib.cloud/img/081e9f07d9bd4c2ba090efde163518f9/5fae2d9099c208487bc97867bece2bf3d904068e307c7bd30c646c9f3059af33.png"
  }
  },
  "31":
  {
  "class_type": "ImageScale",
  "inputs":
  {
  "width": 2048,
  "height": 2048
  }
  }
  }
  }
  标准版*按系数放大

https://www.liblib.art/modelinfo/1bf585fa9ae7455395ee7a595c3920a3?from=personal_page&versionUuid=9a1c74ae498640c28e4269958b1a1b15
{
"templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
"generateParams": {
"workflowUuid": "9a1c74ae498640c28e4269958b1a1b15",
"30":
{
"class_type": "LoadImage",
"inputs":
{
"image": "https://liblibai-online.liblib.cloud/img/081e9f07d9bd4c2ba090efde163518f9/5fae2d9099c208487bc97867bece2bf3d904068e307c7bd30c646c9f3059af33.png"
}
},
"37":
{
"class_type": "CR Upscale Image",
"inputs":
{
"upscale_model": "ESRGAN_4x",
"rescale_factor": 2
}
}
}
}
SD放大
https://www.liblib.art/modelinfo/1bf585fa9ae7455395ee7a595c3920a3?from=personal_page&versionUuid=b2c5e10ee73d4cf69a0e51cb1cbc1622
{
"templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
"generateParams": {
"workflowUuid": "b2c5e10ee73d4cf69a0e51cb1cbc1622",
"30":
{
"class_type": "UltimateSDUpscale",
"inputs":
{
"upscale_by": 2,
"steps": 30
}
},
"40":
{
"class_type": "LoadImage",
"inputs":
{
"image": "https://liblibai-online.liblib.cloud/img/081e9f07d9bd4c2ba090efde163518f9/5fae2d9099c208487bc97867bece2bf3d904068e307c7bd30c646c9f3059af33.png"
}
},
"41":
{
"class_type": "UpscaleModelLoader",
"inputs":
{
"model_name": "ESRGAN_4x"
}
}  
 }
}
图像外扩
https://www.liblib.art/modelinfo/ef740b8a4f384db48fcf9f208372493a?from=personal_page&versionUuid=99fa146a003743bdb676179fa2e546ca
{
"templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
"generateParams": {
"workflowUuid": "99fa146a003743bdb676179fa2e546ca",
"17":
{
"class_type": "LoadImage",
"inputs":
{
"image": "https://liblibai-online.liblib.cloud/img/081e9f07d9bd4c2ba090efde163518f9/ed68325cbfcf4b8f724b6b5aa5914e7d91358c3bbf81fccd5002950a2f8180df.png"
}
},
"23":
{
"class_type": "CLIPTextEncode",
"inputs":
{
"text": "beautiful scenery"
}
},
"44":
{
"class_type": "ImagePadForOutpaint",
"inputs":
{
"left": 400,
"top": 400,
"right": 400,
"bottom": 400,
"feathering": 24
}
}  
 }
}
