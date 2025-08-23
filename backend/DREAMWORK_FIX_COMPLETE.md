# DreamWork 图生图 500/400 错误完整修复报告

## 🎯 问题总结

用户反馈DreamWork图生图功能持续报错：

- 前端显示：`POST http://localhost:8080/api/v1/dreamwork/submit/image-to-image 500 (Internal Server Error)`
- 后端错误：`DreamWork API错误: 提交任务失败，返回 code: 0`

## 🔍 根本原因分析

通过深度诊断发现，问题根源是：

1. **API格式要求错误理解**：DreamWork API的图生图接口要求的是**完整的data URL格式**，而不是裸露的base64数据
2. **图片大小限制**：API拒绝过小的图片（如1x1像素的测试图片）
3. **data URL格式缺失**：原代码错误地移除了`data:image/png;base64,`前缀

### 关键错误信息解读：

```
"Image Decode Error: image format unsupported: invalid image url.
err=Get \"iVBORw0KGg...\": unsupported protocol scheme \"\""
```

这表明API将base64数据误认为URL，导致协议解析失败。

## ✅ 修复方案

### 1. 修复核心文件：`open_webui/utils/dreamwork_fixed.py`

**关键修复点：**

```python
# ❌ 错误做法：移除data URL前缀
if image_data.startswith('data:'):
    image_data = image_data.split(',')[1]  # 移除前缀

# ✅ 正确做法：保持完整data URL格式
if image_data.startswith('data:'):
    data_url = image_data  # 保持完整格式
else:
    # 为纯base64数据添加正确的前缀
    data_url = f"data:image/{image_format};base64,{clean_image_data}"
```

### 2. 完整的修复函数：

```python
async def generate_image_to_image_fixed(config, request) -> dict:
    """修复版图生图函数 - 解决API需要完整data URL格式的问题"""

    # 确保是完整的data URL格式
    if image_data.startswith('data:'):
        data_url = image_data  # 保持完整格式
    else:
        # 检测图片格式并构建正确的data URL
        decoded = base64.b64decode(clean_image_data)
        image_format = detect_image_format(decoded)
        data_url = f"data:image/{image_format};base64,{clean_image_data}"

    # 使用完整的data URL调用API
    request_data = {
        "model": "doubao-seededit-3-0-i2i-250628",
        "prompt": request.prompt.strip(),
        "image": data_url  # 关键：使用完整的data URL
    }
```

## 🧪 验证结果

### 测试前（失败）：

```
状态码: 500
错误: {"code": 0, "msg": "提交任务失败"}
```

### 测试后（成功）：

```
🎨 【DreamWork修复版】响应状态: 200
✅ 修复成功! API返回:
   模型: doubao-seededit-3-0-i2i-250628
   图片数量: 1
   图片URL: https://p3-aiop-sign.byteimg.com/tos-cn-i-vuqhorh5...
```

## 📋 完整修复清单

✅ **数据库修复**：添加缺失的表列（progress, input_image, properties）
✅ **标签修复**：修复DreamWork任务显示"MidJourney"标签的问题
✅ **历史加载修复**：修复DreamWork图片刷新后消失的问题
✅ **API格式修复**：修复图生图API调用的data URL格式问题
✅ **图片大小修复**：确保API接收足够大小的图片数据

## 🚀 部署说明

修复已经完成并验证有效。当前的实现：

1. **路由层**：`open_webui/routers/dreamwork.py` 调用修复版函数
2. **核心修复**：`open_webui/utils/dreamwork_fixed.py` 包含正确的API调用
3. **前端兼容**：保持现有前端接口不变

## 🎉 最终状态

- ✅ 文生图功能：正常工作
- ✅ 图生图功能：**已修复，正常工作**
- ✅ 任务历史：正确保存和显示
- ✅ 积分管理：正常扣费和退费
- ✅ 服务识别：正确显示"即梦 (DreamWork)"标签

## 📞 技术要点总结

1. **data URL格式重要性**：图片必须以`data:image/格式;base64,数据`的完整格式发送
2. **图片大小限制**：避免使用过小的测试图片，建议最小100x100像素
3. **错误诊断技巧**：通过API错误信息"unsupported protocol scheme"识别格式问题
4. **兼容性设计**：修复函数自动检测输入格式并转换为正确格式

**修复时间**：2025-08-17
**修复状态**：完成 ✅
**验证状态**：通过 ✅
