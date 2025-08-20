# FLUX.1 Kontext [Max Multi]（实验性多图编辑）

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-pro/kontext/max/multi:
    post:
      summary: FLUX.1 Kontext [Max Multi]（实验性多图编辑）
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
              title: FluxKontextMultiInput 请求体
              type: object
              required:
                - prompt
                - image_urls
              properties:
                prompt:
                  type: string
                  description: 文本描述，模型将根据该描述及图片内容进行编辑
                  examples:
                    - Put the little duckling on top of the woman's t-shirt.
                seed:
                  type: integer
                  description: 随机种子，传入相同参数时图片结果保持一致
                guidance_scale:
                  type: number
                  default: 3.5
                  description: 提示词遵循程度 (Classifier Free Guidance Scale)，数值越大越贴合prompt
                sync_mode:
                  type: boolean
                  default: false
                  description: 同步模式。true时会等待图片生成并上传再返回，适合需要直接获得图片内容时
                num_images:
                  type: integer
                  default: 1
                  minimum: 1
                  maximum: 4
                  description: 生成图片数量
                safety_tolerance:
                  type: string
                  enum:
                    - '1'
                    - '2'
                    - '3'
                    - '4'
                    - '5'
                    - '6'
                  default: '2'
                  description: 安全容忍度，1最严格(内容少)，6最宽松(内容多)
                output_format:
                  type: string
                  enum:
                    - jpeg
                    - png
                  default: jpeg
                  description: 输出图片格式
                aspect_ratio:
                  type: string
                  enum:
                    - '21:9'
                    - '16:9'
                    - '4:3'
                    - '3:2'
                    - '1:1'
                    - '2:3'
                    - '3:4'
                    - '9:16'
                    - '9:21'
                  description: 输出图片比例
                image_urls:
                  type: array
                  items:
                    type: string
                    format: uri
                    description: 图片的公网可访问URL，如 https://...
                  minItems: 1
                  description: 批量编辑的图片列表，支持多张图片
              x-apifox-orders:
                - prompt
                - seed
                - guidance_scale
                - sync_mode
                - num_images
                - safety_tolerance
                - output_format
                - aspect_ratio
                - image_urls
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  request_id:
                    type: string
                  response_url:
                    type: string
                  status_url:
                    type: string
                  cancel_url:
                    type: string
                  queue_position:
                    type: integer
                required:
                  - status
                  - request_id
                  - response_url
                  - status_url
                  - cancel_url
                  - queue_position
                x-apifox-orders:
                  - status
                  - request_id
                  - response_url
                  - status_url
                  - cancel_url
                  - queue_position
                title: FluxKontextOutput 响应体
              example:
                status: IN_QUEUE
                request_id: 551a32da-52b2-4be8-bf2f-bfb7cce2b324
                response_url: >-
                  https://queue.fal.run/fal-ai/flux-1/requests/551a32da-52b2-4be8-bf2f-bfb7cce2b324
                status_url: >-
                  https://queue.fal.run/fal-ai/flux-1/requests/551a32da-52b2-4be8-bf2f-bfb7cce2b324/status
                cancel_url: >-
                  https://queue.fal.run/fal-ai/flux-1/requests/551a32da-52b2-4be8-bf2f-bfb7cce2b324/cancel
                queue_position: 0
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 绘图模型/Flux 系列/Fal.ai 平台兼容
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309299431-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
