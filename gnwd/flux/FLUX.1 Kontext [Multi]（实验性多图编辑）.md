# FLUX.1 Kontext [Multi]（实验性多图编辑）

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-pro/kontext/multi:
    post:
      summary: FLUX.1 Kontext [Multi]（实验性多图编辑）
      deprecated: false
      description: 实验性多图像编辑API，支持对多张图片，结合文本提示进行图像内容上下文理解和修改。广泛用于AI图片编辑、修图等场景。
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
                - image_urls
              properties:
                prompt:
                  type: string
                  description: 描述你想对图片实现的编辑目标。必填。
                image_urls:
                  type: array
                  items:
                    type: string
                  description: 要编辑的图片URL列表。必填。
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
                  description: 可选。输出图片宽高比。如'16:9'
                guidance_scale:
                  type: number
                  description: 引导强度，数值越大越偏向prompt描述，默认3.5
                sync_mode:
                  type: boolean
                  description: 是否同步返回结果，true同步返回图片，false异步(推荐)
                num_images:
                  type: integer
                  description: 返回图片数量，1-4
                output_format:
                  type: string
                  enum:
                    - jpeg
                    - png
                  description: 图片返回格式，可选jpeg/png
                safety_tolerance:
                  type: string
                  enum:
                    - '1'
                    - '2'
                    - '3'
                    - '4'
                    - '5'
                    - '6'
                  description: 风险内容检测敏感级别。1最严，6最宽松
                seed:
                  type: integer
                  description: 生成图片的随机种子(可选，相同seed可复刻同样生成结果)
              x-apifox-orders:
                - prompt
                - image_urls
                - aspect_ratio
                - guidance_scale
                - sync_mode
                - num_images
                - output_format
                - safety_tolerance
                - seed
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
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309320132-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
