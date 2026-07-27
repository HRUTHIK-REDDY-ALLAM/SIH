const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

export async function api(path, { method = 'GET', body, token } = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(`Cannot reach the TradeBridge API at ${BASE} — is the backend running? (cd backend && python run.py)`, 0)
  }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const data = await res.json()
      if (data?.detail) detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch { /* keep default detail */ }
    throw new ApiError(detail, res.status)
  }
  return res.status === 204 ? null : res.json()
}

export const tokens = {
  get: (role) => localStorage.getItem(`tb_token_${role}`),
  set: (role, value) => localStorage.setItem(`tb_token_${role}`, value),
  clear: (role) => localStorage.removeItem(`tb_token_${role}`),
  clearAll: () => {
    localStorage.removeItem('tb_token_msme')
    localStorage.removeItem('tb_token_financier')
  },
}
