# 文生视频

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/google/v1/models/veo/videos:
    post:
      summary: 文生视频
      deprecated: false
      description: ''
      tags:
        - 视频模型/Google-Veo
      parameters:
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
            default: Bearer {{YOUR_API_KEY}}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                prompt:
                  type: string
                model:
                  type: string
                  enum:
                    - veo3
                    - veo3-fast
                    - veo3-pro
                    - veo3-pro-frames
                    - veo2
                    - veo2-fast
                    - veo2-fast-frames
                    - veo2-fast-components
                    - veo2-pro
                    - veo3-fast-frames
                  x-apifox-enum:
                    - value: veo3
                      name: ''
                      description: ''
                    - value: veo3-fast
                      name: ''
                      description: ''
                    - value: veo3-pro
                      name: ''
                      description: ''
                    - value: veo3-pro-frames
                      name: ''
                      description: 支持图生视频
                  x-apifox:
                    enumDescriptions:
                      veo3: ''
                      veo3-fast: ''
                      veo3-pro: ''
                      veo3-pro-frames: ''
                      veo2: ''
                      veo2-fast: ''
                      veo2-fast-frames: ''
                      veo2-fast-components: ''
                      veo2-pro: ''
                      veo3-fast-frames: ''
                enhance_prompt:
                  type: boolean
                  description: |
                    是否优化提示词，一般是false；由于 veo 只支持英文提示词，所以如果需要中文自动转成英文提示词，可以开启此开关
              required:
                - prompt
                - model
                - enhance_prompt
              x-apifox-orders:
                - prompt
                - model
                - enhance_prompt
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
                x-apifox-orders: []
              example:
                code: success
                message: ''
                data: f0aa213c-c09e-4e19-a0e5-c698fe48acf1
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频模型/Google-Veo
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-310714193-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
