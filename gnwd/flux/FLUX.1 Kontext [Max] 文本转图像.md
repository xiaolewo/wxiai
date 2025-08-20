# FLUX.1 Kontext [Max] 文本转图像

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-pro/kontext/text-to-image:
    post:
      summary: FLUX.1 Kontext [Max] 文本转图像
      deprecated: false
      description: FLUX.1 Kontext [max] 是一款高性能文本转图像AI模型，支持高还原文本描述生成高质量图片，且在各种细节和风格领域表现突出。
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
              title: FLUX.1 Kontext Max 文本转图像请求参数
              type: object
              properties:
                prompt:
                  type: string
                  description: 生成图片的文本提示
                  examples:
                    - 一只猫咪在宇宙飞船里俯瞰地球
                seed:
                  type: integer
                  description: 随机种子，相同seed将产生相同图片。
                guidance_scale:
                  type: number
                  description: CFG 指令引导参数，决定图片与 prompt 的贴合度，默认3.5，取值范围[1,20]。
                sync_mode:
                  type: boolean
                  description: 是否同步等待图片生成功能，true时接口直接返回图像，latency更高。
                  default: false
                num_images:
                  type: integer
                  description: 一次生成图片数量，默认1，最多4。
                  minimum: 1
                  maximum: 4
                safety_tolerance:
                  type: string
                  description: 安全容忍度，1最严格，6最宽松。默认2。
                  enum:
                    - '1'
                    - '2'
                    - '3'
                    - '4'
                    - '5'
                    - '6'
                  default: '2'
                output_format:
                  type: string
                  description: 生成图片的格式，支持jpeg/png，默认jpeg。
                  enum:
                    - jpeg
                    - png
                  default: jpeg
                aspect_ratio:
                  type: string
                  description: 长宽比例，默认1:1
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
                  default: '1:1'
              required:
                - prompt
              x-apifox-orders:
                - prompt
                - seed
                - guidance_scale
                - sync_mode
                - num_images
                - safety_tolerance
                - output_format
                - aspect_ratio
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
                title: FLUX.1 Kontext Max 文本转图像响应参数
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
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309326161-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
