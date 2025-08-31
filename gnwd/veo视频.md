Google Veo 视频生成 API 文档


包含三个接口
文生视频 文本生成视频
图生视频 图像生成视频
查询与获取结果

一 文生视频 API

接口地址
POST {{BASE_URL}}/google/v1/models/veo/videos

Header

参数 Content-Type
类型 string
必需 是
示例值 application/json

参数 Authorization
类型 string
必需 否
示例值 Bearer {{YOUR_API_KEY}}

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

可选模型
veo3
veo3-fast
veo3-pro
veo3-pro-frames
veo2
veo2-fast
veo2-fast-frames
veo2-fast-components
veo2-pro
veo3-fast-frames

请求示例
import http.client
import json

conn = http.client.HTTPSConnection("{{BASE_URL}}")
payload = json.dumps({
   "prompt": "A futuristic city with flying cars",
   "model": "veo3",
   "enhance_prompt": True
})
headers = {
   "Authorization": "Bearer {{YOUR_API_KEY}}",
   "Content-Type": "application/json"
}
conn.request("POST", "/google/v1/models/veo/videos", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

返回示例
{
    "code": "success",
    "message": "",
    "data": "f0aa213c-c09e-4e19-a0e5-c698fe48acf1"
}


字段说明
code string 状态码 success 表示成功
message string 额外消息 可为空
data string 任务 ID

二 图生视频 API

接口地址
POST {{BASE_URL}}/google/v1/models/veo/videos

注意事项
当模型是 veo3-pro-frames 最多支持 1 个首帧
当模型是 veo2-fast-frames 最多支持 2 张图 分别是首尾帧
当模型是 veo2-fast-components 最多支持 3 张图 作为视频元素

Header

参数 Content-Type
类型 string
必需 是
示例值 application/json

参数 Authorization
类型 string
必需 否
示例值 Bearer {{YOUR_API_KEY}}

Body application/json

参数 prompt
类型 string
必需 是
说明 视频生成提示词

参数 model
类型 enum string
必需 是
说明 选择生成模型

参数 enhance_prompt
类型 boolean
必需 是
说明 是否优化提示词

参数 images
类型 array string
必需 是
说明 图片数组 url 或 base64 数量依模型限制

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

返回示例
{
    "code": "success",
    "message": "",
    "data": "f0aa213c-c09e-4e19-a0e5-c698fe48acf1"
}


字段说明
code string 状态码
message string 额外消息
data string 任务 ID

三 查询与获取结果 API

接口地址
GET {{BASE_URL}}/google/v1/tasks/{task_id}

任务状态
NOT_START 未启动
SUBMITTED 已提交
IN_PROGRESS 执行中
FAILURE 失败
SUCCESS 成功

Path

task_id string 必需 是 视频生成任务 ID

Header

参数 Content-Type
类型 string
必需 是
示例值 application/json

参数 Authorization
类型 string
必需 否
示例值 Bearer {{YOUR_API_KEY}}

请求示例
import http.client
import json

conn = http.client.HTTPSConnection("{{BASE_URL}}")
payload = ""
headers = {
   "Authorization": "Bearer {{YOUR_API_KEY}}",
   "Content-Type": "application/json"
}
conn.request("GET", "/google/v1/tasks/f0aa213c-c09e-4e19-a0e5-c698fe48acf1", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

返回示例
{
    "code": "success",
    "message": "",
    "data": {
        "task_id": "f0aa213c-c09e-4e19-a0e5-c698fe48acf1",
        "notify_hook": "",
        "action": "google-videos",
        "status": "SUCCESS",
        "fail_reason": "",
        "submit_time": 1750221308,
        "start_time": 0,
        "finish_time": 1750221572,
        "progress": "100%",
        "data": {
            "id": "f0aa213c-c09e-4e19-a0e5-c698fe48acf1",
            "status": "completed",
            "video_url": "https://filesystem.site/cdn/20250618/a5O3efr3GyiSTIMxAtXYmCWKcNPjBL.mp4",
            "status_update_time": 1750221453056
        }
    }
}

字段说明

code string 状态码
message string 额外消息
data object 任务详情

任务详情字段
task_id string 任务 ID
notify_hook string 回调地址
action string 动作类型
status string 任务状态
fail_reason string 失败原因
submit_time number 提交时间戳
start_time number 开始时间戳
finish_time number 完成时间戳
progress string 任务进度百分比

data 内部字段
id string 视频 ID
status string 视频状态
video_url string 视频下载地址
status_update_time number 状态更新时间