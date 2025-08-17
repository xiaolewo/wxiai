import { EventSourceParserStream } from 'eventsource-parser/stream';
import type { ParsedEvent } from 'eventsource-parser';
import { WEBUI_API_BASE_URL } from '$lib/constants';
import type { MJTask } from './index';

// MJ 任务更新类型
export type MJTaskUpdate = {
	type: 'task_update' | 'task_complete' | 'task_failed' | 'credits_update' | 'error';
	taskId?: string;
	task?: MJTask;
	credits?: number;
	error?: string;
	timestamp: number;
};

// 创建 MJ 任务状态 SSE 流
export async function createMJTaskStream(
	token: string,
	taskIds: string[] = []
): Promise<AsyncGenerator<MJTaskUpdate>> {
	const url = new URL(`${WEBUI_API_BASE_URL}/midjourney/stream`);

	// 添加查询参数
	if (taskIds.length > 0) {
		url.searchParams.append('tasks', taskIds.join(','));
	}

	const response = await fetch(url.toString(), {
		method: 'GET',
		headers: {
			Accept: 'text/event-stream',
			'Cache-Control': 'no-cache',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!response.ok) {
		throw new Error(`Failed to establish MJ stream: ${response.statusText}`);
	}

	if (!response.body) {
		throw new Error('Response body is null');
	}

	const eventStream = response.body
		.pipeThrough(new TextDecoderStream())
		.pipeThrough(new EventSourceParserStream())
		.getReader();

	return mjStreamToIterator(eventStream);
}

// 将 SSE 流转换为异步迭代器
async function* mjStreamToIterator(
	reader: ReadableStreamDefaultReader<ParsedEvent>
): AsyncGenerator<MJTaskUpdate> {
	try {
		while (true) {
			const { value, done } = await reader.read();

			if (done) {
				break;
			}

			if (!value || !value.data) {
				continue;
			}

			const data = value.data;

			// 跳过心跳消息
			if (data === '[HEARTBEAT]') {
				continue;
			}

			try {
				const parsedData = JSON.parse(data);
				console.log('MJ Stream Event:', parsedData);

				// 🔥 处理流结束标记
				if (parsedData.type === 'stream_end') {
					console.log('🔄 【流媒体修复版】收到流结束标记，停止监听');
					break;
				}

				// 🔥 过滤重复的已完成任务
				if (
					parsedData.status === 'SUCCESS' ||
					parsedData.status === 'FAILURE' ||
					parsedData.status === 'FAILED'
				) {
					console.log(
						`🔄 【流媒体修复版】收到完成任务事件: ${parsedData.id}, 状态: ${parsedData.status}`
					);
					yield {
						type: 'task_complete',
						taskId: parsedData.id,
						task: parsedData,
						timestamp: Date.now()
					};
					// 任务完成后可以考虑停止这个特定任务的监听
					continue;
				}

				// 处理不同类型的事件
				if (parsedData.type === 'task_update' && parsedData.task) {
					yield {
						type: 'task_update',
						taskId: parsedData.task.id,
						task: parsedData.task,
						timestamp: Date.now()
					};
				} else if (parsedData.type === 'task_complete' && parsedData.task) {
					yield {
						type: 'task_complete',
						taskId: parsedData.task.id,
						task: parsedData.task,
						timestamp: Date.now()
					};
				} else if (parsedData.type === 'task_failed' && parsedData.task) {
					yield {
						type: 'task_failed',
						taskId: parsedData.task.id,
						task: parsedData.task,
						timestamp: Date.now()
					};
				} else if (parsedData.type === 'credits_update' && parsedData.credits !== undefined) {
					yield {
						type: 'credits_update',
						credits: parsedData.credits,
						timestamp: Date.now()
					};
				} else if (parsedData.error) {
					yield {
						type: 'error',
						error: parsedData.error,
						timestamp: Date.now()
					};
				} else if (parsedData.id && (parsedData.status || parsedData.progress)) {
					// 🔥 处理直接的任务数据 (后端修复版本返回格式)
					const isCompleted =
						parsedData.status === 'SUCCESS' ||
						parsedData.status === 'FAILURE' ||
						parsedData.status === 'FAILED';

					yield {
						type: isCompleted ? 'task_complete' : 'task_update',
						taskId: parsedData.id,
						task: parsedData,
						timestamp: Date.now()
					};
				}
			} catch (error) {
				console.error('Error parsing MJ stream event:', error);
				yield {
					type: 'error',
					error: `Failed to parse stream data: ${error.message}`,
					timestamp: Date.now()
				};
			}
		}
	} finally {
		reader.releaseLock();
	}
}

// 创建用户专用的 MJ 任务流（确保用户隔离）
export async function createUserMJTaskStream(
	token: string,
	userId?: string
): Promise<AsyncGenerator<MJTaskUpdate>> {
	const url = new URL(`${WEBUI_API_BASE_URL}/midjourney/stream/user`);

	if (userId) {
		url.searchParams.append('userId', userId);
	}

	const response = await fetch(url.toString(), {
		method: 'GET',
		headers: {
			Accept: 'text/event-stream',
			'Cache-Control': 'no-cache',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!response.ok) {
		throw new Error(`Failed to establish user MJ stream: ${response.statusText}`);
	}

	if (!response.body) {
		throw new Error('Response body is null');
	}

	const eventStream = response.body
		.pipeThrough(new TextDecoderStream())
		.pipeThrough(new EventSourceParserStream())
		.getReader();

	return mjStreamToIterator(eventStream);
}

// MJ 回调处理器类
export class MJCallbackHandler {
	private eventTarget: EventTarget;
	private activeStreams: Map<string, ReadableStreamDefaultReader> = new Map();

	constructor() {
		this.eventTarget = new EventTarget();
	}

	// 订阅特定类型的事件
	subscribe(
		eventType: 'task_update' | 'task_complete' | 'task_failed' | 'credits_update' | 'error',
		callback: (data: MJTaskUpdate) => void
	): () => void {
		const handler = (event: CustomEvent<MJTaskUpdate>) => {
			if (event.detail.type === eventType) {
				callback(event.detail);
			}
		};

		this.eventTarget.addEventListener('mj_event', handler as EventListener);

		// 返回取消订阅函数
		return () => {
			this.eventTarget.removeEventListener('mj_event', handler as EventListener);
		};
	}

	// 开始监听用户的 MJ 任务流
	async startUserStream(token: string, userId?: string): Promise<string> {
		const streamId = `user_${userId || 'default'}_${Date.now()}`;

		try {
			const stream = await createUserMJTaskStream(token, userId);

			// 处理流数据
			this.processStream(stream, streamId);

			return streamId;
		} catch (error) {
			console.error('Failed to start user MJ stream:', error);
			this.dispatchEvent({
				type: 'error',
				error: `Failed to start stream: ${error.message}`,
				timestamp: Date.now()
			});
			throw error;
		}
	}

	// 处理流数据
	private async processStream(stream: AsyncGenerator<MJTaskUpdate>, streamId: string) {
		try {
			for await (const update of stream) {
				this.dispatchEvent(update);
			}
		} catch (error) {
			console.error(`Stream ${streamId} error:`, error);
			this.dispatchEvent({
				type: 'error',
				error: `Stream error: ${error.message}`,
				timestamp: Date.now()
			});
		} finally {
			this.activeStreams.delete(streamId);
		}
	}

	// 分发事件
	private dispatchEvent(data: MJTaskUpdate) {
		const event = new CustomEvent('mj_event', { detail: data });
		this.eventTarget.dispatchEvent(event);
	}

	// 停止所有流
	stopAllStreams() {
		for (const [streamId, reader] of this.activeStreams) {
			try {
				reader.cancel();
				reader.releaseLock();
			} catch (error) {
				console.error(`Error stopping stream ${streamId}:`, error);
			}
		}
		this.activeStreams.clear();
	}

	// 清理资源
	destroy() {
		this.stopAllStreams();
	}
}

// 创建全局 MJ 回调处理器实例
export const mjCallbackHandler = new MJCallbackHandler();
