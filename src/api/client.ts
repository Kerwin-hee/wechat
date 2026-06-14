/**
 * API 客户端封装
 * - 统一请求/响应拦截
 * - Token 管理（JWT Bearer）
 * - 错误码映射
 * - SSE 流式请求支持
 */

// ===== 类型定义 =====

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  request_id?: string
}

export interface PaginatedData<T> {
  list: T[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface ApiError {
  code: number
  message: string
  status: number
}

// ===== Token 管理 =====

const TOKEN_KEY = 'mp_editor_access_token'
const REFRESH_TOKEN_KEY = 'mp_editor_refresh_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setAccessToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string) {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function isLoggedIn(): boolean {
  return !!getAccessToken()
}

// ===== Token 刷新 =====

let refreshPromise: Promise<boolean> | null = null

async function tryRefreshToken(): Promise<boolean> {
  // 避免并发刷新
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    try {
      const refreshToken = getRefreshToken()
      if (!refreshToken) return false

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) return false

      const result: ApiResponse = await response.json()
      if (result.code === 0) {
        setAccessToken(result.data.access_token)
        setRefreshToken(result.data.refresh_token)
        return true
      }
      return false
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

// ===== 请求核心 =====

const BASE_URL = '/api'

interface RequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: any
  signal?: AbortSignal
  noAuth?: boolean
}

/**
 * 通用请求
 */
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = `${BASE_URL}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  // 添加认证头
  if (!options.noAuth) {
    const token = getAccessToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const fetchOptions: RequestInit = {
    method: options.method || 'GET',
    headers,
    signal: options.signal,
  }

  if (options.body && options.method !== 'GET') {
    fetchOptions.body = JSON.stringify(options.body)
  }

  let response = await fetch(url, fetchOptions)

  // Token 过期 → 尝试刷新
  if (response.status === 401 && !options.noAuth) {
    const errorData = await response.json().catch(() => ({}))
    if (errorData.code === 1003) {
      const refreshed = await tryRefreshToken()
      if (refreshed) {
        // 重试原请求
        headers['Authorization'] = `Bearer ${getAccessToken()}`
        response = await fetch(url, { ...fetchOptions, headers })
      } else {
        clearTokens()
        throw createApiError(1002, '请重新登录', 401)
      }
    }
  }

  // 处理响应
  if (!response.ok) {
    let errorData: any
    try {
      errorData = await response.json()
    } catch {
      errorData = { code: 9999, message: '服务器错误' }
    }
    throw createApiError(
      errorData.code || 9999,
      errorData.message || '请求失败',
      response.status
    )
  }

  const result: ApiResponse<T> = await response.json()

  if (result.code !== 0) {
    throw createApiError(result.code, result.message, 200)
  }

  return result.data
}

/**
 * SSE 流式请求
 */
export async function streamRequest(
  path: string,
  body: any,
  onEvent: (eventType: string, data: any) => void,
  signal?: AbortSignal
): Promise<void> {
  const url = `${BASE_URL}${path}`
  const token = getAccessToken()

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw createApiError(
      errorData.code || 9999,
      errorData.message || '请求失败',
      response.status
    )
  }

  const reader = response.body?.getReader()
  if (!reader) throw createApiError(9999, '不支持流式读取', 500)

  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          onEvent(currentEvent, data)
        } catch {
          // 忽略解析失败
        }
      }
    }
  }
}

// ===== 错误处理 =====

function createApiError(code: number, message: string, status: number): ApiError {
  return { code, message, status }
}

/**
 * 获取错误码对应的用户提示
 */
export function getErrorMessage(error: ApiError): string {
  const messages: Record<number, string> = {
    1001: '参数错误',
    1002: '请先登录',
    1003: '登录已过期，请重新登录',
    1004: '无权限访问',
    1005: '资源不存在',
    1006: 'AI 额度已用完',
    1007: '操作频繁，请稍后再试',
    2001: 'AI 服务超时，请重试',
    2002: 'AI 服务暂不可用',
    2003: '内容不符合规范，请修改后重试',
    3001: '微信接口异常，请重新授权',
    9999: '服务器错误，请稍后重试',
  }
  return messages[error.code] || error.message || '未知错误'
}

// ===== 便捷方法 =====

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'GET' }),

  post: <T>(path: string, body?: any, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'POST', body }),

  put: <T>(path: string, body?: any, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PUT', body }),

  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),

  stream: streamRequest,
}
