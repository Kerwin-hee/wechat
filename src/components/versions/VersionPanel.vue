<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useEditorStore } from '../../stores/editor'
import * as db from '../../db'
import * as articlesApi from '../../api/articles'
import { isLoggedIn } from '../../api/client'
import type { ArticleVersion } from '../../types'

const store = useEditorStore()
const emit = defineEmits<{
  close: []
}>()

const versions = ref<ArticleVersion[]>([])
const selectedVersion = ref<ArticleVersion | null>(null)
const isRestoring = ref(false)
const isLoadingCloud = ref(false)

const isFreeUser = computed(() => true) // TODO: 从用户状态获取
const FREE_VERSION_LIMIT = 20

async function loadVersions() {
  if (!store.currentArticleId) return
  // 加载本地版本
  versions.value = await db.getVersions(store.currentArticleId)

  // 如果已登录且文章有 cloudId，同时拉取云端版本
  const article = store.currentArticle
  if (isLoggedIn() && article?.cloudId) {
    isLoadingCloud.value = true
    try {
      const result = await articlesApi.fetchVersions(article.cloudId, 1, 50)
      // 将云端版本映射并合并到本地列表
      const cloudVersions: ArticleVersion[] = result.list.map((v) => ({
        id: undefined, // 云端版本使用 cloudId 标识
        cloudId: v.id,
        articleId: store.currentArticleId!,
        versionNumber: v.version_number,
        title: v.title,
        content: v.content,
        wordCount: v.word_count,
        diffFromPrevious: v.diff_from_previous || undefined,
        createdAt: new Date(v.created_at),
      }))

      // 合并去重（按 versionNumber）
      const existingNumbers = new Set(versions.value.map((v) => v.versionNumber))
      for (const cv of cloudVersions) {
        if (!existingNumbers.has(cv.versionNumber)) {
          versions.value.push(cv)
        }
      }
      // 按版本号降序
      versions.value.sort((a, b) => b.versionNumber - a.versionNumber)
    } catch {
      // 云端拉取失败，保留本地版本
    } finally {
      isLoadingCloud.value = false
    }
  }
}

function selectVersion(version: ArticleVersion) {
  selectedVersion.value = version
}

async function restoreVersion() {
  if (!selectedVersion.value || !store.currentArticleId) return

  isRestoring.value = true
  try {
    // 先保存当前内容为新版本
    await store.saveArticle()

    const targetVersion = selectedVersion.value

    // 云端恢复（如果文章有 cloudId 且选中版本有 cloudId）
    const article = store.currentArticle
    if (isLoggedIn() && article?.cloudId && targetVersion.cloudId) {
      try {
        await articlesApi.restoreVersion(article.cloudId, targetVersion.cloudId)
      } catch {
        // 云端恢复失败，继续本地恢复
      }
    }

    // 本地恢复
    await db.updateArticle(store.currentArticleId, {
      content: targetVersion.content,
      title: targetVersion.title,
      wordCount: targetVersion.wordCount,
    })
    await store.loadArticle(store.currentArticleId)
    emit('close')
  } finally {
    isRestoring.value = false
  }
}

function formatTime(date: Date | string) {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

watch(() => store.currentArticleId, loadVersions)
onMounted(loadVersions)
</script>

<template>
  <div class="version-panel">
    <div class="version-header">
      <span class="header-title">版本历史</span>
      <div class="header-right">
        <span v-if="isLoadingCloud" class="cloud-loading">同步中...</span>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>
    </div>

    <div v-if="!isFreeUser" class="version-quota">
      {{ versions.length }} 个版本（专业版无限）
    </div>
    <div v-else class="version-quota free">
      {{ versions.length }} / {{ FREE_VERSION_LIMIT }} 个版本（免费版限制）
    </div>

    <div class="version-body">
      <!-- 版本列表 -->
      <div class="version-list">
        <div
          v-for="(v, index) in versions"
          :key="v.cloudId || v.id"
          class="version-item"
          :class="{
            active: (selectedVersion?.cloudId || selectedVersion?.id) === (v.cloudId || v.id),
            current: index === 0,
          }"
          @click="selectVersion(v)"
        >
          <div class="version-dot" :class="{ latest: index === 0 }" />
          <div class="version-content">
            <div class="version-title">
              {{ v.title || '无标题' }}
              <span v-if="v.cloudId" class="cloud-badge" title="已同步云端">☁️</span>
            </div>
            <div class="version-meta">
              <span>{{ formatTime(v.createdAt) }}</span>
              <span>{{ v.wordCount }} 字</span>
            </div>
          </div>
          <span v-if="index === 0" class="latest-badge">当前</span>
        </div>

        <div v-if="versions.length === 0" class="empty-state">
          <p>暂无版本历史</p>
          <p class="hint">每次保存或自动保存都会创建一个版本</p>
        </div>
      </div>

      <!-- 版本预览 -->
      <div class="version-preview">
        <div v-if="selectedVersion" class="preview-content">
          <div class="preview-header">
            <span>{{ selectedVersion.title || '无标题' }}</span>
            <span class="preview-time">{{ formatTime(selectedVersion.createdAt) }}</span>
          </div>
          <div class="preview-body" v-html="selectedVersion.content || '<p style=color:#ccc>空内容</p>'" />
        </div>
        <div v-else class="preview-empty">
          <p>选择左侧版本查看内容</p>
        </div>
      </div>
    </div>

    <div class="version-footer">
      <button
        class="restore-btn"
        :disabled="!selectedVersion || (selectedVersion?.cloudId || selectedVersion?.id) === (versions[0]?.cloudId || versions[0]?.id)"
        @click="restoreVersion"
      >
        {{ isRestoring ? '恢复中...' : '恢复到该版本' }}
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.version-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 600px;
  height: 100vh;
  background: #fff;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
  z-index: 100;
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.version-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e8e8e8;

  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: #333;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .cloud-loading {
    font-size: 11px;
    color: #07c160;
    animation: pulse 1.5s ease infinite;
  }

  .close-btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    color: #999;

    &:hover {
      background: #f0f0f0;
      color: #333;
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.version-quota {
  padding: 6px 16px;
  font-size: 12px;
  color: #888;
  background: #fafafa;

  &.free {
    color: #faad14;
  }
}

.version-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.version-list {
  width: 240px;
  min-width: 240px;
  border-right: 1px solid #e8e8e8;
  overflow-y: auto;
  padding: 8px;
}

.version-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;

  &:hover {
    background: #f5f5f5;
  }

  &.active {
    background: #e6f7ef;
  }
}

.version-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ddd;
  flex-shrink: 0;
  margin-top: 3px;

  &.latest {
    background: #07c160;
    box-shadow: 0 0 0 3px rgba(7, 193, 96, 0.2);
  }
}

.version-content {
  flex: 1;
  min-width: 0;

  .version-title {
    font-size: 13px;
    font-weight: 500;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .version-meta {
    display: flex;
    gap: 8px;
    font-size: 11px;
    color: #aaa;
    margin-top: 2px;
  }
}

.cloud-badge {
  margin-left: 4px;
  font-size: 10px;
}

.latest-badge {
  padding: 1px 6px;
  background: #e6f7ef;
  color: #07c160;
  font-size: 10px;
  border-radius: 4px;
  flex-shrink: 0;
}

.version-preview {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: #333;
  font-weight: 500;

  .preview-time {
    font-size: 12px;
    color: #aaa;
    font-weight: 400;
  }
}

.preview-body {
  font-size: 14px;
  line-height: 1.8;
  color: #555;

  :deep(img) {
    max-width: 100%;
    height: auto;
  }
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #ccc;
  font-size: 14px;
}

.version-footer {
  padding: 12px 16px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  gap: 8px;
}

.restore-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 6px;
  background: #07c160;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;

  &:hover:not(:disabled) {
    background: #06ad56;
  }

  &:disabled {
    background: #e0e0e0;
    color: #aaa;
    cursor: not-allowed;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: #ccc;

  p { margin: 0 0 4px; }
  .hint { font-size: 12px; color: #ddd; }
}
</style>
