// ComfyUI配置保存请求监控脚本
// 在浏览器控制台中运行此脚本来监控前端请求

(function () {
	console.log('🚀 开始监控ComfyUI配置保存请求...');

	// 保存原始的fetch函数
	const originalFetch = window.fetch;

	// 重写fetch函数来监控请求
	window.fetch = function (...args) {
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
		return originalFetch
			.apply(this, args)
			.then((response) => {
				if (typeof url === 'string' && url.includes('comfyui/admin/config')) {
					console.log('📊 ComfyUI配置请求响应:');
					console.log('   状态码:', response.status);
					console.log('   状态文本:', response.statusText);

					// 克隆响应以便读取（避免消耗原始响应）
					const clonedResponse = response.clone();
					clonedResponse
						.json()
						.then((data) => {
							console.log('   响应数据:', data);
						})
						.catch((e) => {
							console.log('   响应不是JSON格式');
						});
				}
				return response;
			})
			.catch((error) => {
				if (typeof url === 'string' && url.includes('comfyui/admin/config')) {
					console.log('❌ ComfyUI配置请求失败:', error);
				}
				throw error;
			});
	};

	console.log('✅ 监控脚本已启动，现在可以尝试保存ComfyUI配置');
	console.log('💡 提示：打开开发者工具网络面板也可以查看请求');
})();
