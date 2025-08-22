# 查询、获取结果

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /BASE_URL/google/v1/tasks/{task_id}:
    get:
      summary: 查询、获取结果
      deprecated: false
      description: >-
        任务状态:
        NOT_START（未启动）、SUBMITTED（已提交处理）、IN_PROGRESS（执行中）、FAILURE（失败）、SUCCESS（成功）
      tags:
        - 视频模型/Google-Veo
      parameters:
        - name: task_id
          in: path
          description: ''
          required: true
          schema:
            type: string
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
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
              example:
                code: success
                message: ''
                data:
                  task_id: f0aa213c-c09e-4e19-a0e5-c698fe48acf1
                  notify_hook: ''
                  action: google-videos
                  status: SUCCESS
                  fail_reason: ''
                  submit_time: 1750221308
                  start_time: 0
                  finish_time: 1750221572
                  progress: 100%
                  data:
                    id: f0aa213c-c09e-4e19-a0e5-c698fe48acf1
                    status: completed
                    video_url: >-
                      https://filesystem.site/cdn/20250618/a5O3efr3GyiSTIMxAtXYmCWKcNPjBL.mp4
                    status_update_time: 1750221453056
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频模型/Google-Veo
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-310715882-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []
```
