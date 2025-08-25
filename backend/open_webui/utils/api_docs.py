"""
API文档增强工具
用于配置和生成完善的OpenAPI文档
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
from typing import Dict, List, Any


def get_custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """生成自定义的OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="WXIAI - AI服务聚合平台",
        version="2.0.0",
        description="""
        # 🚀 WXIAI AI服务聚合平台

        这是一个综合性的AI服务平台，集成了多种主流AI生成服务，为用户提供一站式的AI内容生成解决方案。

        ## 🎯 核心功能
        
        - **🤖 AI服务集成**: 支持Midjourney、Flux、即梦、可灵等多种AI服务
        - **💰 积分管理**: 完整的积分计费和支付体系  
        - **👥 用户管理**: 多角色权限管理系统
        - **💬 聊天系统**: 智能对话和文件处理
        - **📁 文件管理**: 云存储集成和文件管理
        - **⚙️ 配置管理**: 灵活的系统配置管理

        ## 🔐 认证方式

        ### JWT Token认证 (推荐)
        大部分API需要JWT Token认证，通过登录接口获取Token后，在请求头中添加：
        ```http
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        ```

        ### API Key认证
        部分API支持API Key认证，在用户设置中生成API Key后使用：
        ```http
        Authorization: Bearer sk-abcd1234efgh5678...
        ```

        ## 📊 响应格式

        ### 成功响应
        ```json
        {
          "data": "实际数据内容",
          "success": true,
          "message": "操作成功"
        }
        ```

        ### 错误响应
        ```json
        {
          "error": "错误代码",
          "detail": "详细错误信息",
          "success": false
        }
        ```

        ## 🚦 状态码说明

        - `200` - 请求成功
        - `201` - 创建成功
        - `400` - 请求参数错误
        - `401` - 未授权访问 (Token无效或过期)
        - `403` - 权限不足 (无相关操作权限)
        - `404` - 资源不存在
        - `429` - 请求过于频繁 (触发限流)
        - `500` - 服务器内部错误

        ## 🎯 快速开始

        ### 1. 用户注册和登录
        ```python
        import requests
        
        # 用户登录
        response = requests.post("/api/v1/auths/signin", json={
            "email": "user@example.com",
            "password": "your_password"
        })
        token = response.json()["token"]
        ```

        ### 2. 使用AI服务
        ```python
        headers = {"Authorization": f"Bearer {token}"}
        
        # Midjourney图像生成
        response = requests.post("/api/v1/midjourney/submit/imagine", 
            headers=headers,
            json={
                "prompt": "a beautiful sunset over the ocean",
                "mode": "fast"
            }
        )
        ```

        ### 3. 查看积分和使用记录
        ```python
        response = requests.get("/api/v1/credit", headers=headers)
        credit_info = response.json()
        ```

        ## 📱 SDKs 和工具

        - **Python SDK**: `pip install wxiai-python`
        - **JavaScript SDK**: `npm install wxiai-js`
        - **Postman Collection**: [下载链接](#)

        ## 🔗 相关链接

        - **官方网站**: https://wxiai.com
        - **开发者文档**: https://docs.wxiai.com
        - **技术支持**: https://wxiai.com/support
        - **GitHub**: https://github.com/wxiai/wxiai-main

        ## 📞 联系我们

        - **技术支持邮箱**: support@wxiai.com
        - **商务合作**: business@wxiai.com
        - **官方QQ群**: 123456789
        """,
        routes=app.routes,
        contact={
            "name": "WXIAI Support Team",
            "url": "https://wxiai.com/support",
            "email": "support@wxiai.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {"url": "https://api.wxiai.com", "description": "🚀 生产环境 - 稳定版本"},
            {
                "url": "https://staging.wxiai.com",
                "description": "🧪 测试环境 - 预发布版本",
            },
            {"url": "http://localhost:8080", "description": "💻 开发环境 - 本地开发"},
        ],
    )

    # 自定义标签分类和描述
    openapi_schema["tags"] = [
        {
            "name": "认证系统",
            "description": "**用户注册、登录、权限管理**\n\n包含用户注册、登录、登出、密码管理、权限验证等核心认证功能。支持邮箱、手机号、OAuth等多种认证方式。",
            "externalDocs": {
                "description": "认证系统详细文档",
                "url": "https://docs.wxiai.com/auth",
            },
        },
        {
            "name": "用户管理",
            "description": "**用户信息和个人设置管理**\n\n用户个人信息管理、账户设置、偏好配置等功能。支持头像上传、个人资料编辑等。",
            "externalDocs": {
                "description": "用户管理文档",
                "url": "https://docs.wxiai.com/users",
            },
        },
        {
            "name": "积分系统",
            "description": "**积分充值、消费、查询管理**\n\n完整的积分生态系统，包含积分查询、充值、消费记录、兑换码使用、支付管理等功能。支持多种支付方式。",
            "externalDocs": {
                "description": "积分系统使用指南",
                "url": "https://docs.wxiai.com/credits",
            },
        },
        {
            "name": "聊天对话",
            "description": "**智能对话和聊天管理**\n\n支持多模型对话、文件上传、聊天历史管理、标签分类等功能。兼容OpenAI API格式。",
            "externalDocs": {
                "description": "聊天API使用指南",
                "url": "https://docs.wxiai.com/chat",
            },
        },
        {
            "name": "AI图像生成",
            "description": "**Midjourney、Flux、DreamWork图像生成**\n\n集成多种主流图像生成AI服务，支持文生图、图生图、图像编辑等功能。提供实时状态监控和结果管理。",
            "externalDocs": {
                "description": "图像生成API指南",
                "url": "https://docs.wxiai.com/image-generation",
            },
        },
        {
            "name": "AI视频生成",
            "description": "**即梦、可灵视频生成服务**\n\n专业的视频生成功能，支持文生视频、图生视频，多种视频比例和时长选择。提供高质量视频输出。",
            "externalDocs": {
                "description": "视频生成API指南",
                "url": "https://docs.wxiai.com/video-generation",
            },
        },
        {
            "name": "文件管理",
            "description": "**文件上传、存储、管理**\n\n支持多格式文件上传、云存储集成、文件夹管理、文件分享等功能。自动处理AI生成内容的存储。",
            "externalDocs": {
                "description": "文件管理API文档",
                "url": "https://docs.wxiai.com/files",
            },
        },
        {
            "name": "系统配置",
            "description": "**系统设置和服务配置管理**\n\n管理员功能，包含系统配置、AI服务配置、用户权限管理、系统监控等高级功能。",
            "externalDocs": {
                "description": "系统配置管理文档",
                "url": "https://docs.wxiai.com/admin",
            },
        },
    ]

    # 添加通用错误响应模式
    openapi_schema["components"]["responses"] = {
        "ValidationError": {
            "description": "请求参数验证错误",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "loc": {"type": "array"},
                                        "msg": {"type": "string"},
                                        "type": {"type": "string"},
                                    },
                                },
                            }
                        },
                    }
                }
            },
        },
        "AuthError": {
            "description": "认证错误",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string", "example": "Token已过期"},
                            "error": {"type": "string", "example": "INVALID_TOKEN"},
                        },
                    }
                }
            },
        },
        "InsufficientCredits": {
            "description": "积分不足",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "余额不足，请前往设置-积分充值",
                            },
                            "current_credit": {"type": "string", "example": "5.0000"},
                            "required_credit": {"type": "number", "example": 10},
                        },
                    }
                }
            },
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_enhanced_swagger_ui_html():
    """获取增强的Swagger UI HTML"""
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="WXIAI API Documentation",
        oauth2_redirect_url="/api/docs/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": 2,
            "defaultModelExpandDepth": 2,
            "displayRequestDuration": True,
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "deepLinking": True,
            "layout": "StandaloneLayout",
            "docExpansion": "list",
            "defaultModelRendering": "example",
            "showRequestHeaders": True,
            "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
            "tryItOutEnabled": True,
        },
    )


def get_enhanced_redoc_html():
    """获取增强的ReDoc HTML"""
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="WXIAI API Documentation - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.0/bundles/redoc.standalone.js",
        redoc_options={
            "theme": {
                "colors": {"primary": {"main": "#1976d2"}},
                "typography": {
                    "fontSize": "14px",
                    "lineHeight": "1.5em",
                    "code": {"fontSize": "13px"},
                    "headings": {"fontFamily": "Montserrat, sans-serif"},
                },
            },
            "hideDownloadButton": False,
            "hideLoading": False,
            "hideSchemaPattern": True,
            "expandResponses": "200,201",
            "requiredPropsFirst": True,
            "sortPropsAlphabetically": True,
            "showObjectSchemaExamples": True,
            "payloadSampleIdx": 0,
        },
    )


def get_api_overview_html():
    """获取API概览页面HTML"""
    return HTMLResponse(
        f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WXIAI API Documentation Center</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 40px 20px;
            }}
            
            .header {{ 
                text-align: center; 
                margin-bottom: 60px; 
                color: white;
            }}
            
            .header h1 {{ 
                font-size: 3rem; 
                margin-bottom: 20px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            
            .header p {{ 
                font-size: 1.2rem; 
                opacity: 0.9;
                margin-bottom: 10px;
            }}
            
            .version {{ 
                display: inline-block;
                background: rgba(255,255,255,0.2);
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9rem;
            }}
            
            .docs-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
                gap: 30px; 
                margin-bottom: 50px;
            }}
            
            .doc-card {{ 
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .doc-card:hover {{ 
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }}
            
            .doc-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }}
            
            .doc-card h3 {{ 
                font-size: 1.5rem;
                margin-bottom: 15px;
                color: #333;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .doc-card p {{ 
                color: #666; 
                margin-bottom: 20px;
                line-height: 1.6;
            }}
            
            .doc-card a {{ 
                display: inline-flex;
                align-items: center;
                gap: 8px;
                text-decoration: none; 
                color: #667eea;
                font-weight: 600;
                padding: 12px 24px;
                border: 2px solid #667eea;
                border-radius: 8px;
                transition: all 0.3s ease;
            }}
            
            .doc-card a:hover {{ 
                background: #667eea;
                color: white;
                transform: translateX(5px);
            }}
            
            .stats-section {{
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 50px;
                color: white;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 30px;
                text-align: center;
            }}
            
            .stat-item h4 {{
                font-size: 2rem;
                margin-bottom: 10px;
                color: #FFD700;
            }}
            
            .stat-item p {{
                opacity: 0.9;
            }}
            
            .footer {{
                text-align: center;
                color: white;
                opacity: 0.8;
            }}
            
            .footer a {{
                color: white;
                text-decoration: none;
                margin: 0 15px;
            }}
            
            .footer a:hover {{
                text-decoration: underline;
            }}
            
            @media (max-width: 768px) {{
                .container {{ padding: 20px 15px; }}
                .header h1 {{ font-size: 2rem; }}
                .docs-grid {{ grid-template-columns: 1fr; }}
                .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 WXIAI API Documentation</h1>
                <p>AI服务聚合平台 API 文档中心</p>
                <span class="version">Version 2.0.0</span>
            </div>
            
            <div class="stats-section">
                <div class="stats-grid">
                    <div class="stat-item">
                        <h4>5+</h4>
                        <p>AI服务集成</p>
                    </div>
                    <div class="stat-item">
                        <h4>50+</h4>
                        <p>API接口</p>
                    </div>
                    <div class="stat-item">
                        <h4>99.9%</h4>
                        <p>服务可用性</p>
                    </div>
                    <div class="stat-item">
                        <h4>24/7</h4>
                        <p>技术支持</p>
                    </div>
                </div>
            </div>
            
            <div class="docs-grid">
                <div class="doc-card">
                    <h3>📚 Swagger UI</h3>
                    <p>交互式API文档，支持在线测试和调试。包含完整的请求参数说明和响应示例。</p>
                    <a href="/api/docs">访问 Swagger UI →</a>
                </div>
                
                <div class="doc-card">
                    <h3>📖 ReDoc</h3>
                    <p>美观的API文档展示，提供清晰的结构化视图和详细的说明信息。</p>
                    <a href="/api/redoc">访问 ReDoc →</a>
                </div>
                
                <div class="doc-card">
                    <h3>📋 OpenAPI Schema</h3>
                    <p>标准的OpenAPI 3.0规范文件，可用于生成SDK和客户端代码。</p>
                    <a href="/api/openapi.json">下载 Schema →</a>
                </div>
                
                <div class="doc-card">
                    <h3>🔗 API Examples</h3>
                    <p>常用API调用示例和最佳实践，帮助快速上手和集成。</p>
                    <a href="/api/examples">查看示例 →</a>
                </div>
                
                <div class="doc-card">
                    <h3>🎯 快速开始</h3>
                    <p>完整的入门指南，从注册到第一次API调用的详细步骤。</p>
                    <a href="/api/quickstart">开始使用 →</a>
                </div>
                
                <div class="doc-card">
                    <h3>📞 技术支持</h3>
                    <p>遇到问题？联系我们的技术支持团队获得帮助和指导。</p>
                    <a href="mailto:support@wxiai.com">联系支持 →</a>
                </div>
            </div>
            
            <div class="footer">
                <p>
                    <a href="https://wxiai.com">官网</a> |
                    <a href="https://docs.wxiai.com">完整文档</a> |
                    <a href="https://wxiai.com/support">技术支持</a> |
                    <a href="https://github.com/wxiai">GitHub</a>
                </p>
                <p style="margin-top: 10px; font-size: 0.9rem;">
                    © 2025 WXIAI. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    )


# API示例数据
API_EXAMPLES = {
    "authentication": {
        "title": "用户认证",
        "examples": {
            "login": {
                "summary": "用户登录",
                "description": "使用邮箱和密码登录获取JWT Token",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/auths/signin",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"email": "user@example.com", "password": "your_password"},
                },
                "response": {
                    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user": {
                        "id": "user123",
                        "name": "张三",
                        "email": "user@example.com",
                        "role": "user",
                    },
                    "credit": "100.0000",
                },
            }
        },
    },
    "ai_services": {
        "title": "AI服务使用",
        "examples": {
            "midjourney_imagine": {
                "summary": "Midjourney图像生成",
                "description": "提交Midjourney图像生成任务",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/midjourney/submit/imagine",
                    "headers": {
                        "Authorization": "Bearer <your_token>",
                        "Content-Type": "application/json",
                    },
                    "body": {
                        "prompt": "a beautiful sunset over the ocean",
                        "mode": "fast",
                        "aspect_ratio": "16:9",
                    },
                },
                "response": {
                    "code": 1,
                    "description": "提交成功",
                    "result": "12345678-1234-1234-1234-123456789012",
                    "properties": {},
                },
            }
        },
    },
}


def setup_enhanced_api_docs(app: FastAPI):
    """设置增强的API文档路由"""

    # 设置自定义OpenAPI schema
    app.openapi = lambda: get_custom_openapi_schema(app)

    # API概览页面
    @app.get("/api", include_in_schema=False)
    async def api_overview():
        return get_api_overview_html()

    # 自定义Swagger UI
    @app.get("/api/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_enhanced_swagger_ui_html()

    # 自定义ReDoc
    @app.get("/api/redoc", include_in_schema=False)
    async def redoc_html():
        return get_enhanced_redoc_html()

    # API示例页面
    @app.get("/api/examples", include_in_schema=False)
    async def api_examples():
        return {"examples": API_EXAMPLES}

    return app
