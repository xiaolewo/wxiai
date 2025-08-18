<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';
	import {
		getBindingStatus,
		bindPhone,
		bindEmail,
		unbindPhone,
		unbindEmail,
		sendSmsCode
	} from '$lib/apis/auths';

	const i18n = getContext('i18n');

	let bindingStatus = {
		email: '',
		phone: '',
		has_email: false,
		has_phone: false,
		can_unbind_email: false,
		can_unbind_phone: false
	};

	// 绑定手机号相关状态
	let showBindPhone = false;
	let bindPhoneNumber = '';
	let bindPhoneCode = '';
	let bindPhoneCountdown = 0;
	let bindPhoneInterval = null;

	// 绑定邮箱相关状态
	let showBindEmail = false;
	let bindEmailAddress = '';
	let bindEmailPassword = '';

	// 解绑相关状态
	let showUnbindEmail = false;
	let unbindEmailPassword = '';

	// 手机号格式验证
	const isPhoneNumber = (input) => {
		return /^1[3-9]\d{9}$/.test(input);
	};

	// 邮箱格式验证
	const isEmailAddress = (input) => {
		return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input);
	};

	// 发送绑定手机号验证码
	const sendBindPhoneCode = async () => {
		if (!isPhoneNumber(bindPhoneNumber)) {
			toast.error('请输入正确的手机号');
			return;
		}

		try {
			await sendSmsCode(bindPhoneNumber, 'bind');
			toast.success('验证码已发送');

			// 开始倒计时
			bindPhoneCountdown = 60;
			bindPhoneInterval = setInterval(() => {
				bindPhoneCountdown--;
				if (bindPhoneCountdown <= 0) {
					clearInterval(bindPhoneInterval);
					bindPhoneInterval = null;
				}
			}, 1000);
		} catch (error) {
			toast.error(`发送失败：${error}`);
		}
	};

	// 绑定手机号
	const handleBindPhone = async () => {
		if (!isPhoneNumber(bindPhoneNumber)) {
			toast.error('请输入正确的手机号');
			return;
		}
		if (!bindPhoneCode) {
			toast.error('请输入验证码');
			return;
		}

		try {
			await bindPhone(localStorage.token, bindPhoneNumber, bindPhoneCode);
			toast.success('手机号绑定成功');
			showBindPhone = false;
			bindPhoneNumber = '';
			bindPhoneCode = '';
			await refreshBindingStatus();
		} catch (error) {
			toast.error(`绑定失败：${error}`);
		}
	};

	// 绑定邮箱
	const handleBindEmail = async () => {
		if (!isEmailAddress(bindEmailAddress)) {
			toast.error('请输入正确的邮箱地址');
			return;
		}
		if (!bindEmailPassword) {
			toast.error('请输入当前密码');
			return;
		}

		try {
			await bindEmail(localStorage.token, bindEmailAddress, bindEmailPassword);
			toast.success('邮箱绑定成功');
			showBindEmail = false;
			bindEmailAddress = '';
			bindEmailPassword = '';
			await refreshBindingStatus();
		} catch (error) {
			toast.error(`绑定失败：${error}`);
		}
	};

	// 解绑手机号
	const handleUnbindPhone = async () => {
		try {
			await unbindPhone(localStorage.token);
			toast.success('手机号解绑成功');
			await refreshBindingStatus();
		} catch (error) {
			toast.error(`解绑失败：${error}`);
		}
	};

	// 解绑邮箱
	const handleUnbindEmail = async () => {
		if (!unbindEmailPassword) {
			toast.error('请输入当前密码');
			return;
		}

		try {
			await unbindEmail(localStorage.token, unbindEmailPassword);
			toast.success('邮箱解绑成功');
			showUnbindEmail = false;
			unbindEmailPassword = '';
			await refreshBindingStatus();
		} catch (error) {
			toast.error(`解绑失败：${error}`);
		}
	};

	// 刷新绑定状态
	const refreshBindingStatus = async () => {
		try {
			bindingStatus = await getBindingStatus(localStorage.token);
		} catch (error) {
			console.error('Failed to get binding status:', error);
		}
	};

	// 组件卸载时清理定时器
	const cleanup = () => {
		if (bindPhoneInterval) {
			clearInterval(bindPhoneInterval);
		}
	};

	onMount(async () => {
		await refreshBindingStatus();
		return cleanup;
	});
</script>

<div class="space-y-4">
	<div class="text-sm font-medium">账号绑定管理</div>

	<!-- 当前绑定状态 -->
	<div class="space-y-3">
		<!-- 邮箱状态 -->
		<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-850 rounded-lg">
			<div class="flex items-center space-x-3">
				<div
					class="w-2 h-2 rounded-full {bindingStatus.has_email ? 'bg-green-500' : 'bg-gray-400'}"
				></div>
				<div>
					<div class="text-sm font-medium">邮箱</div>
					<div class="text-xs text-gray-500">
						{bindingStatus.has_email ? bindingStatus.email : '未绑定邮箱'}
					</div>
				</div>
			</div>
			<div class="flex space-x-2">
				{#if !bindingStatus.has_email}
					<button
						class="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition"
						on:click={() => (showBindEmail = true)}
					>
						绑定邮箱
					</button>
				{:else if bindingStatus.can_unbind_email}
					<button
						class="px-3 py-1 text-xs bg-red-500 hover:bg-red-600 text-white rounded transition"
						on:click={() => (showUnbindEmail = true)}
					>
						解绑邮箱
					</button>
				{/if}
			</div>
		</div>

		<!-- 手机号状态 -->
		<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-850 rounded-lg">
			<div class="flex items-center space-x-3">
				<div
					class="w-2 h-2 rounded-full {bindingStatus.has_phone ? 'bg-green-500' : 'bg-gray-400'}"
				></div>
				<div>
					<div class="text-sm font-medium">手机号</div>
					<div class="text-xs text-gray-500">
						{bindingStatus.has_phone ? bindingStatus.phone : '未绑定手机号'}
					</div>
				</div>
			</div>
			<div class="flex space-x-2">
				{#if !bindingStatus.has_phone}
					<button
						class="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition"
						on:click={() => (showBindPhone = true)}
					>
						绑定手机号
					</button>
				{:else if bindingStatus.can_unbind_phone}
					<button
						class="px-3 py-1 text-xs bg-red-500 hover:bg-red-600 text-white rounded transition"
						on:click={handleUnbindPhone}
					>
						解绑手机号
					</button>
				{/if}
			</div>
		</div>
	</div>

	<!-- 绑定手机号弹窗 -->
	{#if showBindPhone}
		<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
				<h3 class="text-lg font-medium mb-4">绑定手机号</h3>

				<div class="space-y-4">
					<div>
						<label class="block text-sm font-medium mb-1">手机号</label>
						<input
							bind:value={bindPhoneNumber}
							type="tel"
							class="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
							placeholder="请输入手机号"
						/>
					</div>

					<div>
						<label class="block text-sm font-medium mb-1">验证码</label>
						<div class="flex gap-2">
							<input
								bind:value={bindPhoneCode}
								type="text"
								class="flex-1 p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
								placeholder="请输入验证码"
								maxlength="6"
							/>
							<button
								class="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm transition disabled:opacity-50"
								disabled={bindPhoneCountdown > 0 || !isPhoneNumber(bindPhoneNumber)}
								on:click={sendBindPhoneCode}
							>
								{bindPhoneCountdown > 0 ? `${bindPhoneCountdown}s` : '获取验证码'}
							</button>
						</div>
					</div>
				</div>

				<div class="flex justify-end space-x-2 mt-6">
					<button
						class="px-4 py-2 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition"
						on:click={() => {
							showBindPhone = false;
							bindPhoneNumber = '';
							bindPhoneCode = '';
						}}
					>
						取消
					</button>
					<button
						class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition"
						on:click={handleBindPhone}
					>
						确认绑定
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- 绑定邮箱弹窗 -->
	{#if showBindEmail}
		<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
				<h3 class="text-lg font-medium mb-4">绑定邮箱</h3>

				<div class="space-y-4">
					<div>
						<label class="block text-sm font-medium mb-1">邮箱地址</label>
						<input
							bind:value={bindEmailAddress}
							type="email"
							class="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
							placeholder="请输入邮箱地址"
						/>
					</div>

					<div>
						<label class="block text-sm font-medium mb-1">当前密码</label>
						<input
							bind:value={bindEmailPassword}
							type="password"
							class="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
							placeholder="请输入当前密码进行验证"
						/>
					</div>
				</div>

				<div class="flex justify-end space-x-2 mt-6">
					<button
						class="px-4 py-2 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition"
						on:click={() => {
							showBindEmail = false;
							bindEmailAddress = '';
							bindEmailPassword = '';
						}}
					>
						取消
					</button>
					<button
						class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition"
						on:click={handleBindEmail}
					>
						确认绑定
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- 解绑邮箱弹窗 -->
	{#if showUnbindEmail}
		<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
				<h3 class="text-lg font-medium mb-4">解绑邮箱</h3>

				<div
					class="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded"
				>
					<p class="text-sm text-yellow-800 dark:text-yellow-200">
						解绑邮箱后，您将只能使用手机号登录。请确保您的手机号仍然有效。
					</p>
				</div>

				<div>
					<label class="block text-sm font-medium mb-1">当前密码</label>
					<input
						bind:value={unbindEmailPassword}
						type="password"
						class="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
						placeholder="请输入当前密码进行验证"
					/>
				</div>

				<div class="flex justify-end space-x-2 mt-6">
					<button
						class="px-4 py-2 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition"
						on:click={() => {
							showUnbindEmail = false;
							unbindEmailPassword = '';
						}}
					>
						取消
					</button>
					<button
						class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded transition"
						on:click={handleUnbindEmail}
					>
						确认解绑
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
