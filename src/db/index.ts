import Dexie, { type Table } from 'dexie'
import type { Article, ArticleVersion, UserStyle } from '../types'

class MpEditorDB extends Dexie {
  articles!: Table<Article, number>
  versions!: Table<ArticleVersion, number>
  styles!: Table<UserStyle, number>

  constructor() {
    super('MpEditorDB')

    // v1: 初始 schema
    this.version(1).stores({
      articles: '++id, title, status, updatedAt, createdAt',
      versions: '++id, articleId, versionNumber, createdAt',
      styles: '++id, userId, name, createdAt',
    })

    // v2: 新增 cloudId, syncStatus 字段索引
    this.version(2).stores({
      articles: '++id, cloudId, title, status, syncStatus, updatedAt, createdAt',
      versions: '++id, cloudId, articleId, versionNumber, createdAt',
      styles: '++id, cloudId, userId, name, createdAt',
    }).upgrade((tx) => {
      // 为已有文章设置默认 syncStatus
      return tx.table('articles').toCollection().modify((article: Article) => {
        if (!article.syncStatus) {
          article.syncStatus = 'local_only'
        }
      })
    })
  }
}

const db = new MpEditorDB()

// ===== Article CRUD =====

export async function createArticle(data: Partial<Article> = {}): Promise<number> {
  const now = new Date()
  const article: Article = {
    title: data.title || '未命名文章',
    content: data.content || '',
    plainText: data.plainText || '',
    wordCount: data.wordCount || 0,
    imageCount: data.imageCount || 0,
    totalImageSize: data.totalImageSize || 0,
    status: data.status || 'local',
    syncStatus: 'local_only',
    tags: data.tags || [],
    createdAt: now,
    updatedAt: now,
  }
  return db.articles.add(article)
}

export async function getArticle(id: number): Promise<Article | undefined> {
  return db.articles.get(id)
}

export async function getAllArticles(status?: Article['status']): Promise<Article[]> {
  let query = db.articles.orderBy('updatedAt')
  if (status) {
    const all = await query.reverse().toArray()
    return all.filter((a) => a.status === status)
  }
  return query.reverse().toArray()
}

export async function updateArticle(id: number, data: Partial<Article>): Promise<number> {
  return db.articles.update(id, {
    ...data,
    updatedAt: new Date(),
  })
}

export async function deleteArticle(id: number): Promise<void> {
  // 也删除关联的版本
  await db.versions.where('articleId').equals(id).delete()
  await db.articles.delete(id)
}

export async function searchArticles(keyword: string): Promise<Article[]> {
  const lower = keyword.toLowerCase()
  const all = await db.articles.toArray()
  return all.filter(
    (a) =>
      a.title.toLowerCase().includes(lower) ||
      a.plainText.toLowerCase().includes(lower)
  )
}

// ===== Article Version =====

export async function createVersion(articleId: number, data: Partial<ArticleVersion>): Promise<number> {
  const existing = await db.versions
    .where('articleId')
    .equals(articleId)
    .reverse()
    .first()

  const versionNumber = existing ? existing.versionNumber + 1 : 1
  const article = await getArticle(articleId)

  const version: ArticleVersion = {
    articleId,
    versionNumber,
    title: data.title || article?.title || '',
    content: data.content || article?.content || '',
    wordCount: data.wordCount || article?.wordCount || 0,
    createdAt: new Date(),
  }
  return db.versions.add(version)
}

export async function getVersions(articleId: number): Promise<ArticleVersion[]> {
  return db.versions
    .where('articleId')
    .equals(articleId)
    .reverse()
    .toArray()
}

export async function getVersion(versionId: number): Promise<ArticleVersion | undefined> {
  return db.versions.get(versionId)
}

export async function deleteOldVersions(articleId: number, keepCount: number = 20): Promise<void> {
  const versions = await db.versions
    .where('articleId')
    .equals(articleId)
    .reverse()
    .toArray()

  if (versions.length > keepCount) {
    const toDelete = versions.slice(keepCount).map((v) => v.id!)
    await db.versions.bulkDelete(toDelete)
  }
}

// ===== User Styles =====

export async function saveStyle(style: Omit<UserStyle, 'id'>): Promise<number> {
  return db.styles.add(style)
}

export async function getAllStyles(): Promise<UserStyle[]> {
  return db.styles.orderBy('createdAt').reverse().toArray()
}

export async function deleteStyle(id: number): Promise<void> {
  await db.styles.delete(id)
}

export async function updateStyle(id: number, data: Partial<UserStyle>): Promise<number> {
  return db.styles.update(id, data)
}

// ===== Storage Check =====

export async function estimateStorageUsage(): Promise<{ used: number; quota: number }> {
  if (navigator.storage && navigator.storage.estimate) {
    const est = await navigator.storage.estimate()
    return {
      used: est.usage || 0,
      quota: est.quota || 0,
    }
  }
  return { used: 0, quota: 0 }
}

export default db
