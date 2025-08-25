# 业务监控和告警系统

## 📊 监控系统概述

### 监控目标

建立全面的业务指标监控和告警系统，实时监控平台运行状态、用户行为、AI服务性能等关键指标，确保系统稳定运行和用户体验。

## 🎯 监控指标体系

### 1. 系统性能指标

#### 1.1 HTTP请求指标

- **请求总数** (http_requests_total)
- **请求响应时间** (http_request_duration_seconds)
- **错误率** (http_errors_rate)
- **并发连接数** (http_concurrent_connections)

#### 1.2 数据库指标

- **查询响应时间** (db_query_duration_seconds)
- **连接池使用率** (db_connection_pool_usage)
- **慢查询数量** (db_slow_queries_total)
- **死锁数量** (db_deadlocks_total)

#### 1.3 Redis缓存指标

- **缓存命中率** (cache_hit_rate)
- **缓存大小** (cache_size_bytes)
- **缓存操作延迟** (cache_operation_duration_seconds)
- **内存使用率** (redis_memory_usage_ratio)

### 2. 业务关键指标

#### 2.1 用户活跃指标

- **日活跃用户** (daily_active_users)
- **月活跃用户** (monthly_active_users)
- **新用户注册数** (new_users_registered)
- **用户留存率** (user_retention_rate)

#### 2.2 AI服务使用指标

- **AI任务提交数** (ai_tasks_submitted_total)
- **AI任务成功率** (ai_task_success_rate)
- **AI任务平均处理时间** (ai_task_duration_avg)
- **各服务使用量分布** (ai_service_usage_distribution)

#### 2.3 积分系统指标

- **总积分消费** (credits_consumed_total)
- **平均用户积分余额** (avg_user_credits)
- **充值金额** (credits_purchased_total)
- **积分转化率** (credit_conversion_rate)

### 3. 错误和异常指标

#### 3.1 系统错误

- **应用错误数** (application_errors_total)
- **AI服务调用失败** (ai_service_failures_total)
- **支付处理失败** (payment_failures_total)
- **文件上传失败** (file_upload_failures_total)

#### 3.2 安全指标

- **登录失败次数** (login_failures_total)
- **API滥用检测** (api_abuse_detected)
- **异常访问模式** (suspicious_access_patterns)

## 🛠️ 监控系统架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        应用服务层                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   FastAPI       │  │   AI Services   │  │   Database      │ │
│  │   应用服务       │  │   AI服务监控     │  │   数据库监控     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                        指标收集层                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Prometheus    │  │    Grafana      │  │    Alertmanager │ │
│  │   指标收集       │  │    可视化       │  │    告警管理      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                        通知渠道层                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │     邮件        │  │     微信        │  │     钉钉        │ │
│  │    Email        │  │   WeChat        │  │   DingTalk      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 实施方案

### 方案1：Prometheus指标收集

#### 1.1 安装依赖

```python
# requirements.txt 添加
prometheus-client==0.20.0
```

#### 1.2 指标定义模块

```python
# backend/open_webui/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Enum, Info
from functools import wraps
import time
from typing import Dict, Any

# =================== HTTP请求指标 ===================
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'user_role']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_CONCURRENT_CONNECTIONS = Gauge(
    'http_concurrent_connections',
    'Current number of concurrent connections'
)

# =================== 数据库指标 ===================
DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['table', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

DB_CONNECTION_POOL_SIZE = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

DB_CONNECTION_POOL_USAGE = Gauge(
    'db_connection_pool_usage',
    'Database connection pool usage'
)

# =================== 缓存指标 ===================
CACHE_OPERATIONS_TOTAL = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']  # operation: get/set/delete, result: hit/miss/success/error
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

# =================== 业务指标 ===================
ACTIVE_USERS = Gauge(
    'active_users_current',
    'Current number of active users'
)

AI_TASKS_TOTAL = Counter(
    'ai_tasks_total',
    'Total AI tasks submitted',
    ['service', 'status', 'user_role']  # service: midjourney/flux/etc, status: success/failed/pending
)

AI_TASK_DURATION = Histogram(
    'ai_task_duration_seconds',
    'AI task processing duration',
    ['service', 'mode'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200]
)

CREDITS_OPERATIONS = Counter(
    'credits_operations_total',
    'Total credits operations',
    ['operation', 'user_role']  # operation: consume/refund/purchase
)

CREDITS_BALANCE = Histogram(
    'user_credits_balance',
    'User credits balance distribution',
    buckets=[0, 10, 50, 100, 500, 1000, 5000, float('inf')]
)

# =================== 错误指标 ===================
APPLICATION_ERRORS = Counter(
    'application_errors_total',
    'Total application errors',
    ['error_type', 'component']
)

SECURITY_EVENTS = Counter(
    'security_events_total',
    'Security-related events',
    ['event_type', 'severity']  # login_failure, api_abuse, etc.
)

# =================== 系统信息 ===================
SYSTEM_INFO = Info(
    'system_info',
    'System information'
)
```

### 方案2：监控装饰器和中间件

#### 2.1 HTTP请求监控中间件

```python
# backend/open_webui/utils/monitoring_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from .metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION, HTTP_CONCURRENT_CONNECTIONS

class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.active_requests = 0

    async def dispatch(self, request: Request, call_next):
        # 记录并发连接数
        self.active_requests += 1
        HTTP_CONCURRENT_CONNECTIONS.set(self.active_requests)

        # 记录请求开始时间
        start_time = time.time()

        # 获取用户角色（如果已认证）
        user_role = "anonymous"
        if hasattr(request.state, 'user'):
            user_role = getattr(request.state.user, 'role', 'user')

        try:
            # 处理请求
            response = await call_next(request)

            # 记录指标
            duration = time.time() - start_time

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=response.status_code,
                user_role=user_role
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=self._get_endpoint_name(request)
            ).observe(duration)

            return response

        except Exception as e:
            # 记录错误
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=500,
                user_role=user_role
            ).inc()

            APPLICATION_ERRORS.labels(
                error_type=type(e).__name__,
                component="http_middleware"
            ).inc()

            raise

        finally:
            # 更新并发连接数
            self.active_requests -= 1
            HTTP_CONCURRENT_CONNECTIONS.set(self.active_requests)

    def _get_endpoint_name(self, request: Request) -> str:
        """获取端点名称"""
        if hasattr(request, 'url') and hasattr(request.url, 'path'):
            path = request.url.path

            # 简化路径以减少标签基数
            if path.startswith('/api/v1/'):
                parts = path.split('/')
                if len(parts) >= 4:
                    # /api/v1/service -> service
                    return parts[3]

            return path.rstrip('/')

        return "unknown"

# 业务指标装饰器
def monitor_ai_task(service: str):
    """AI任务监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            user_role = "user"  # 可以从参数中获取

            try:
                result = await func(*args, **kwargs)

                # 记录成功任务
                AI_TASKS_TOTAL.labels(
                    service=service,
                    status="success",
                    user_role=user_role
                ).inc()

                duration = time.time() - start_time
                AI_TASK_DURATION.labels(
                    service=service,
                    mode="default"  # 可以从参数中获取
                ).observe(duration)

                return result

            except Exception as e:
                # 记录失败任务
                AI_TASKS_TOTAL.labels(
                    service=service,
                    status="failed",
                    user_role=user_role
                ).inc()

                APPLICATION_ERRORS.labels(
                    error_type=type(e).__name__,
                    component=f"ai_service_{service}"
                ).inc()

                raise

        return wrapper
    return decorator

def monitor_credits_operation(operation: str):
    """积分操作监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = "user"  # 可以从参数中获取

            try:
                result = func(*args, **kwargs)

                CREDITS_OPERATIONS.labels(
                    operation=operation,
                    user_role=user_role
                ).inc()

                # 如果是消费操作，记录余额分布
                if operation == "consume" and hasattr(result, 'credit'):
                    CREDITS_BALANCE.observe(float(result.credit))

                return result

            except Exception as e:
                APPLICATION_ERRORS.labels(
                    error_type=type(e).__name__,
                    component="credits_system"
                ).inc()
                raise

        return wrapper
    return decorator
```

### 方案3：告警规则配置

#### 3.1 Prometheus告警规则

```yaml
# alerts/business_alerts.yml
groups:
  - name: business_critical
    rules:
      # HTTP错误率告警
      - alert: HighErrorRate
        expr: (rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])) > 0.05
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: 'High error rate detected'
          description: 'Error rate is {{ $value | humanizePercentage }} over the last 5 minutes'

      # 响应时间告警
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 3m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'Slow response time detected'
          description: '95th percentile response time is {{ $value }}s'

      # AI服务失败率告警
      - alert: AIServiceHighFailureRate
        expr: (rate(ai_tasks_total{status="failed"}[10m]) / rate(ai_tasks_total[10m])) > 0.1
        for: 5m
        labels:
          severity: critical
          team: ai_services
        annotations:
          summary: 'AI service failure rate is high'
          description: '{{ $labels.service }} service failure rate is {{ $value | humanizePercentage }}'

      # 缓存命中率低告警
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 0.7
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'Cache hit rate is low'
          description: 'Cache hit rate is {{ $value | humanizePercentage }}'

      # 用户活跃度异常
      - alert: UnusualUserActivity
        expr: |
          (
            avg_over_time(active_users_current[1h]) 
            - 
            avg_over_time(active_users_current[1h] offset 1d)
          ) / avg_over_time(active_users_current[1h] offset 1d) > 0.5
        for: 10m
        labels:
          severity: info
          team: product
        annotations:
          summary: 'Unusual increase in user activity'
          description: 'Active users increased by {{ $value | humanizePercentage }} compared to yesterday'

  - name: system_resources
    rules:
      # 数据库连接池告警
      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_usage / db_connection_pool_size > 0.9
        for: 2m
        labels:
          severity: critical
          team: database
        annotations:
          summary: 'Database connection pool nearly exhausted'
          description: 'Connection pool usage is {{ $value | humanizePercentage }}'

      # Redis内存使用告警
      - alert: RedisHighMemoryUsage
        expr: redis_memory_usage_ratio > 0.85
        for: 5m
        labels:
          severity: warning
          team: cache
        annotations:
          summary: 'Redis memory usage is high'
          description: 'Redis memory usage is {{ $value | humanizePercentage }}'

  - name: security
    rules:
      # 登录失败告警
      - alert: HighLoginFailureRate
        expr: rate(security_events_total{event_type="login_failure"}[5m]) > 10
        for: 2m
        labels:
          severity: warning
          team: security
        annotations:
          summary: 'High login failure rate detected'
          description: 'Login failure rate is {{ $value }} per second'

      # API滥用告警
      - alert: APIAbuseDetected
        expr: rate(security_events_total{event_type="api_abuse"}[1m]) > 0
        for: 0m
        labels:
          severity: critical
          team: security
        annotations:
          summary: 'API abuse detected'
          description: 'API abuse detected at rate {{ $value }} per second'
```

### 方案4：Grafana仪表板

#### 4.1 业务仪表板配置

```json
{
	"dashboard": {
		"title": "WXIAI 业务监控仪表板",
		"panels": [
			{
				"title": "实时用户活跃",
				"type": "stat",
				"targets": [
					{
						"expr": "active_users_current",
						"legendFormat": "当前活跃用户"
					}
				]
			},
			{
				"title": "AI任务成功率",
				"type": "stat",
				"targets": [
					{
						"expr": "rate(ai_tasks_total{status=\"success\"}[5m]) / rate(ai_tasks_total[5m])",
						"legendFormat": "成功率"
					}
				]
			},
			{
				"title": "各AI服务使用量",
				"type": "piechart",
				"targets": [
					{
						"expr": "sum by (service) (rate(ai_tasks_total[1h]))",
						"legendFormat": "{{ service }}"
					}
				]
			},
			{
				"title": "API响应时间趋势",
				"type": "timeseries",
				"targets": [
					{
						"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
						"legendFormat": "95th percentile"
					},
					{
						"expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
						"legendFormat": "50th percentile"
					}
				]
			},
			{
				"title": "缓存命中率",
				"type": "timeseries",
				"targets": [
					{
						"expr": "cache_hit_rate",
						"legendFormat": "命中率"
					}
				]
			}
		]
	}
}
```

## 📱 实施工具

### 工具1：监控健康检查端点

```python
# backend/open_webui/routers/monitoring.py
from fastapi import APIRouter, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import json
from ..utils.metrics import *
from ..utils.auth import get_admin_user

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus指标端点"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "ai_services": await check_ai_services_health()
        }
    }

    # 如果有任何检查失败，返回503
    if not all(check["healthy"] for check in checks["checks"].values()):
        return Response(
            content=json.dumps(checks),
            status_code=503,
            media_type="application/json"
        )

    return checks

@router.get("/stats", dependencies=[Depends(get_admin_user)])
async def monitoring_stats():
    """监控统计信息"""
    from ..main import app

    stats = {
        "cache_stats": {},
        "active_connections": HTTP_CONCURRENT_CONNECTIONS._value._value,
        "total_requests": sum([
            metric._value._value for metric in HTTP_REQUESTS_TOTAL._metrics.values()
        ]),
        "ai_tasks_stats": {
            service: sum([
                metric._value._value
                for metric in AI_TASKS_TOTAL._metrics.values()
                if metric._labelvalues[0] == service
            ])
            for service in ["midjourney", "flux", "dreamwork", "jimeng", "kling"]
        }
    }

    # 获取缓存统计
    if hasattr(app.state, 'cache_manager'):
        stats["cache_stats"] = app.state.cache_manager.get_stats()

    return stats

async def check_database_health():
    """检查数据库健康状态"""
    try:
        from ..internal.db import get_db
        with get_db() as db:
            db.execute("SELECT 1")
        return {"healthy": True, "message": "Database is accessible"}
    except Exception as e:
        return {"healthy": False, "message": f"Database error: {str(e)}"}

async def check_redis_health():
    """检查Redis健康状态"""
    try:
        from ..main import app
        if hasattr(app.state, 'cache_manager') and app.state.cache_manager.redis:
            await app.state.cache_manager.redis.ping()
            return {"healthy": True, "message": "Redis is accessible"}
        return {"healthy": True, "message": "Redis not configured"}
    except Exception as e:
        return {"healthy": False, "message": f"Redis error: {str(e)}"}

async def check_ai_services_health():
    """检查AI服务健康状态"""
    # 这里可以添加对各个AI服务的健康检查
    return {"healthy": True, "message": "AI services check not implemented"}
```

### 工具2：告警通知系统

```python
# backend/open_webui/utils/alerting.py
import asyncio
import httpx
import json
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AlertManager:
    """告警管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled_channels = config.get('enabled_channels', [])

    async def send_alert(self,
                        alert_name: str,
                        severity: str,
                        message: str,
                        details: Dict[str, Any] = None):
        """发送告警"""
        alert_data = {
            "alert_name": alert_name,
            "severity": severity,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "source": "wxiai-platform"
        }

        # 并发发送到所有启用的通道
        tasks = []

        if 'email' in self.enabled_channels:
            tasks.append(self._send_email_alert(alert_data))

        if 'webhook' in self.enabled_channels:
            tasks.append(self._send_webhook_alert(alert_data))

        if 'dingtalk' in self.enabled_channels:
            tasks.append(self._send_dingtalk_alert(alert_data))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 记录发送结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Alert channel {i} failed: {result}")
                else:
                    logger.info(f"Alert sent successfully to channel {i}")

    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """发送邮件告警"""
        email_config = self.config.get('email', {})
        if not email_config.get('enabled'):
            return

        # 实现邮件发送逻辑
        logger.info(f"Sending email alert: {alert_data['alert_name']}")

    async def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """发送Webhook告警"""
        webhook_config = self.config.get('webhook', {})
        if not webhook_config.get('enabled'):
            return

        url = webhook_config.get('url')
        if not url:
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=alert_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response.raise_for_status()

        except Exception as e:
            logger.error(f"Webhook alert failed: {e}")
            raise

    async def _send_dingtalk_alert(self, alert_data: Dict[str, Any]):
        """发送钉钉告警"""
        dingtalk_config = self.config.get('dingtalk', {})
        if not dingtalk_config.get('enabled'):
            return

        webhook_url = dingtalk_config.get('webhook_url')
        if not webhook_url:
            return

        # 格式化钉钉消息
        severity_emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }

        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"WXIAI告警: {alert_data['alert_name']}",
                "text": f"""
## {severity_emoji.get(alert_data['severity'], '📢')} {alert_data['alert_name']}

**告警等级**: {alert_data['severity'].upper()}

**告警信息**: {alert_data['message']}

**发生时间**: {alert_data['timestamp']}

**系统来源**: {alert_data['source']}
"""
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=message,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response.raise_for_status()

        except Exception as e:
            logger.error(f"DingTalk alert failed: {e}")
            raise

# 全局告警管理器实例
alert_manager: AlertManager = None

def init_alert_manager(config: Dict[str, Any]):
    """初始化告警管理器"""
    global alert_manager
    alert_manager = AlertManager(config)
    return alert_manager

async def send_business_alert(alert_name: str, severity: str, message: str, **kwargs):
    """发送业务告警的便捷函数"""
    if alert_manager:
        await alert_manager.send_alert(alert_name, severity, message, kwargs)
    else:
        logger.warning(f"Alert manager not initialized, alert dropped: {alert_name}")
```

## 📈 预期效果

### 监控覆盖率

- **系统性能**: 100%覆盖HTTP、数据库、缓存指标
- **业务指标**: 100%覆盖用户、AI服务、积分系统
- **错误监控**: 全面的异常和安全事件监控
- **告警响应**: 2分钟内检测到关键问题
- **可视化**: 实时仪表板和历史趋势分析

### 运维效率提升

- **故障发现时间**: 从人工发现减少到自动检测2分钟内
- **问题定位效率**: 通过详细指标快速定位问题根因
- **预防性维护**: 通过趋势分析预防潜在问题
- **容量规划**: 基于历史数据进行资源规划

---

**监控系统建设完成后，将大大提升系统可观测性和运维效率！**

_最后更新: 2025-08-24_
