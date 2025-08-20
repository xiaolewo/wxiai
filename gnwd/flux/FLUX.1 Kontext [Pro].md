# FLUX.1 Kontext [Pro]

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-pro/kontext:
    post:
      summary: FLUX.1 Kontext [Pro]
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
              type: object
              required:
                - prompt
              properties:
                prompt:
                  type: string
                  description: 用于生成图片的文本描述（必须）
                seed:
                  type: integer
                  description: 随机种子，设置相同的 seed 和 prompt 会输出相同的图片（可选）
                guidance_scale:
                  type: number
                  default: 3.5
                  description: CFG 指导强度，决定生成图片是否更贴合 prompt，默认值3.5（可选）
                sync_mode:
                  type: boolean
                  description: 同步模式，若为 true，则直接返回图片内容（可选）
                num_images:
                  type: integer
                  default: 1
                  description: 生成图片数量，默认为1（可选）
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
                  description: 内容安全容忍度，1最严格，6最宽松，默认2（API专有，可选）
                output_format:
                  type: string
                  enum:
                    - jpeg
                    - png
                  default: jpeg
                  description: 图片输出格式，支持 jpeg 或 png，默认 jpeg（可选）
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
                  default: '1:1'
                  description: 图片输出宽高比，默认 1:1（可选）
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
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309256309-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
