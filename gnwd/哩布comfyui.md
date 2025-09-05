你看看这个项目，我在这里面开发下面的功能，api地址和key也是在管理员面板配置的，然后我的意思是像后台添加应用似的添加comfyui的配置，然后配置积分扣除，你看看怎么配置好后台，配置什么才能调用工作流，公开的话就显示在前台的广场里面，用户点击哪个然后进入一个节点页面就使用，我数据库用的sqlite

2. 开始使用
   在这一部分，我们将展示如何开通API的权益，以及如何创建你的API密钥。
   2.1 访问地址
   Liblib开放平台域名：https://openapi.liblibai.cloud（无法直接打开，需配合密钥访问）
   2.2 计费规则
   非固定消耗，每次生图任务消耗的积分与以下参数有关：

- 选用模型
- 采样步数（steps）
- 采样方法（sampler，SDE系列会产生额外消耗）
- 生成图片宽度
- 生成图片高度
- 生成图片张数
- 重绘幅度（denoisingStrength）
- 高分辨率修复的重绘步数和重绘幅度
- Controlnet数量
  2.3 并发数和QPS
- 生图任务并发数，默认5（因生图需要时间，指同时可进行的生图任务数）
- 发起生图任务接口，QPS默认1秒1次，（可用每天预计生图张数/24h/60m/60s来估算平均值）
- 查询生图结果接口，QPS无限制
  2.4 生成API密钥
  在登录Liblib领取API试用积分或购买API积分后，Liblib会生成开放平台访问密钥，用于后续API接口访问，密钥包括：
- AccessKey，API访问凭证，唯一识别访问用户，长度通常在20-30位左右，如：KIQMFXjHaobx7wqo9XvYKA
- SecretKey，API访问密钥，用于加密请求参数，避免请求参数被篡改，长度通常在30位以上，如：KppKsn7ezZxhi6lIDjbo7YyVYzanSu2d
  2.4.1 使用密钥
  申请API密钥之后，需要在每次请求API接口的查询字符串中固定传递以下参数：
  参数
  类型
  是否必需
  说明
  AccessKey
  String
  是
  开通开放平台授权的访问AccessKey
  Signature
  String
  是
  加密请求参数生成的签名，签名公式见下节“生成签名”
  Timestamp
  String
  是
  生成签名时的毫秒时间戳，整数字符串，有效期5分钟
  SignatureNonce
  String
  是
  生成签名时的随机字符串
  如请求地址：https://test.xxx.com/api/genImg?AccessKey=KIQMFXjHaobx7wqo9XvYKA&Signature=test1232132&Timestamp=1725458584000&SignatureNonce=random1232
  2.4.2 生成签名
  签名生成公式如下：

# 1. 用"&"拼接参数

# URL地址：以上方请求地址为例，为“/api/genImg”

# 毫秒时间戳：即上节“使用密钥”中要传递的“Timestamp”

# 随机字符串：即上节“使用密钥”中要传递的“SignatureNonce”

原文 = URL地址 + "&" + 毫秒时间戳 + "&" + 随机字符串

# 2. 用SecretKey加密原文，使用hmacsha1算法

密文 = hmacSha1(原文, SecretKey)

# 3. 生成url安全的base64签名

# 注：base64编码时不要补全位数

签名 = encodeBase64URLSafeString(密文)
Java生成签名示例，以访问上方“使用密钥”的请求地址为例：
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.lang3.RandomStringUtils;

public class SignUtil {

    /**
     * 生成请求签名
     * 其中相关变量均为示例，请替换为您的实际数据
     */
    public static String makeSign() {

        // API访问密钥
        String secretKey = "KppKsn7ezZxhi6lIDjbo7YyVYzanSu2d";

        // 请求API接口的uri地址
        String uri = "/api/generate/webui/text2img";
        // 当前毫秒时间戳
        Long timestamp = System.currentTimeMillis();
        // 随机字符串
        String signatureNonce = RandomStringUtils.randomAlphanumeric(10);
        // 拼接请求数据
        String content = uri + "&" + timestamp + "&" + signatureNonce;

        try {
            // 生成签名
            SecretKeySpec secret = new SecretKeySpec(secretKey.getBytes(), "HmacSHA1");
            Mac mac = Mac.getInstance("HmacSHA1");
            mac.init(secret);
            return Base64.encodeBase64URLSafeString(mac.doFinal(content.getBytes()));
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("no such algorithm");
        } catch (InvalidKeyException e) {
            throw new RuntimeException(e);
        }
    }

}
Python生成签名示例，以访问上方“使用密钥”的请求地址为例：
import hmac
from hashlib import sha1
import base64
import time
import uuid

def make_sign():
"""
生成签名
"""

    # API访问密钥
    secret_key = 'KppKsn7ezZxhi6lIDjbo7YyVYzanSu2d'

    # 请求API接口的uri地址
    uri = "/api/genImg"
    # 当前毫秒时间戳
    timestamp = str(int(time.time() * 1000))
    # 随机字符串
    signature_nonce= str(uuid.uuid4())
    # 拼接请求数据
    content = '&'.join((uri, timestamp, signature_nonce))

    # 生成签名
    digest = hmac.new(secret_key.encode(), content.encode(), sha1).digest()
    # 移除为了补全base64位数而填充的尾部等号
    sign = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return sign

NodeJs 生成签名示例，以访问上方“使用密钥”的请求地址为例：
const hmacsha1 = require("hmacsha1");
const randomString = require("string-random");
// 生成签名
const urlSignature = (url) => {
if (!url) return;
const timestamp = Date.now(); // 当前时间戳
const signatureNonce = randomString(16); // 随机字符串，你可以任意设置，这个没有要求
// 原文 = URl地址 + "&" + 毫秒时间戳 + "&" + 随机字符串
const str = ${url}&${timestamp}&${signatureNonce};
  const secretKey = "官网上的 SecretKey "; // 下单后在官网中，找到自己的 SecretKey'
  const hash = hmacsha1(secretKey, str);
  // 最后一步： encodeBase64URLSafeString(密文)
  // 这一步很重要，生成安全字符串。java、Python 以外的语言，可以参考这个 JS 的处理
  let signature = hash
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
return {
signature,
timestamp,
signatureNonce,
};
};
// 例子：原本查询生图进度接口是 https://openapi.liblibai.cloud/api/generate/webui/status
// 加密后，url 就变更为 https://openapi.liblibai.cloud/api/generate/webui/status?AccessKey={YOUR_ACCESS_KEY}&Signature={签名}&Timestamp={时间戳}&SignatureNonce={随机字符串}
const getUrl = () => {
const url = "/api/generate/webui/status";
const { signature, timestamp, signatureNonce } = urlSignature(url);
const accessKey = "替换自己的 AccessKey"; // '下单后在官网中，找到自己的 AccessKey'
return ${url}?AccessKey=${accessKey}&Signature=${signature}&Timestamp=${timestamp}&SignatureNonce=${signatureNonce};
}; 8. ComfyUI工作流
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

8.4 个人工作流调用方法
需要编辑工作流后发布，务必看完6.4.2⚠️⚠️⚠️
6.4.1 发布本地工作流
个人本地搭建的ComfyUI工作流，需要先在LiblibAI主页右上方发布至平台，可按需选择【自见】，必须选【生成图片可出售或用于商业目的】。
[图片]
[图片]
[图片]

6.4.2 编辑工作流（⚠️⚠️⚠️易被忽略的步骤）
编辑方法，详见：LiblibAI--AI应用指南
节点适配范围和调整方式详见：ComfyUI FAQ
成功编辑好的工作流，会出现“运行应用”的button；若未出现，将无法调用API。
[图片]

6.4.3 发布工作流
我们需要约30秒-20分钟，自动试跑该工作流，试跑完成后，该工作流的详情页将会出现API调用参数，可完成API支持调用。
[图片]

8.5 工作流调用费用
每个工作流不同，消耗积分数可以参考API参数详情页左方试跑示范。
[图片]
