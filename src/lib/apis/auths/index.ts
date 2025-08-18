import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getAdminDetails = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/admin/details`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getAdminConfig = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/admin/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateAdminConfig = async (token: string, body: object) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/admin/config`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(body)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getSessionUser = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		credentials: 'include'
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const ldapUserSignIn = async (user: string, password: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/ldap`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include',
		body: JSON.stringify({
			user: user,
			password: password
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);

			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getLdapConfig = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/admin/config/ldap`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateLdapConfig = async (token: string = '', enable_ldap: boolean) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/admin/config/ldap`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			enable_ldap: enable_ldap
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getLdapServer = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/admin/config/ldap/server`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateLdapServer = async (token: string = '', body: object) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/admin/config/ldap/server`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(body)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const userSignIn = async (email: string, password: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signin`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include',
		body: JSON.stringify({
			email: email,
			password: password
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);

			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const userSignUp = async (
	name: string,
	email: string,
	password: string,
	profile_image_url: string
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signup`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include',
		body: JSON.stringify({
			name: name,
			email: email,
			password: password,
			profile_image_url: profile_image_url
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const userSignOut = async () => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signout`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include'
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	sessionStorage.clear();
	return res;
};

export const addUser = async (
	token: string,
	name: string,
	email: string,
	password: string,
	role: string = 'pending',
	profile_image_url: null | string = null
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/add`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			name: name,
			email: email,
			password: password,
			role: role,
			...(profile_image_url && { profile_image_url: profile_image_url })
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateUserProfile = async (token: string, name: string, profileImageUrl: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/update/profile`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			name: name,
			profile_image_url: profileImageUrl
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateUserPassword = async (token: string, password: string, newPassword: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/update/password`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			password: password,
			new_password: newPassword
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getSignUpEnabledStatus = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signup/enabled`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getDefaultUserRole = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signup/user/role`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateDefaultUserRole = async (token: string, role: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signup/user/role`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			role: role
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const toggleSignUpEnabledStatus = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signup/enabled/toggle`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getJWTExpiresDuration = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/token/expires`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateJWTExpiresDuration = async (token: string, duration: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/token/expires/update`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			duration: duration
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const createAPIKey = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/api_key`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});
	if (error) {
		throw error;
	}
	return res.api_key;
};

export const getAPIKey = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/api_key`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});
	if (error) {
		throw error;
	}
	return res.api_key;
};

export const deleteAPIKey = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/api_key`, {
		method: 'DELETE',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});
	if (error) {
		throw error;
	}
	return res;
};

////////////////////////////
// SMS and Phone Auth APIs
////////////////////////////

export const sendSmsCode = async (phone: string, purpose: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/send-sms-code`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			phone: phone,
			purpose: purpose
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const verifySmsCode = async (phone: string, code: string, purpose: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/verify-sms-code`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			phone: phone,
			code: code,
			purpose: purpose
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const phoneSignUp = async (
	phone: string,
	code: string,
	name: string,
	password: string,
	profile_image_url: string = '/user.png'
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signup-phone`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include',
		body: JSON.stringify({
			phone: phone,
			code: code,
			name: name,
			password: password,
			profile_image_url: profile_image_url
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const phoneSignIn = async (phone: string, code: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signin-phone`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include',
		body: JSON.stringify({
			phone: phone,
			code: code
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const bindPhone = async (token: string, phone: string, code: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/bind-phone`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			phone: phone,
			code: code
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const bindEmail = async (token: string, email: string, password: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/bind-email`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			email: email,
			password: password
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const unbindPhone = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/unbind-phone`, {
		method: 'DELETE',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const unbindEmail = async (token: string, password: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/unbind-email`, {
		method: 'DELETE',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			password: password
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getBindingStatus = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/binding-status`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getSmsConfig = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/sms/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateSmsConfig = async (token: string, config: any) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/sms/config`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(config)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
