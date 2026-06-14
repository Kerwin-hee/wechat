<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEditorStore } from '../../stores/editor'
import * as db from '../../db'
import * as articlesApi from '../../api/articles'
import { isLoggedIn } from '../../api/client'
import type { Article } from '../../types'

const store = useEditorStore()

const articles = ref<Article[]>([])
const activeStatus = ref<'local' | 'draft' | 'published'>('local')
const searchKeyword = ref('')
const isSyncing = ref(false)

const filteredArticles = computed(() => {
  let list = articles.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(
      (a) =>
        a.title.toLowerCase().includes(kw) ||
        a.plainText.toLowerCase().includes(kw)
    )
  }
  return list
})

/** 加载文章列表：本地 + 云端合并 */
async function loadArticles() {
  // 1. 加载本地文章
  const localArticles = await db.getAllArticles(activeStatus.value)
  articles.value = localArticles

  // 2. 如果已登录且不是纯本地视图，从云端拉取并合并
  if (isLoggedIn() && activeStatus.value !== 'local') {
    isSyncing.value = true
    try {
      const result = await articlesApi.fetchArticles({
        status: activeStatus.value as 'draft' | 'published',
        page_size: 100,
        sort_by: 'updated_at',
        order: 'desc',
      })

      // 将云端数据映射为本地 Article 类型
      const cloudArticles: Article[] = result.list.map((a) => ({
        id: undefined, // 可能本地不存在
        cloudId: a.id,
        title: a.title,
        content: a.content,
        plainText: a.plain_text,
        wordCount: a.word_count,
        imageCount: a.image_count,
        totalImageSize: a.total_image_size,
        status: a.status,
        coverUrl: a.cover_url || undefined,
        summary: a.summary || undefined,
        wechatMediaId: a.wechat_media_id || undefined,
        wechatPublishUrl: a.wechat_publish_url || undefined,
        syncStatus: a.sync_status || 'synced',
        createdAt: new Date(a.created_at),
        updatedAt: new Date(a.updated_at),
        publishedAt: a.published_at ? new Date(a.published_at) : undefined,
        tags: a.tags || [],
      }))

      // 合并：云端文章更新本地缓存
      for (const cloud of cloudArticles) {
        const existing = localArticles.find((a) => a.cloudId === cloud.cloudId)
        if (existing) {
          // 云端版本更新 → 同步到本地
          await db.updateArticle(existing.id!, {
            title: cloud.title,
            content: cloud.content,
            plainText: cloud.plainText,
            wordCount: cloud.wordCount,
            imageCount: cloud.imageCount,
            totalImageSize: cloud.totalImageSize,
            status: cloud.status,
            syncStatus: 'synced',
            updatedAt: cloud.updatedAt,
            tags: cloud.tags,
          })
        } else {
          // 新云端文章 → 插入本地
          await db.createArticle(cloud)
        }
      }

      // 重新加载本地（已合并）
      articles.value = await db.getAllArticles(activeStatus.value)
    } catch {
      // 云端拉取失败，保留本地数据
    } finally {
      isSyncing.value = false
    }
  }
}

async function openArticle(id: number) {
  await store.loadArticle(id)
}

async function newArticle() {
  await store.createNewArticle()
  await loadArticles()
}

function formatDate(date: Date | string) {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

/** 同步状态图标 */
function syncIcon(article: Article): string {
  if (article.syncStatus === 'synced') return '☁️'
  if (article.syncStatus === 'syncing') return '⏳'
  if (article.syncStatus === 'failed') return '⚠️'
  return ''
}

onMounted(loadArticles)
</script>

<template>
  <div class="article-panel">
    <div class="article-header">
      <span class="header-title">文章管理</span>
      <button class="new-btn" @click="newArticle">+ 新建</button>
    </div>

    <div class="status-tabs">
      <button
        class="status-tab"
        :class="{ active: activeStatus === 'local' }"
        @click="activeStatus = 'local'; loadArticles()"
      >
        本地
      </button>
      <button
        class="status-tab"
        :class="{ active: activeStatus === 'draft' }"
        @click="activeStatus = 'draft'; loadArticles()"
      >
        草稿箱
      </button>
      <button
        class="status-tab"
        :class="{ active: activeStatus === 'published' }"
        @click="activeStatus = 'published'; loadArticles()"
      >
        已发布
      </button>
    </div>

    <div class="search-box">
      <input
        v-model="searchKeyword"
        type="text"
        class="search-input"
        placeholder="搜索文章..."
      />
      <span v-if="isSyncing" class="syncing-indicator">同步中...</span>
    </div>

    <div class="article-list">
      <div
        v-for="article in filteredArticles"
        :key="article.id"
        class="article-card"
        :class="{ active: store.currentArticleId === article.id }"
        @click="openArticle(article.id!)"
      >
        <div class="card-title">
          <span class="sync-icon" :title="article.syncStatus">{{ syncIcon(article) }}</span>
          {{ article.title || '未命名文章' }}
        </div>
        <div class="card-meta">
          <span class="card-time">{{ formatDate(article.updatedAt) }}</span>
          <span class="card-words">{{ article.wordCount }} 字</span>
          <span v-if="article.syncStatus === 'failed'" class="sync-failed">同步失败</span>
        </div>
      </div>

      <div v-if="filteredArticles.length === 0" class="empty-state">
        <p>暂无文章</p>
        <button class="empty-new-btn" @click="newArticle">创建第一篇文章</button>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.article-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.article-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;

  .header-title {
    font-size: 15px;
    font-weight: 600;
    color: #333;
  }

  .new-btn {
    padding: 4px 12px;
    border: 1px solid #07c160;
    border-radius: 4px;
    background: #fff;
    color: #07c160;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;

    &:hover {
      background: #07c160;
      color: #fff;
    }
  }
}

.status-tabs {
  display: flex;
  padding: 8px 12px;
  gap: 4px;
  border-bottom: 1px solid #e8e8e8;
}

.status-tab {
  flex: 1;
  padding: 6px 0;
  border: none;
  background: transparent;
  border-radius: 4px;
  font-size: 12px;
  color: #888;
  cursor: pointer;
  transition: all 0.15s;

  &.active {
    background: #e6f7ef;
    color: #07c160;
    font-weight: 500;
  }

  &:hover:not(.active) {
    background: #f5f5f5;
  }
}

.search-box {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  flex: 1;
  height: 30px;
  padding: 0 10px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  font-size: 12px;
  background: #f9f9f9;

  &:focus {
    outline: none;
    border-color: #07c160;
    background: #fff;
  }
}

.syncing-indicator {
  font-size: 11px;
  color: #07c160;
  white-space: nowrap;
  animation: pulse 1.5s ease infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.article-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.article-card {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 4px;

  &:hover {
    background: #f5f5f5;
  }

  &.active {
    background: #e6f7ef;
  }

  .card-title {
    font-size: 13px;
    font-weight: 500;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 4px;
  }

  .card-meta {
    display: flex;
    gap: 12px;
    font-size: 11px;
    color: #aaa;
  }
}

.sync-icon {
  margin-right: 4px;
  font-size: 11px;
}

.sync-failed {
  color: #e53e3e;
  font-weight: 500;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 16px;
  color: #ccc;

  p {
    margin: 0 0 12px;
    font-size: 14px;
  }

  .empty-new-btn {
    padding: 6px 16px;
    border: 1px dashed #ccc;
    border-radius: 6px;
    background: transparent;
    color: #aaa;
    font-size: 12px;
    cursor: pointer;

    &:hover {
      border-color: #07c160;
      color: #07c160;
    }
  }
}
</style>
