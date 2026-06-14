/**
 * 用户样式 API 服务
 *
 * 联调文档参考：
 * - GET    /api/user/styles       获取样式列表
 * - POST   /api/user/styles       创建样式
 * - PUT    /api/user/styles/:id   更新样式
 * - DELETE /api/user/styles/:id   删除样式
 */

import { api } from './client'
import type { StyleProperties } from '../types'

export interface StyleData {
  id: string
  name: string
  style_properties: StyleProperties
  created_at: string
  updated_at: string
}

/**
 * 获取用户样式列表
 */
export async function fetchStyles(): Promise<StyleData[]> {
  return api.get<StyleData[]>('/user/styles')
}

/**
 * 创建样式
 */
export async function createStyle(data: {
  name: string
  style_properties: StyleProperties
}): Promise<StyleData> {
  return api.post<StyleData>('/user/styles', data)
}

/**
 * 更新样式
 */
export async function updateStyle(
  id: string,
  data: Partial<Pick<StyleData, 'name' | 'style_properties'>>
): Promise<StyleData> {
  return api.put<StyleData>(`/user/styles/${id}`, data)
}

/**
 * 删除样式
 */
export async function deleteStyle(id: string): Promise<void> {
  await api.delete(`/user/styles/${id}`)
}
