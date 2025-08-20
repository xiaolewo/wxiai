# FLUX.1 [Dev] 文本生成图片

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-1/dev:
    post:
      summary: FLUX.1 [Dev] 文本生成图片
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
              title: FLUX.1 文本生成图片请求参数
              type: object
              properties:
                prompt:
                  type: string
                  description: 图片描述词，即你期望模型生成的场景、内容描述。必填项。
                num_images:
                  type: integer
                  description: 生成图片数量（最大4）。默认 1。
                image_size:
                  oneOf:
                    - type: object
                      properties: {}
                    - type: string
                      enum:
                        - square_hd
                        - square
                        - portrait_4_3
                        - portrait_16_9
                        - landscape_4_3
                        - landscape_16_9
                  description: 预设图片尺寸（或自定义分辨率，见下），默认 landscape_4_3。
                sync_mode:
                  type: boolean
                  description: 同步生成（true则等图片上传后直接返回，false则异步，默认false）。
                guidance_scale:
                  type: number
                  description: 引导系数(数值越大图片内容更贴近prompt)，默认3.5，范围1~20。
                num_inference_steps:
                  type: integer
                  description: 推理迭代步数，影响图片精细度，默认28，范围1~50。
                seed:
                  type: integer
                  description: 随机数种子，设置后同样描述和参数多次请求生成一致图片。
                enable_safety_checker:
                  type: boolean
                  description: 启用内容安全检查（默认true）。
              required:
                - prompt
              definitions:
                ImageSize:
                  type: object
                  properties:
                    width:
                      type: integer
                      description: 自定义宽度，默认512，最大14142。
                    height:
                      type: integer
                      description: 自定义高度，默认512，最大14142。
                  x-apifox-orders:
                    - width
                    - height
              x-apifox-orders:
                - prompt
                - num_images
                - image_size
                - sync_mode
                - guidance_scale
                - num_inference_steps
                - seed
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
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309502688-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
