Google Veo 查询与获取结果 API

接口地址
GET {{BASE_URL}}/google/v1/tasks/{task_id}

最后修改时间 大约 1 个月前

任务状态说明
NOT_START 未启动
SUBMITTED 已提交处理
IN_PROGRESS 执行中
FAILURE 失败
SUCCESS 成功

请求参数
Path

参数 task_id
类型 string
必需 是
说明 视频生成任务 ID

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

请求示例

Python http.client

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

返回响应

成功响应 200 OK

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

顶层字段
code 类型 string 说明 状态码 success 表示成功
message 类型 string 说明 额外消息 可为空
data 类型 object 说明 任务详情

任务详情字段
task_id 类型 string 说明 任务 ID
notify_hook 类型 string 说明 回调地址 可为空
action 类型 string 说明 动作类型 google-videos
status 类型 string 说明 任务状态
fail_reason 类型 string 说明 失败原因 若有错误则返回
submit_time 类型 number 说明 提交时间 时间戳
start_time 类型 number 说明 开始时间 时间戳
finish_time 类型 number 说明 完成时间 时间戳
progress 类型 string 说明 任务进度 百分比

data 内部字段
id 类型 string 说明 视频 ID
status 类型 string 说明 视频状态 completed 表示完成
video_url 类型 string 说明 视频下载地址
status_update_time 类型 number 说明 最近状态更新时间 时间戳
