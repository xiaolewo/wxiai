<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { getSmsConfig, updateSmsConfig } from '$lib/apis/auths';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Switch from '$lib/components/common/Switch.svelte';

	const i18n = getContext('i18n');

	export let saveHandler: Function;

	let smsConfig = {
		username: '',
		password: '',
		signature: '',
		enabled: false
	};

	let loading = false;

	// 保存SMS配置
	const saveConfig = async () => {
		loading = true;
		try {
			await updateSmsConfig(localStorage.token, smsConfig);
			toast.success('SMS配置保存成功');
			saveHandler();
		} catch (error) {
			toast.error(`保存失败：${error}`);
		} finally {
			loading = false;
		}
	};

	// 测试SMS配置
	const testSmsConfig = async () => {
		if (!smsConfig.username || !smsConfig.password || !smsConfig.signature) {
			toast.error('请先完整填写SMS配置信息');
			return;
		}

		loading = true;
		try {
			// 这里可以添加测试SMS配置的API调用
			toast.success('SMS配置测试成功（注意：这只是配置检查，没有发送实际短信）');
		} catch (error) {
			toast.error(`测试失败：${error}`);
		} finally {
			loading = false;
		}
	};

	onMount(async () => {
		try {
			smsConfig = await getSmsConfig(localStorage.token);
		} catch (error) {
			console.error('Failed to load SMS config:', error);
			// 如果获取失败，使用默认配置
		}
	});
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3">
		<div>
			<div class="mb-2 text-sm font-medium">短信服务配置</div>
			<div class="text-xs text-gray-500 mb-4">
				配置短信宝(SMS Bao)服务，用于发送手机验证码。请在短信宝官网注册账号并获取API密钥。
			</div>
		</div>

		<!-- 启用/禁用SMS服务 -->
		<div class="flex items-center justify-between">
			<div class="space-y-1">
				<div class="text-sm font-medium">启用SMS服务</div>
				<div class="text-xs text-gray-500">启用后用户可以使用手机号注册和登录</div>
			</div>
			<Switch bind:state={smsConfig.enabled} />
		</div>

		{#if smsConfig.enabled}
			<hr class="dark:border-gray-850" />

			<!-- SMS Bao用户名 -->
			<div class="space-y-2">
				<div class="flex items-center space-x-2">
					<div class="text-sm font-medium">短信宝用户名</div>
				</div>
				<input
					class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none"
					type="text"
					bind:value={smsConfig.username}
					placeholder="请输入短信宝用户名"
					required
				/>
			</div>

			<!-- SMS Bao密码 -->
			<div class="space-y-2">
				<div class="flex items-center space-x-2">
					<div class="text-sm font-medium">短信宝密码</div>
				</div>
				<SensitiveInput bind:value={smsConfig.password} placeholder="请输入短信宝密码" required />
			</div>

			<!-- SMS签名 -->
			<div class="space-y-2">
				<div class="flex items-center space-x-2">
					<div class="text-sm font-medium">短信签名</div>
				</div>
				<input
					class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none"
					type="text"
					bind:value={smsConfig.signature}
					placeholder="请输入短信签名，例如：【您的网站名】"
					required
				/>
				<div class="text-xs text-gray-500">
					短信签名将显示在验证码短信的开头，请确保已在短信宝平台审核通过
				</div>
			</div>

			<hr class="dark:border-gray-850" />

			<!-- 配置说明 -->
			<div class="space-y-2">
				<div class="text-sm font-medium">配置说明</div>
				<div class="text-xs text-gray-500 space-y-1">
					<div>
						1. 请前往 <a
							href="https://www.smsbao.com/"
							target="_blank"
							class="text-blue-500 hover:underline">短信宝官网</a
						> 注册账号
					</div>
					<div>2. 在"短信设置"中添加短信签名并等待审核通过</div>
					<div>3. 在"API接口"中获取您的用户名和密码</div>
					<div>4. 确保账户有足够的短信余额</div>
				</div>
			</div>

			<!-- 测试按钮 -->
			<div class="flex space-x-2">
				<button
					class="px-3 py-1.5 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition disabled:opacity-50"
					on:click={testSmsConfig}
					disabled={loading}
				>
					{loading ? '测试中...' : '测试配置'}
				</button>
			</div>
		{/if}
	</div>

	<!-- 保存按钮 -->
	<div class="flex justify-end pt-3">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full disabled:opacity-50"
			on:click={saveConfig}
			disabled={loading}
		>
			{loading ? '保存中...' : '保存'}
		</button>
	</div>
</div>
