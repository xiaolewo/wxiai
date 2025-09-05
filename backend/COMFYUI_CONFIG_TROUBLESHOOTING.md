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
   curl -X POST http://localhost:8080/api/v1/comfyui/admin/config \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer YOUR_TOKEN" \
        -d '{"access_key":"test","secret_key":"test","base_url":"https://openapi.liblibai.cloud","enabled":true}'
   ```

## 临时解决方案

如果Web界面无法保存，可以使用命令行工具：

```bash
python manual_set_comfyui_config.py
```
