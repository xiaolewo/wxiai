# FLUX.1 Kontext [Max]

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-pro/kontext/max:
    post:
      summary: FLUX.1 Kontext [Max]
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
              properties:
                prompt:
                  type: string
                  description: 提示词，对图片进行的编辑描述。例如：'把甜甜圈放在面粉旁边'
                  examples:
                    - Put a donut next to the flour.
                seed:
                  type: integer
                  description: 随机种子，保证同样输入下生成一致的图片。可选
                guidance_scale:
                  type: number
                  description: CFG 值，控制模型对prompt的遵循度，默认 3.5，可选，范围1-20。
                  default: 3.5
                sync_mode:
                  type: boolean
                  description: 同步模式，true时等待图片生成完成并直接返回图片，false时通过CDN获取图片。默认 false
                  default: false
                num_images:
                  type: integer
                  description: 生成图片数量，取值1-4，默认1
                  default: 1
                  minimum: 1
                  maximum: 4
                safety_tolerance:
                  type: string
                  description: 安全容忍等级，1最严格，6最宽松，默认2
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
                  description: 图片格式，jpeg 或 png，默认 jpeg
                  enum:
                    - jpeg
                    - png
                  default: jpeg
                aspect_ratio:
                  type: string
                  description: 图片宽高比，可选如：21:9, 16:9, 4:3, 3:2, 1:1, 2:3, 3:4, 9:16, 9:21
                image_url:
                  type: string
                  description: 要编辑的图片URL，必填，建议使用公开可访问的图片链接
                  examples:
                    - >-
                      https://v3.fal.media/files/rabbit/rmgBxhwGYb2d3pl3x9sKf_output.png
              required:
                - prompt
                - image_url
              x-apifox-orders:
                - prompt
                - seed
                - guidance_scale
                - sync_mode
                - num_images
                - safety_tolerance
                - output_format
                - aspect_ratio
                - image_url
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
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309292279-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
