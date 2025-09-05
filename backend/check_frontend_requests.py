#!/usr/bin/env python3
"""
检查前端请求的工具
通过日志分析或实时监控来查看前端是否正确发送请求
"""

import sqlite3
import json
import os


def check_recent_requests():
    """检查最近的请求日志"""
    print("📋 检查最近的API请求...")

    # 检查是否有日志文件
    log_files = [
        "backend.log",
        "webui.log",
        "../webui.log",
        "logs/webui.log",
        "logs/backend.log",
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📄 找到日志文件: {log_file}")
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    # 查找ComfyUI相关的请求
                    comfyui_lines = [
                        line for line in lines[-200:] if "comfyui" in line.lower()
                    ]
                    if comfyui_lines:
                        print(f"🔍 最近的ComfyUI相关日志 ({len(comfyui_lines)} 条):")
                        for line in comfyui_lines[-10:]:
                            print(f"   {line.strip()}")
                    else:
                        print("   ❌ 没有找到ComfyUI相关的日志")
            except Exception as e:
                print(f"   ❌ 读取日志文件失败: {e}")
        else:
            print(f"   ❌ 日志文件不存在: {log_file}")


def create_request_monitor():
    """创建请求监控脚本"""
    monitor_script = """
// ComfyUI配置保存请求监控脚本
// 在浏览器控制台中运行此脚本来监控前端请求

(function() {
    console.log('🚀 开始监控ComfyUI配置保存请求...');
    
    // 保存原始的fetch函数
    const originalFetch = window.fetch;
    
    // 重写fetch函数来监控请求
    window.fetch = function(...args) {
        const url = args[0];
        const options = args[1] || {};
        
        // 检查是否是ComfyUI配置请求
        if (typeof url === 'string' && url.includes('comfyui/admin/config')) {
            console.log('🔍 检测到ComfyUI配置请求:');
            console.log('   URL:', url);
            console.log('   Method:', options.method || 'GET');
            console.log('   Headers:', options.headers);
            
            if (options.body) {
                try {
                    const bodyData = JSON.parse(options.body);
                    console.log('   请求数据:', bodyData);
                    console.log('   Access Key:', bodyData.access_key ? '已设置' : '❌ 空');
                    console.log('   Secret Key:', bodyData.secret_key ? '已设置' : '❌ 空');
                } catch (e) {
                    console.log('   Body:', options.body);
                }
            }
        }
        
        // 调用原始fetch并监控响应
        return originalFetch.apply(this, args).then(response => {
            if (typeof url === 'string' && url.includes('comfyui/admin/config')) {
                console.log('📊 ComfyUI配置请求响应:');
                console.log('   状态码:', response.status);
                console.log('   状态文本:', response.statusText);
                
                // 克隆响应以便读取（避免消耗原始响应）
                const clonedResponse = response.clone();
                clonedResponse.json().then(data => {
                    console.log('   响应数据:', data);
                }).catch(e => {
                    console.log('   响应不是JSON格式');
                });
            }
            return response;
        }).catch(error => {
            if (typeof url === 'string' && url.includes('comfyui/admin/config')) {
                console.log('❌ ComfyUI配置请求失败:', error);
            }
            throw error;
        });
    };
    
    console.log('✅ 监控脚本已启动，现在可以尝试保存ComfyUI配置');
    console.log('💡 提示：打开开发者工具网络面板也可以查看请求');
})();
"""

    with open("monitor_comfyui_requests.js", "w", encoding="utf-8") as f:
        f.write(monitor_script)

    print(f"📝 已创建请求监控脚本: monitor_comfyui_requests.js")
    print("使用方法：")
    print("1. 打开浏览器开发者工具（F12）")
    print("2. 切换到Console标签")
    print("3. 复制粘贴脚本内容并回车运行")
    print("4. 尝试在Web界面保存ComfyUI配置")
    print("5. 观察控制台输出的请求信息")


def create_troubleshooting_guide():
    """创建故障排除指南"""
    guide = """
# ComfyUI配置保存问题故障排除指南

## 问题现象
Web界面显示配置保存成功，但数据库中access_key和secret_key仍为空

## 已确认正常的部分
✅ 后端API路由正确注册
✅ 后端配置保存功能正常
✅ 数据库表结构完整
✅ 前端代码逻辑正确

## 可能的原因和解决方案

### 1. 认证问题
**症状**: API返回401未认证错误
**检查**: 浏览器网络面板是否显示401状态码
**解决**: 确认管理员用户登录状态，检查token是否有效

### 2. 前端JavaScript错误
**症状**: 前端出现异常，请求未发送
**检查**: 浏览器控制台是否有JavaScript错误
**解决**: 修复前端代码错误

### 3. 网络请求被拦截
**症状**: 请求发送但被防火墙/代理拦截
**检查**: 网络面板显示请求失败或超时
**解决**: 检查网络配置，确保能访问API

### 4. 请求数据格式问题
**症状**: 后端收到请求但数据格式不正确
**检查**: 后端日志是否有数据验证错误
**解决**: 检查前后端数据格式是否匹配

### 5. 浏览器缓存问题
**症状**: 旧版本的前端代码被缓存
**检查**: 强制刷新页面（Ctrl+F5）
**解决**: 清除浏览器缓存或使用无痕模式

### 6. CORS跨域问题
**症状**: 浏览器控制台显示CORS错误
**检查**: 控制台是否有跨域相关错误信息
**解决**: 检查后端CORS配置

## 调试步骤

1. **检查浏览器控制台**
   - 打开F12开发者工具
   - 查看Console标签是否有JavaScript错误
   - 查看Network标签是否有网络请求记录

2. **运行请求监控脚本**
   ```javascript
   // 在控制台运行监控脚本内容
   ```

3. **使用调试工具**
   ```bash
   python debug_comfyui_frontend.py
   ```

4. **手动测试API**
   ```bash
   curl -X POST http://localhost:8080/api/v1/comfyui/admin/config \\
        -H "Content-Type: application/json" \\
        -H "Authorization: Bearer YOUR_TOKEN" \\
        -d '{"access_key":"test","secret_key":"test","base_url":"https://openapi.liblibai.cloud","enabled":true}'
   ```

## 临时解决方案
如果Web界面无法保存，可以使用命令行工具：
```bash
python manual_set_comfyui_config.py
```
"""

    with open("COMFYUI_CONFIG_TROUBLESHOOTING.md", "w", encoding="utf-8") as f:
        f.write(guide)

    print(f"📚 已创建故障排除指南: COMFYUI_CONFIG_TROUBLESHOOTING.md")


if __name__ == "__main__":
    print("🔍 ComfyUI前端请求检查工具")
    print("=" * 60)

    check_recent_requests()
    print()
    create_request_monitor()
    print()
    create_troubleshooting_guide()

    print("\n💡 建议的调试步骤:")
    print("1. 运行 python debug_comfyui_frontend.py 测试完整流程")
    print("2. 在浏览器中使用监控脚本观察请求")
    print("3. 参考故障排除指南进行具体问题的排查")
    print("4. 如有需要使用手动配置脚本作为临时解决方案")
