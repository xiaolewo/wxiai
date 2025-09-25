import { WEBUI_API_BASE_URL } from '$lib/constants';
import { toast } from 'svelte-sonner';

export type MediaAssetFile = {
	id: string | null;
	cloud_url: string | null;
	storage_provider: string | null;
	file_size: number | null;
	mime_type: string | null;
	status: string | null;
};

export type MediaAsset = {
	id: string;
	display_name: string;
	media_type: string;
	mime_type: string | null;
	visibility_scope: 'user' | 'group';
	owner_id: string;
	folder_id: string | null;
	tags: Record<string, unknown> | null;
	metadata: Record<string, unknown> | null;
	source: string | null;
	thumbnail_url: string | null;
	checksum: string | null;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
	width: number | null;
	height: number | null;
	duration: number | null;
	file: MediaAssetFile | null;
	can_manage?: boolean;
};

export type MediaFolder = {
	id: string;
	parent_id: string | null;
	visibility_scope: 'user' | 'group';
	owner_id: string;
	name: string;
	slug: string | null;
	preset_key: string | null;
	sort_order: number;
	is_locked: boolean;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
};

export type MediaAssetListResponse = {
	data: MediaAsset[];
	total: number;
	page: number;
	limit: number;
};

export type MediaLibrarySettingsForm = {
	enable_group_sharing?: boolean;
	allow_bulk_download?: boolean;
	allowed_media_types?: string[] | null;
	default_visibility?: 'user' | 'group';
	max_storage_per_user?: number | null;
	max_storage_per_group?: number | null;
	signed_url_ttl_seconds?: number | null;
	thumbnail_strategy?: string | null;
	extra_config?: Record<string, unknown> | null;
};

const buildHeaders = (token: string) => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	...(token && { Authorization: `Bearer ${token}` })
});

const handleResponse = async (res: Response) => {
	if (!res.ok) {
		let detail = res.statusText;
		try {
			const body = await res.json();
			detail = body?.detail ?? JSON.stringify(body);
		} catch (error) {
			// no-op
		}
		throw new Error(detail);
	}
	try {
		return await res.json();
	} catch (error) {
		return null;
	}
};

export const getMediaLibrarySettings = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/settings`, {
		method: 'GET',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export const listMediaAssets = async (
	token: string,
	params: {
		scope?: string;
		page?: number;
		limit?: number;
		mediaType?: string;
		folderId?: string;
		includeDeleted?: boolean;
		search?: string;
		source?: string;
	}
): Promise<MediaAssetListResponse> => {
	const searchParams = new URLSearchParams();
	if (params.scope) searchParams.append('scope', params.scope);
	if (params.page) searchParams.append('page', params.page.toString());
	if (params.limit) searchParams.append('limit', params.limit.toString());
	if (params.mediaType) searchParams.append('media_type', params.mediaType);
	if (params.folderId) searchParams.append('folder_id', params.folderId);
	if (params.includeDeleted) searchParams.append('include_deleted', 'true');
	if (params.search) searchParams.append('search', params.search);
	if (params.source) searchParams.append('source', params.source);

	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/assets?${searchParams.toString()}`, {
		method: 'GET',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export const updateMediaAsset = async (
	token: string,
	assetId: string,
	payload: Record<string, unknown>
): Promise<MediaAsset> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/assets/${assetId}`, {
		method: 'PATCH',
		headers: buildHeaders(token),
		body: JSON.stringify(payload)
	});
	return handleResponse(res);
};

export const deleteMediaAsset = async (token: string, assetId: string): Promise<MediaAsset> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/assets/${assetId}`, {
		method: 'DELETE',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export const restoreMediaAsset = async (token: string, assetId: string): Promise<MediaAsset> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/assets/${assetId}/restore`, {
		method: 'POST',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export const listMediaFolders = async (token: string, scope: string): Promise<MediaFolder[]> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/folders?scope=${scope}`, {
		method: 'GET',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export const createMediaFolder = async (
	token: string,
	payload: Record<string, unknown>
): Promise<MediaFolder> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/folders`, {
		method: 'POST',
		headers: buildHeaders(token),
		body: JSON.stringify(payload)
	});
	return handleResponse(res);
};

export const updateMediaFolder = async (
	token: string,
	folderId: string,
	payload: Record<string, unknown>
): Promise<MediaFolder> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/folders/${folderId}`, {
		method: 'PATCH',
		headers: buildHeaders(token),
		body: JSON.stringify(payload)
	});
	return handleResponse(res);
};

export const deleteMediaFolder = async (token: string, folderId: string): Promise<MediaFolder> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/folders/${folderId}`, {
		method: 'DELETE',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export const restoreMediaFolder = async (token: string, folderId: string): Promise<MediaFolder> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/folders/${folderId}/restore`, {
		method: 'POST',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export type MediaUploadOptions = {
	folderId?: string;
	visibilityScope?: 'user' | 'group';
	ownerId?: string;
	title?: string;
	tags?: Record<string, unknown> | string;
};

export const uploadMediaAsset = async (
	token: string,
	file: File,
	options: MediaUploadOptions = {}
): Promise<MediaAsset> => {
	const formData = new FormData();
	formData.append('file', file);
	if (options.folderId) formData.append('folder_id', options.folderId);
	if (options.visibilityScope) formData.append('visibility_scope', options.visibilityScope);
	if (options.ownerId) formData.append('owner_id', options.ownerId);
	if (options.title) formData.append('title', options.title);
	if (options.tags) {
		formData.append(
			'tags',
			typeof options.tags === 'string' ? options.tags : JSON.stringify(options.tags)
		);
	}

	const res = await fetch(`${WEBUI_API_BASE_URL}/media-library/upload`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
		},
		body: formData
	});
	return handleResponse(res);
};

// Admin APIs
export const adminListMediaAssets = async (
	token: string,
	params: {
		page?: number;
		limit?: number;
		mediaType?: string;
		folderId?: string;
		includeDeleted?: boolean;
		search?: string;
		source?: string;
		ownerId?: string;
		visibilityScope?: string;
	}
): Promise<MediaAssetListResponse> => {
	const searchParams = new URLSearchParams();
	if (params.page) searchParams.append('page', params.page.toString());
	if (params.limit) searchParams.append('limit', params.limit.toString());
	if (params.mediaType) searchParams.append('media_type', params.mediaType);
	if (params.folderId) searchParams.append('folder_id', params.folderId);
	if (params.includeDeleted) searchParams.append('include_deleted', 'true');
	if (params.search) searchParams.append('search', params.search);
	if (params.source) searchParams.append('source', params.source);
	if (params.ownerId) searchParams.append('owner_id', params.ownerId);
	if (params.visibilityScope) searchParams.append('visibility_scope', params.visibilityScope);

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/admin/media-library/assets?${searchParams.toString()}`,
		{
			method: 'GET',
			headers: buildHeaders(token)
		}
	);
	return handleResponse(res);
};

export const adminReassignAsset = async (
	token: string,
	assetId: string,
	payload: { owner_id: string; visibility_scope: string }
): Promise<MediaAsset> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/admin/media-library/assets/${assetId}/reassign`, {
		method: 'POST',
		headers: buildHeaders(token),
		body: JSON.stringify(payload)
	});
	return handleResponse(res);
};

export const adminUpdateSettings = async (token: string, payload: MediaLibrarySettingsForm) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/admin/media-library/settings`, {
		method: 'PATCH',
		headers: buildHeaders(token),
		body: JSON.stringify(payload)
	});
	return handleResponse(res);
};

export const adminGetMediaLibrarySettings = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/admin/media-library/settings`, {
		method: 'GET',
		headers: buildHeaders(token)
	});
	return handleResponse(res);
};

export const notifyError = (message: string) => {
	toast.error(message);
};
