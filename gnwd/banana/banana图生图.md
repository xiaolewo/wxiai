Nano-banana (图生图)
POST
/v1/images/edits
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
Body 参数multipart/form-data
model
string
必需
示例值:
nano-banana
prompt
string
必需
示例值:
一只猫
image
file
必需
支持多图或不带参考图
示例值:
["file://E:\\Downloads\\1745936044575403500.png","file://E:\\Downloads\\微信图片_20250826114255_1785.jpg"]
response_format
string
可选
url 或 b64_json
示例值:
url
请求示例代码
http.client
Requests
import http.client
import mimetypes
from codecs import encode

conn = http.client.HTTPSConnection("")
dataList = []
boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
dataList.append(encode('--' + boundary))
dataList.append(encode('Content-Disposition: form-data; name=model;'))

dataList.append(encode('Content-Type: {}'.format('text/plain')))
dataList.append(encode(''))

dataList.append(encode("nano-banana"))
dataList.append(encode('--' + boundary))
dataList.append(encode('Content-Disposition: form-data; name=prompt;'))

dataList.append(encode('Content-Type: {}'.format('text/plain')))
dataList.append(encode(''))

dataList.append(encode("一只猫"))
dataList.append(encode('--' + boundary))
dataList.append(encode('Content-Disposition: form-data; name=image; filename={0}'.format('E:\\Downloads\\1745936044575403500.png')))

fileType = mimetypes.guess_type('E:\\Downloads\\1745936044575403500.png')[0] or 'application/octet-stream'
dataList.append(encode('Content-Type: {}'.format(fileType)))
dataList.append(encode(''))

with open('E:\Downloads\1745936044575403500.png', 'rb') as f:
dataList.append(f.read())
dataList.append(encode('--' + boundary))
dataList.append(encode('Content-Disposition: form-data; name=image; filename={0}'.format('E:\\Downloads\\微信图片\_20250826114255_1785.jpg')))

fileType = mimetypes.guess_type('E:\\Downloads\\微信图片\_20250826114255_1785.jpg')[0] or 'application/octet-stream'
dataList.append(encode('Content-Type: {}'.format(fileType)))
dataList.append(encode(''))

with open('E:\Downloads\微信图片\_20250826114255_1785.jpg', 'rb') as f:
dataList.append(f.read())
dataList.append(encode('--' + boundary))
dataList.append(encode('Content-Disposition: form-data; name=response_format;'))

dataList.append(encode('Content-Type: {}'.format('text/plain')))
dataList.append(encode(''))

dataList.append(encode("url"))
dataList.append(encode('--'+boundary+'--'))
dataList.append(encode(''))
body = b'\r\n'.join(dataList)
payload = body
headers = {
'Authorization': 'Bearer {{YOUR_API_KEY}}',
'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
}
conn.request("POST", "/v1/images/edits", payload, headers)
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
