// ===== 对齐联调文档的数据结构 =====

/** 文章（对齐后端 ArticleData） */
export interface Article {
  /** 本地自增 ID（IndexedDB），云端为 UUID 字符串 */
  id?: number
  /** 云端文章 ID（UUID 格式：art_xxx），本地文章无此字段 */
  cloudId?: string
  title: string
  content: string
  plainText: string
  wordCount: number
  imageCount: number
  totalImageSize: number
  status: 'local' | 'draft' | 'published' | 'trash'
  coverUrl?: string
  summary?: string
  wechatMediaId?: string
  wechatPublishUrl?: string
  /** 同步状态 */
  syncStatus: 'synced' | 'syncing' | 'failed' | 'local_only'
  createdAt: Date
  updatedAt: Date
  publishedAt?: Date
  tags: string[]
}

/** 文章版本（对齐后端 ArticleVersionData） */
export interface ArticleVersion {
  id?: number
  /** 云端版本 ID */
  cloudId?: string
  articleId: number
  versionNumber: number
  title: string
  content: string
  wordCount: number
  diffFromPrevious?: string
  createdAt: Date
}

/** 用户自定义样式（对齐后端 UserStyle） */
export interface UserStyle {
  id?: number
  cloudId?: string
  userId?: string
  name: string
  styleProperties: StyleProperties
  createdAt: Date
}

export interface StyleProperties {
  fontSize?: string
  lineHeight?: string
  letterSpacing?: string
  textIndent?: string
  color?: string
  alignment?: string
  fontFamily?: string
  backgroundColor?: string
  fontWeight?: string
  fontStyle?: string
  marginTop?: string
  marginBottom?: string
}
