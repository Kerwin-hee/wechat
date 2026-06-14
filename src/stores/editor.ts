import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Article } from '../types'
import * as db from '../db'
import * as articlesApi from '../api/articles'
import { isLoggedIn } from '../api/client'

export const useEditorStore = defineStore('editor', () => {
  // ===== 当前编辑的文章 =====
  const currentArticle = ref<Article | null>(null)
  const currentArticleId = ref<number | null>(null)
  const isDirty = ref(false)
  const lastSavedAt = ref<Date | null>(null)
  const isSaving = ref(false)

  // ===== 编辑器状态 =====
  const wordCount = ref(0)
  const imageCount = ref(0)
  const editorContent = ref('')

  // ===== 面板状态 =====
  const leftPanelOpen = ref(true)
  const rightPanelOpen = ref(true)
  const leftPanelTab = ref<'ai' | 'articles'>('ai')
  const aiSubTab = ref<'full' | 'continue' | 'rewrite' | 'outline' | 'title'>('full')
  const previewDevice = ref<'iphone-se' | 'iphone-14' | 'iphone-14-max' | 'android'>('iphone-14')
  const syncScroll = ref(true)

  // ===== 加载文章 =====
  async function loadArticle(id: number) {
    const article = await db.getArticle(id)
    if (article) {
      currentArticle.value = article
      currentArticleId.value = id
      isDirty.value = false
      editorContent.value = article.content
      wordCount.value = article.wordCount
      imageCount.value = article.imageCount
    }
  }

  // ===== 新建文章 =====
  async function createNewArticle() {
    const id = await db.createArticle()
    await loadArticle(id)
    return id
  }

  // ===== 保存文章（本地 + 云端） =====
  async function saveArticle(content?: string) {
    if (!currentArticleId.value) return

    isSaving.value = true
    try {
      const htmlContent = content || editorContent.value
      const plainText = htmlContent.replace(/<[^>]*>/g, '').trim()
      const words = plainText.length

      // 1. 本地存储
      await db.updateArticle(currentArticleId.value, {
        content: htmlContent,
        plainText,
        wordCount: words,
        title: extractTitle(htmlContent) || currentArticle.value?.title || '未命名文章',
        syncStatus: isLoggedIn() ? 'syncing' : 'local_only',
      })

      // 2. 创建版本快照（本地）
      await db.createVersion(currentArticleId.value, {
        content: htmlContent,
        wordCount: words,
      })
      await db.deleteOldVersions(currentArticleId.value, 20)

      // 3. 云端同步（已登录 + 有 cloudId）
      if (isLoggedIn()) {
        const article = currentArticle.value
        if (article?.cloudId) {
          try {
            await articlesApi.updateArticle(article.cloudId, {
              title: article.title || '未命名文章',
              content: htmlContent,
            })
            await db.updateArticle(currentArticleId.value, { syncStatus: 'synced' })
          } catch {
            await db.updateArticle(currentArticleId.value, { syncStatus: 'failed' })
          }
        } else {
          // 本地文章 → 首次同步到云端
          try {
            const result = await articlesApi.createArticle({
              title: article?.title || '未命名文章',
              content: htmlContent,
              status: 'draft',
            })
            await db.updateArticle(currentArticleId.value, {
              cloudId: result.id,
              syncStatus: 'synced',
            })
          } catch {
            await db.updateArticle(currentArticleId.value, { syncStatus: 'failed' })
          }
        }
      }

      isDirty.value = false
      lastSavedAt.value = new Date()

      // 重新加载
      await loadArticle(currentArticleId.value)
    } finally {
      isSaving.value = false
    }
  }

  // ===== 标记为已修改 =====
  function markDirty() {
    isDirty.value = true
  }

  // ===== 更新编辑器内容 =====
  function updateContent(content: string) {
    editorContent.value = content
    isDirty.value = true
    const plainText = content.replace(/<[^>]*>/g, '').trim()
    wordCount.value = plainText.length
  }

  // ===== 提取标题 =====
  function extractTitle(html: string): string {
    const match = html.match(/<h[1-3][^>]*>(.*?)<\/h[1-3]>/)
    if (match) {
      return match[1].replace(/<[^>]*>/g, '').trim()
    }
    return ''
  }

  return {
    // state
    currentArticle,
    currentArticleId,
    isDirty,
    lastSavedAt,
    isSaving,
    wordCount,
    imageCount,
    editorContent,
    leftPanelOpen,
    rightPanelOpen,
    leftPanelTab,
    aiSubTab,
    previewDevice,
    syncScroll,
    // actions
    loadArticle,
    createNewArticle,
    saveArticle,
    markDirty,
    updateContent,
  }
})
