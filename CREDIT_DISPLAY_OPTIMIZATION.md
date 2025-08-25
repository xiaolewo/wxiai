# 积分显示精度优化建议

## 更新内容

已将积分系统优化为：

1. **Token计费**: 不足1000token按1000token计费（向上取整）
2. **积分精度**: 保留1位小数显示

## 前端显示建议

### JavaScript积分格式化函数

```javascript
// 积分显示格式化函数
function formatCredit(credit) {
	const num = parseFloat(credit);
	if (isNaN(num)) return '0.0';

	// 保留1位小数
	return num.toFixed(1);
}

// 使用示例
console.log(formatCredit(10.123456)); // "10.1"
console.log(formatCredit(5)); // "5.0"
console.log(formatCredit(0.5)); // "0.5"
```

### CSS样式建议

```css
.credit-display {
	font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
	font-weight: 600;
	color: #10b981; /* 绿色表示积分 */
}

.credit-insufficient {
	color: #ef4444; /* 红色表示积分不足 */
}
```

### Svelte组件示例

```svelte
<script>
	export let credit = 0;

	function formatCredit(value) {
		return parseFloat(value).toFixed(1);
	}

	$: formattedCredit = formatCredit(credit);
	$: isLow = credit < 1.0;
</script>

<div class="credit-display" class:credit-insufficient={isLow}>
	{formattedCredit} 积分
</div>
```

## API响应格式

确保所有积分相关的API响应都使用1位小数格式：

```json
{
	"user_credit": "10.5",
	"cost": "2.0",
	"remaining": "8.5"
}
```
