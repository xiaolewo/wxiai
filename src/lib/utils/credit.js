/**
 * 积分相关工具函数
 * 统一处理积分的格式化和显示
 */

/**
 * 格式化积分为整数显示
 * @param {number|string} credit - 积分值
 * @returns {number} 格式化后的整数积分
 */
export function formatCredit(credit) {
	const num = parseFloat(credit);
	if (isNaN(num)) return 0;
	return Math.round(num);
}

/**
 * 格式化积分价格为整数
 * @param {number} price - 价格值
 * @returns {number} 格式化后的整数价格
 */
export function formatCreditPrice(price) {
	const num = parseFloat(price);
	if (isNaN(num)) return 0;
	return Math.round(num);
}

/**
 * 检查积分是否足够
 * @param {number} current - 当前积分
 * @param {number} required - 需要积分
 * @returns {boolean} 是否足够
 */
export function hasEnoughCredit(current, required) {
	return formatCredit(current) >= formatCredit(required);
}

/**
 * 计算积分差值
 * @param {number} current - 当前积分
 * @param {number} required - 需要积分
 * @returns {number} 积分差值（正数表示不足）
 */
export function getCreditDifference(current, required) {
	return Math.max(0, formatCredit(required) - formatCredit(current));
}

/**
 * 格式化积分显示文本
 * @param {number} credit - 积分值
 * @param {string} unit - 单位（默认"积分"）
 * @returns {string} 格式化后的显示文本
 */
export function formatCreditText(credit, unit = '积分') {
	return `${formatCredit(credit)} ${unit}`;
}
