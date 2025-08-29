Google Veo 图生视频 API

接口地址
POST {{BASE_URL}}/google/v1/models/veo/videos

最后修改时间 大约 1 个月前

注意事项
当模型是 veo3-pro-frames 时 最多支持 1 个首帧
当模型是 veo2-fast-frames 时 最多支持 2 张图 分别是首尾帧
当模型是 veo2-fast-components 时 最多支持 3 张图 作为视频中的元素

请求参数
Header

参数 Content-Type
类型 string
必需 是
示例值 application/json
说明 固定值

参数 Authorization
类型 string
必需 否
示例值 Bearer {{YOUR_API_KEY}}
说明 API Key 鉴权

Body application/json

参数 prompt
类型 string
必需 是
说明 视频生成提示词 仅支持英文 若为中文需配合 enhance_prompt true 自动翻译

参数 model
类型 enum string
必需 是
说明 选择生成模型

参数 enhance_prompt
类型 boolean
必需 是
说明 是否优化提示词 中文会自动转成英文

参数 images
类型 array string
必需 是
说明 输入图片数组 URL 或 Base64 编码 数量依模型限制 1 到 3 张

可选模型
veo2
veo2-fast
veo2-fast-frames
veo2-fast-components
veo2-pro
veo3
veo3-fast
veo3-pro
veo3-pro-frames

请求示例

Python http.client

import http.client
import json

conn = http.client.HTTPSConnection("{{BASE_URL}}")

payload = json.dumps({
"prompt": "A forest turning into a futuristic city",
"model": "veo3-pro-frames",
"enhance_prompt": True,
"images": [
"https://example.com/frame1.png"
]
})

headers = {
"Authorization": "Bearer {{YOUR_API_KEY}}",
"Content-Type": "application/json"
}

conn.request("POST", "/google/v1/models/veo/videos", payload, headers)
res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

返回响应

成功响应 200 OK

{
"code": "success",
"message": "",
"data": "f0aa213c-c09e-4e19-a0e5-c698fe48acf1"
}

字段说明
code 类型 string 说明 状态码 success 表示成功
message 类型 string 说明 额外消息 可为空
data 类型 string 说明 任务ID 用于查询视频生成进度或获取结果
