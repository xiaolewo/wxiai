Nano-banana (文生图)
POST
/v1/images/generations
最后修改时间：
6 天前
Nano-banana 和 gemini-2.5-flash-image-preview 的区别
gemini-2.5-flash-image-preview 官方的api模型，没做任何处理，仅支持聊天接口，可能不会返回图片，返回的图片是 base64
nano-banana 我们基于 gemini-2.5-flash-image-preview 专门画图优化的api模型，支持 dalle 格式、返回url，失败不扣费，优化了支持设置图片比例（图生图不支持设置比例）
nano-banana-hd 是高清版4K画质
请求参数
Header 参数
Authorization
string
可选
默认值:
Bearer {{YOUR_API_KEY}}
Body 参数
application/json
model
string
必需
prompt
string
必需
aspect_ratio
enum<string>
必需
枚举值:
4:3
3:4
16:9
9:16
2:3
3:2
response_format
string
可选
url 或 b64_json
image_urls
array[string]
可选
示例
{
"prompt": "cat",
"model": "nano-banana"
}
请求示例代码
http.client
Requests
import http.client
import json

conn = http.client.HTTPSConnection("")
payload = json.dumps({
"prompt": "cat",
"model": "nano-banana"
})
headers = {
'Authorization': 'Bearer {{YOUR_API_KEY}}',
'Content-Type': 'application/json'
}
conn.request("POST", "/v1/images/generations", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
返回响应
🟢200
成功
application/json
object

示例
{}
