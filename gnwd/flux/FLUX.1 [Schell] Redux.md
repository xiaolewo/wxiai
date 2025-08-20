# FLUX.1 [Schell] Redux

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-1/schnell/redux:
    post:
      summary: FLUX.1 [Schell] Redux
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
                image_url:
                  type: string
                  description: 输入图片的URL(必填)
                image_size:
                  oneOf:
                    - type: string
                      enum:
                        - square_hd
                        - square
                        - portrait_4_3
                        - portrait_16_9
                        - landscape_4_3
                        - landscape_16_9
                    - type: object
                      properties:
                        width:
                          type: integer
                          default: 512
                          maximum: 14142
                        height:
                          type: integer
                          default: 512
                          maximum: 14142
                      required:
                        - width
                        - height
                      x-apifox-orders:
                        - width
                        - height
                  description: 生成图片尺寸，可选字符串或指定宽/高
                num_inference_steps:
                  type: integer
                  minimum: 1
                  maximum: 12
                  default: 4
                  description: 推理步数
                seed:
                  type: integer
                  description: 随机种子，保证可复现
                  nullable: true
                sync_mode:
                  type: boolean
                  default: false
                  description: 是否同步返回图片
                num_images:
                  type: integer
                  minimum: 1
                  maximum: 4
                  default: 1
                  description: 生成图片数量
                enable_safety_checker:
                  type: boolean
                  default: true
                  description: 是否启用敏感内容检测
              required:
                - image_url
              x-apifox-orders:
                - image_url
                - image_size
                - num_inference_steps
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
                  logs:
                    type: object
                    properties: {}
                    x-apifox-orders: []
                  metrics:
                    type: object
                    properties: {}
                    x-apifox-orders: []
                  queue_position:
                    type: integer
                required:
                  - status
                  - request_id
                  - response_url
                  - status_url
                  - cancel_url
                  - logs
                  - metrics
                  - queue_position
                x-apifox-orders:
                  - status
                  - request_id
                  - response_url
                  - status_url
                  - cancel_url
                  - logs
                  - metrics
                  - queue_position
              example:
                status: IN_QUEUE
                request_id: xxx123
                response_url: https://queue.fal.run/xxx/response
                status_url: https://queue.fal.run/xxx/status
                cancel_url: https://queue.fal.run/xxx/cancel
                logs: {}
                metrics: {}
                queue_position: 2
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 绘图模型/Flux 系列/Fal.ai 平台兼容
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309503830-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
