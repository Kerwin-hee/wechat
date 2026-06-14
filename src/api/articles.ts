/**
 * 文章管理 API 服务 — 对接后端 REST 接口
 *
 * 联调文档参考：
 * - GET    /api/articles         列表
 * - POST   /api/articles         创建
 * - GET    /api/articles/:id     详情
 * - PUT    /api/articles/:id     更新
 * - DELETE /api/articles/:id     删除
 * - GET    /api/articles/:id/versions      版本列表
 * - POST   /api/articles/:id/restore/:vid  恢复版本
 */

import { api, type PaginatedData } from './client'

// ===== 类型定义（对齐联调文档） =====

export type ArticleStatus = 'draft' | 'published' | 'trash'
export type SyncStatus = 'synced' | 'syncing' | 'failed' | 'local_only'

export interface ArticleData {
  id: string
  title: string
  content: string
  plain_text: string
  word_count: number
  image_count: number
  total_image_size: number
  status: ArticleStatus
  cover_url: string | null
  summary: string | null
  wechat_media_id: string | null
  wechat_publish_url: string | null
  tags: string[]
  created_at: string
  updated_at: string
  published_at: string | null
  sync_status?: SyncStatus
}

export interface ArticleVersionData {
  id: string
  article_id: string
  version_number: number
  title: string
  content: string
  word_count: number
  diff_from_previous: string | null
  created_at: string
}

export interface ArticleListParams {
  page?: number
  page_size?: number
  status?: ArticleStatus
  keyword?: string
  sort_by?: 'created_at' | 'updated_at' | 'word_count'
  order?: 'asc' | 'desc'
}

// ===== API 方法 =====

/**
 * 获取文章列表
 */
export async function fetchArticles(params: ArticleListParams = {}): Promise<PaginatedData<ArticleData>> {
  const query = new URLSearchParams()
  if (params.page) query.set('page', String(params.page))
  if (params.page_size) query.set('page_size', String(params.page_size))
  if (params.status) query.set('status', params.status)
  if (params.keyword) query.set('keyword', params.keyword)
  if (params.sort_by) query.set('sort_by', params.sort_by)
  if (params.order) query.set('order', params.order)

  const qs = query.toString()
  return api.get<PaginatedData<ArticleData>>(`/articles${qs ? '?' + qs : ''}`)
}

/**
 * 获取文章详情
 */
export async function fetchArticle(id: string): Promise<ArticleData> {
  return api.get<ArticleData>(`/articles/${id}`)
}

/**
 * 创建文章
 */
export async function createArticle(data: {
  title?: string
  content?: string
  status?: ArticleStatus
}): Promise<ArticleData> {
  return api.post<ArticleData>('/articles', {
    title: data.title || '未命名文章',
    content: data.content || '<p></p>',
    status: data.status || 'draft',
  })
}

/**
 * 更新文章（部分更新）
 */
export async function updateArticle(
  id: string,
  data: Partial<Pick<ArticleData, 'title' | 'content' | 'summary' | 'tags'>>
): Promise<ArticleData> {
  return api.put<ArticleData>(`/articles/${id}`, data)
}

/**
 * 删除文章（软删除 → trash）
 */
export async function deleteArticle(id: string): Promise<void> {
  await api.delete(`/articles/${id}`)
}

// ===== 版本历史 =====

/**
 * 获取版本列表
 */
export async function fetchVersions(
  articleId: string,
  page = 1,
  pageSize = 50
): Promise<PaginatedData<ArticleVersionData>> {
  return api.get<PaginatedData<ArticleVersionData>>(
    `/articles/${articleId}/versions?page=${page}&page_size=${pageSize}`
  )
}

/**
 * 恢复版本
 */
export async function restoreVersion(
  articleId: string,
  versionId: string
): Promise<ArticleData> {
  return api.post<ArticleData>(`/articles/${articleId}/restore/${versionId}`)
}
