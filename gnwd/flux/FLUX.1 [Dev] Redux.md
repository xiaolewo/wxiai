# FLUX.1 [Dev] Redux

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/fal-ai/flux-1/dev/redux:
    post:
      summary: FLUX.1 [Dev] Redux
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
                  description: 必填。要生成新图片的原图URL
                  type: string
                image_size:
                  type: string
                num_inference_steps:
                  description: 可选。推理步数，默认28，范围1-50
                  type: integer
                seed:
                  description: 可选。随机种子，重复使用可复现图片，可为null
                  type: integer
                guidance_scale:
                  description: 可选。CFG引导尺度，影响图片生成与Prompt的贴合程度，范围1-20
                  type: number
                sync_mode:
                  description: 可选。是否同步等待图片生成（true同步返回结果，false为异步，推荐异步）
                  type: boolean
                num_images:
                  description: 可选。生成图片数量，默认1，1-4
                  type: integer
                enable_safety_checker:
                  description: 可选。是否启用安全检测，默认true
                  type: boolean
              required:
                - image_url
                - image_size
                - num_inference_steps
                - seed
                - guidance_scale
                - sync_mode
                - num_images
                - enable_safety_checker
              x-apifox-orders:
                - image_url
                - image_size
                - num_inference_steps
                - seed
                - guidance_scale
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
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-309504286-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
