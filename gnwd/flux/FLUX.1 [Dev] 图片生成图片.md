# FLUX.1 [Dev] 图片生成图片

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-1/dev/image-to-image:
    post:
      summary: ' FLUX.1 [Dev] 图片生成图片'
      deprecated: false
      description: ''
      tags:
        - 绘图模型/Flux 系列/Fal.ai 平台兼容
      parameters:
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{API_KEY}}
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: false
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              title: FLUX.1 Kontext [Max] - 图像转图像生成
              type: object
              required:
                - image_url
                - prompt
              properties:
                image_url:
                  type: string
                  description: 原始图片的公网 URL。（必填）
                  examples:
                    - https://fal.media/files/koala/Chls9L2ZnvuipUTEwlnJC.png
                prompt:
                  type: string
                  description: 文本提示，用于描述需要生成哪种风格或内容（必填）
                  examples:
                    - >-
                      a cat dressed as a wizard with a background of a mystic
                      forest.
                strength:
                  type: number
                  minimum: 0.01
                  maximum: 1
                  default: 0.95
                  description: 初始图片风格保留程度，越高保留越多（默认0.95，推荐）
                num_inference_steps:
                  type: integer
                  minimum: 10
                  maximum: 50
                  default: 40
                  description: 生成采样步数，步数越多，图片质量可能越高但速度更慢（默认40）
                guidance_scale:
                  type: number
                  minimum: 1
                  maximum: 20
                  default: 3.5
                  description: 控制生成图片与 prompt 的契合程度，数值越高越接近prompt（默认3.5）
                seed:
                  type: integer
                  description: 随机种子 — 用于结果复现，同样参数和 seed 会得到一致结果。可为空
                  nullable: true
                sync_mode:
                  type: boolean
                  default: false
                  description: 是否启用同步模式。如果为 true，接口会等待图片生成完毕后返回。建议异步（false）
                num_images:
                  type: integer
                  minimum: 1
                  maximum: 4
                  default: 1
                  description: 要生成的图片数量（默认1张，最多4张）
                enable_safety_checker:
                  type: boolean
                  default: true
                  description: 是否启用安全检测，过滤不安全内容（默认true）
              x-apifox-orders:
                - image_url
                - prompt
                - strength
                - num_inference_steps
                - guidance_scale
                - seed
                - sync_mode
                - num_images
                - enable_safety_checker
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
                x-apifox-orders: []
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 绘图模型/Flux 系列/Fal.ai 平台兼容
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309501877-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
