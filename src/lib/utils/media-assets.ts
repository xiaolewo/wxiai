import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
import type { MediaAsset } from '$lib/apis/media-library';

type CandidateOptions = {
	preferThumbnail?: boolean;
};

const convertBlobToDataUrl = (blob: Blob) =>
	new Promise<string>((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => resolve(reader.result as string);
		reader.onerror = (err) => reject(err);
		reader.readAsDataURL(blob);
	});

const shouldSendCredentials = (url: string) => {
	if (url.startsWith('/')) return true;
	if (WEBUI_BASE_URL && url.startsWith(WEBUI_BASE_URL)) return true;
	if (WEBUI_API_BASE_URL && url.startsWith(WEBUI_API_BASE_URL)) return true;
	return false;
};

const readMetadataUrl = (asset: MediaAsset): string | null => {
	const metadata = asset.metadata as Record<string, unknown> | null | undefined;
	if (!metadata) return null;
	const possibleKeys = ['cloud_url', 'download_url', 'url'];
	for (const key of possibleKeys) {
		const value = metadata[key];
		if (typeof value === 'string' && value.trim()) {
			return value;
		}
	}
	return null;
};

export const buildAssetContentUrl = (
	asset: MediaAsset,
	options?: { attachment?: boolean }
): string | null => {
	if (!asset?.id) return null;
	const query = new URLSearchParams();
	if (options?.attachment) {
		query.set('attachment', 'true');
	}
	const queryString = query.toString();
	return `${WEBUI_API_BASE_URL}/media-library/assets/${asset.id}/content${
		queryString ? `?${queryString}` : ''
	}`;
};

export const collectAssetSourceUrls = (
	asset: MediaAsset,
	options: CandidateOptions = {}
): string[] => {
	const urls: string[] = [];
	const seen = new Set<string>();

	const push = (value: string | null | undefined) => {
		if (!value) return;
		if (seen.has(value)) return;
		seen.add(value);
		urls.push(value);
	};

	if (options.preferThumbnail) {
		push(asset.thumbnail_url ?? null);
	}

	push(buildAssetContentUrl(asset));

	if (!options.preferThumbnail) {
		push(asset.thumbnail_url ?? null);
	}

	push(asset.file?.cloud_url ?? null);
	push(readMetadataUrl(asset));

	if (asset.file?.id) {
		push(`${WEBUI_API_BASE_URL}/files/${asset.file.id}/content?attachment=false`);
	}

	return urls;
};

export const resolveAssetPreviewUrl = (asset: MediaAsset): string | null => {
	const urls = collectAssetSourceUrls(asset, { preferThumbnail: true });
	return urls[0] ?? null;
};

export const resolveAssetDownloadUrl = (asset: MediaAsset): string | null => {
	return (
		buildAssetContentUrl(asset, { attachment: true }) ??
		readMetadataUrl(asset) ??
		asset.file?.cloud_url ??
		null
	);
};

export async function fetchAssetAsBase64(asset: MediaAsset): Promise<string> {
	if (!asset) {
		throw new Error('未提供媒体资源信息');
	}

	const candidateUrls = collectAssetSourceUrls(asset);
	if (!candidateUrls.length) {
		throw new Error('所选素材缺少可用链接');
	}

	const errors: string[] = [];

	for (const url of candidateUrls) {
		try {
			const response = await fetch(url, {
				credentials: shouldSendCredentials(url) ? 'include' : 'omit'
			});
			if (!response.ok) {
				errors.push(`${url} -> HTTP ${response.status}`);
				continue;
			}

			const blob = await response.blob();
			return await convertBlobToDataUrl(blob);
		} catch (error) {
			errors.push(`${url} -> ${error instanceof Error ? error.message : String(error)}`);
		}
	}

	console.error('媒体库资源下载失败', {
		assetId: asset.id,
		candidateUrls,
		errors
	});

	const lastErrorMessage = errors.length ? errors[errors.length - 1] : '未知错误';
	throw new Error(`下载媒体库资源失败：${lastErrorMessage}`);
}
