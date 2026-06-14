/**
 * AI 服务层 — 对接后端 /api/ai/generate SSE 接口
 *
 * 联调文档参考：
 * - POST /api/ai/generate  (SSE 流式)
 * - POST /api/user/quota   (额度查询)
 */

import { api, type ApiError } from '../api/client'

// ===== 类型定义（对齐联调文档） =====

export type AIFunctionType =
  | 'full_article'
  | 'continue_writing'
  | 'rewrite'
  | 'outline'
  | 'title_optimize'

export type AIStyle = 'formal' | 'casual' | 'concise' | 'passionate' | 'professional'
export type TargetAudience = 'general' | 'professional' | 'tech' | 'student'
export type WordCount = '500-1000' | '1000-2000' | '2000-3000'

export interface AIGenerateRequest {
  type: AIFunctionType
  context: string
  options: {
    style?: AIStyle
    target_audience?: TargetAudience
    word_count?: WordCount
    reference_materials?: string
    outline_level?: number
  }
}

export interface AIQuotaItem {
  used: number
  limit: number | null // null = 不限（付费用户）
}

export interface AIQuotaResponse {
  full_article: AIQuotaItem
  continue_writing: AIQuotaItem
  rewrite: AIQuotaItem
  outline: AIQuotaItem
  title_optimize: AIQuotaItem
  reset_at: string
  is_unlimited: boolean
}

export interface AIStartedEvent {
  request_id: string
  quota_remaining: Partial<Record<AIFunctionType, number>>
}

export interface AITokenEvent {
  token: string
  index: number
}

export interface AIDoneEvent {
  total_tokens: number
  finish_reason: string
  quota_remaining: Partial<Record<AIFunctionType, number>>
}

export interface AIErrorEvent {
  code: number
  message: string
  quota_consumed: boolean
}

// ===== SSE 流式生成 =====

export interface StreamCallbacks {
  onStarted?: (data: AIStartedEvent) => void
  onToken: (token: string, index: number) => void
  onDone: (data: AIDoneEvent) => void
  onError: (error: string) => void
}

/**
 * 调用 AI 生成接口（SSE 流式）
 */
export async function aiGenerate(
  params: AIGenerateRequest,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  try {
    await api.stream(
      '/ai/generate',
      params,
      (eventType, data) => {
        switch (eventType) {
          case 'started':
            callbacks.onStarted?.(data as AIStartedEvent)
            break
          case 'token':
            callbacks.onToken(data.token, data.index)
            break
          case 'done':
            callbacks.onDone(data as AIDoneEvent)
            break
          case 'error':
            callbacks.onError(data.message || 'AI 生成失败')
            break
        }
      },
      signal
    )
  } catch (err: any) {
    if (err.name === 'AbortError') {
      callbacks.onError('已取消生成')
      return
    }
    callbacks.onError(err.message || 'AI 服务请求失败')
  }
}

// ===== 额度查询 =====

let cachedQuota: AIQuotaResponse | null = null
let quotaCacheTime = 0

/**
 * 查询 AI 额度
 */
export async function fetchQuota(): Promise<AIQuotaResponse> {
  const now = Date.now()
  if (cachedQuota && now - quotaCacheTime < 30000) {
    return cachedQuota
  }

  const data = await api.get<AIQuotaResponse>('/user/quota')
  cachedQuota = data
  quotaCacheTime = now
  return data
}

/**
 * 获取某个功能类型的剩余次数
 */
export async function getRemainingQuota(type: AIFunctionType): Promise<number> {
  try {
    const quota = await fetchQuota()
    if (quota.is_unlimited) return Infinity
    const item = quota[type]
    if (!item) return 0
    if (item.limit === null) return Infinity
    return Math.max(0, item.limit - item.used)
  } catch {
    return 0
  }
}

/**
 * 清除额度缓存（AI 调用完成后）
 */
export function clearQuotaCache() {
  cachedQuota = null
  quotaCacheTime = 0
}

// ===== 辅助：构建请求参数 =====

export function buildGenerateRequest(
  type: AIFunctionType,
  context: string,
  extra?: Partial<AIGenerateRequest['options']>
): AIGenerateRequest {
  return {
    type,
    context,
    options: {
      ...extra,
    },
  }
}

// ===== 辅助：功能类型中文映射 =====

export const AI_TYPE_LABELS: Record<AIFunctionType, string> = {
  full_article: '全文生成',
  continue_writing: '续写',
  rewrite: '改写',
  outline: '大纲生成',
  title_optimize: '标题优化',
}

// ===== 错误处理 =====

export function isQuotaError(err: ApiError): boolean {
  return err.code === 1006
}

export function isContentError(err: ApiError): boolean {
  return err.code === 2003
}
