/**
 * 用户认证 API 服务
 *
 * 联调文档参考：
 * - GET  /api/auth/wechat/qrcode   获取微信登录二维码
 * - GET  /api/auth/wechat/status   轮询扫码状态
 * - POST /api/auth/refresh         Token 刷新
 * - GET  /api/user/quota           AI 额度查询
 */

import { api, setAccessToken, setRefreshToken, clearTokens, isLoggedIn } from './client'
import type { AIQuotaResponse } from '../services/aiService'

// ===== 类型 =====

export type LoginStatus = 'pending' | 'scanned' | 'success' | 'expired'

export interface WechatQrcodeData {
  qrcode_url: string
  scene_id: string
  expires_in: number
}

export interface WechatStatusData {
  status: LoginStatus
  access_token?: string
  refresh_token?: string
  expires_in?: number
  user?: UserProfile
}

export interface UserProfile {
  id: string
  nickname: string
  avatar: string
  membership: 'free' | 'pro'
  is_new_user: boolean
}

// ===== API =====

/**
 * 获取微信登录二维码
 */
export async function fetchWechatQrcode(): Promise<WechatQrcodeData> {
  return api.get<WechatQrcodeData>('/auth/wechat/qrcode', { noAuth: true })
}

/**
 * 轮询微信扫码状态
 */
export async function pollWechatStatus(sceneId: string): Promise<WechatStatusData> {
  return api.get<WechatStatusData>(`/auth/wechat/status?scene_id=${sceneId}`, { noAuth: true })
}

/**
 * 处理登录成功
 */
export function handleLoginSuccess(data: WechatStatusData) {
  if (data.access_token) {
    setAccessToken(data.access_token)
  }
  if (data.refresh_token) {
    setRefreshToken(data.refresh_token)
  }
}

/**
 * 登出
 */
export function logout() {
  clearTokens()
}

/**
 * 获取当前用户信息（从 token 或缓存）
 */
export function getCurrentUser(): UserProfile | null {
  try {
    const raw = localStorage.getItem('mp_editor_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setCurrentUser(user: UserProfile) {
  localStorage.setItem('mp_editor_user', JSON.stringify(user))
}

/**
 * 获取 AI 额度
 */
export async function fetchAIQuota(): Promise<AIQuotaResponse> {
  return api.get<AIQuotaResponse>('/user/quota')
}

/**
 * 检查登录状态
 */
export function checkLoginStatus(): boolean {
  return isLoggedIn()
}
