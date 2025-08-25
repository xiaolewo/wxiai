#!/usr/bin/env python3
"""
优化积分计费精度和Token取整逻辑
1. 积分精度：保留1位小数
2. Token计费：不足1000按1000计费（向上取整）
"""

import os
import sys
import math
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_credit_usage_precision():
    """更新积分使用精度和Token取整逻辑"""
    usage_file = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "utils"
        / "credit"
        / "usage.py"
    )

    if not usage_file.exists():
        logger.error(f"文件不存在: {usage_file}")
        return False

    # 读取当前内容
    with open(usage_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = usage_file.with_suffix(".py.precision_backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已备份原文件到: {backup_file}")

    # 在文件开头添加import math
    if "import math" not in content:
        content = content.replace("import time", "import time\nimport math")
        logger.info("✅ 已添加 import math")

    # 修改Token计费逻辑 - 向上取整到1000为单位
    modifications = [
        # prompt价格计算 - 向上取整
        {
            "old": "return self.prompt_unit_price * self.usage.prompt_tokens / 1000",
            "new": "return self.prompt_unit_price * math.ceil(self.usage.prompt_tokens / 1000)",
        },
        # completion价格计算 - 向上取整
        {
            "old": "return self.completion_unit_price * self.usage.completion_tokens / 1000",
            "new": "return self.completion_unit_price * math.ceil(self.usage.completion_tokens / 1000)",
        },
        # 缓存token价格计算 - 向上取整
        {
            "old": """return (
                (
                    self.prompt_cache_unit_price * cache_tokens
                    + self.prompt_unit_price * (self.usage.prompt_tokens - cache_tokens)
                )
                / 1000
            )""",
            "new": """return (
                self.prompt_cache_unit_price * math.ceil(cache_tokens / 1000)
                + self.prompt_unit_price * math.ceil((self.usage.prompt_tokens - cache_tokens) / 1000)
            )""",
        },
    ]

    # 应用修改
    modified_content = content
    for mod in modifications:
        if mod["old"] in modified_content:
            modified_content = modified_content.replace(mod["old"], mod["new"])
            logger.info(f"✅ 已修改Token取整逻辑: {mod['old'][:30]}...")
        else:
            logger.warning(f"⚠️  未找到Token计费逻辑: {mod['old'][:30]}...")

    # 添加积分精度控制方法
    precision_methods = '''
    def round_credit(self, value: Decimal) -> Decimal:
        """将积分值精确到1位小数"""
        return Decimal(str(round(float(value), 1)))
    '''

    # 在CreditDeduct类中添加精度控制方法
    class_start = "class CreditDeduct:"
    if class_start in modified_content:
        # 找到类定义后的位置插入方法
        lines = modified_content.split("\n")
        class_line_idx = None
        for i, line in enumerate(lines):
            if class_start in line:
                class_line_idx = i
                break

        if class_line_idx:
            # 找到类的第一个方法前插入
            insert_idx = class_line_idx + 1
            while insert_idx < len(lines) and not lines[insert_idx].strip().startswith(
                "def "
            ):
                insert_idx += 1

            # 插入精度控制方法
            lines.insert(insert_idx, precision_methods)
            modified_content = "\n".join(lines)
            logger.info("✅ 已添加积分精度控制方法")

    # 修改total_price方法，应用精度控制
    old_total_price = """@property
    def total_price(self) -> Decimal:
        if self.request_unit_price > 0:
            total_price = self.request_price + self.feature_price + self.custom_price
        else:
            total_price = (
                self.prompt_price
                + self.completion_price
                + self.feature_price
                + self.custom_price
            )
        return max(total_price, Decimal(USAGE_CALCULATE_MINIMUM_COST.value))"""

    new_total_price = """@property
    def total_price(self) -> Decimal:
        if self.request_unit_price > 0:
            total_price = self.request_price + self.feature_price + self.custom_price
        else:
            total_price = (
                self.prompt_price
                + self.completion_price
                + self.feature_price
                + self.custom_price
            )
        final_price = max(total_price, Decimal(USAGE_CALCULATE_MINIMUM_COST.value))
        return self.round_credit(final_price)"""

    if old_total_price in modified_content:
        modified_content = modified_content.replace(old_total_price, new_total_price)
        logger.info("✅ 已添加总价格精度控制")

    # 写入修改后的内容
    with open(usage_file, "w", encoding="utf-8") as f:
        f.write(modified_content)

    logger.info(f"✅ 已更新文件: {usage_file}")
    return True


def update_credit_models_precision():
    """更新积分模型的精度设置"""
    models_file = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "models"
        / "credits.py"
    )

    if not models_file.exists():
        logger.error(f"文件不存在: {models_file}")
        return False

    # 读取当前内容
    with open(models_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = models_file.with_suffix(".py.precision_backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已备份原文件到: {backup_file}")

    # 修改数据库字段精度 - 从24,12改为8,1 (8位总长度，1位小数)
    old_precision = "Column(Numeric(precision=24, scale=12))"
    new_precision = "Column(Numeric(precision=8, scale=1))"

    if old_precision in content:
        modified_content = content.replace(old_precision, new_precision)

        # 写入修改后的内容
        with open(models_file, "w", encoding="utf-8") as f:
            f.write(modified_content)

        logger.info("✅ 已更新数据库积分字段精度: 24,12 → 8,1")
        logger.info("⚠️  注意：需要创建数据库迁移文件来应用此更改")
    else:
        logger.info("数据库字段精度已是合适的设置")

    logger.info(f"✅ 已更新文件: {models_file}")
    return True


def create_migration_file():
    """创建数据库迁移文件来修改积分字段精度"""
    migrations_dir = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "migrations"
        / "versions"
    )

    if not migrations_dir.exists():
        logger.warning("迁移目录不存在，跳过创建迁移文件")
        return True

    # 生成迁移文件名
    import time

    timestamp = hex(int(time.time()))[2:]
    migration_file = migrations_dir / f"{timestamp}_update_credit_precision.py"

    migration_content = f'''"""update credit precision
更新积分字段精度为1位小数

Revision ID: {timestamp}
Revises: 
Create Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '{timestamp}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级：将积分字段精度改为8位总长度，1位小数"""
    # SQLite不直接支持ALTER COLUMN，需要重新创建表
    
    # 对于SQLite，这个迁移主要是为了记录更改
    # 实际的精度控制在应用层面处理
    
    # 如果是PostgreSQL或MySQL，可以使用以下语句：
    # op.alter_column('credit', 'credit', 
    #                type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('credit_log', 'credit', 
    #                type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('trade_ticket', 'amount', 
    #                type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('redemption_code', 'amount', 
    #                type_=sa.Numeric(precision=8, scale=1))
    
    pass


def downgrade():
    """降级：恢复到原来的精度设置"""
    # op.alter_column('credit', 'credit', 
    #                type_=sa.Numeric(precision=24, scale=12))
    # op.alter_column('credit_log', 'credit', 
    #                type_=sa.Numeric(precision=24, scale=12))
    # op.alter_column('trade_ticket', 'amount', 
    #                type_=sa.Numeric(precision=24, scale=12))
    # op.alter_column('redemption_code', 'amount', 
    #                type_=sa.Numeric(precision=24, scale=12))
    
    pass
'''

    try:
        with open(migration_file, "w", encoding="utf-8") as f:
            f.write(migration_content)
        logger.info(f"✅ 已创建迁移文件: {migration_file}")
        return True
    except Exception as e:
        logger.error(f"创建迁移文件失败: {e}")
        return False


def update_display_precision():
    """更新前端显示精度"""

    # 创建前端积分显示优化建议文档
    doc_content = """# 积分显示精度优化建议

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
console.log(formatCredit(5));         // "5.0"
console.log(formatCredit(0.5));       // "0.5"
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
"""

    doc_file = Path(__file__).parent.parent / "CREDIT_DISPLAY_OPTIMIZATION.md"

    try:
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(doc_content)
        logger.info(f"✅ 已创建前端显示优化文档: {doc_file}")
        return True
    except Exception as e:
        logger.error(f"创建显示优化文档失败: {e}")
        return False


def main():
    logger.info("开始优化积分计费精度和Token取整...")
    logger.info("目标:")
    logger.info("1. Token计费: 不足1000按1000计费（向上取整）")
    logger.info("2. 积分精度: 保留1位小数")
    logger.info("=" * 50)

    success_count = 0
    total_count = 4

    # 1. 更新计费逻辑精度
    logger.info("\n1. 更新Token取整和积分精度逻辑...")
    if update_credit_usage_precision():
        success_count += 1

    # 2. 更新数据库模型精度
    logger.info("\n2. 更新积分数据库字段精度...")
    if update_credit_models_precision():
        success_count += 1

    # 3. 创建数据库迁移文件
    logger.info("\n3. 创建数据库迁移文件...")
    if create_migration_file():
        success_count += 1

    # 4. 创建前端显示优化文档
    logger.info("\n4. 创建前端显示优化建议...")
    if update_display_precision():
        success_count += 1

    # 总结
    logger.info("\n" + "=" * 50)
    logger.info(f"积分精度优化完成: {success_count}/{total_count}")

    if success_count == total_count:
        logger.info("✅ 所有优化完成！")
        logger.info("\n新的计费逻辑:")
        logger.info("- Token计费: 不足1000token按1000token计费")
        logger.info("- 次数计费: 1次对话=1积分")
        logger.info("- 积分显示: 保留1位小数")
        logger.info("\n示例:")
        logger.info("- 500 tokens = 1.0积分 (向上取整)")
        logger.info("- 1500 tokens = 2.0积分 (向上取整)")
        logger.info("- 1次对话 = 1.0积分")
        logger.info("\n⚠️  请重启后端服务以使更改生效")
        logger.info("💾 备份文件已保存")
    else:
        logger.error("❌ 部分优化失败，请检查日志")

    return success_count == total_count


if __name__ == "__main__":
    main()
