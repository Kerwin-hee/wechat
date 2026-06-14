<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { UserStyle } from '../../types'
import * as db from '../../db'
import * as stylesApi from '../../api/styles'
import { isLoggedIn } from '../../api/client'
import { useToast } from '../../utils/toast'

const toast = useToast()

const styles = ref<UserStyle[]>([])
const isPro = ref(false) // TODO: 从用户状态获取
const FREE_STYLE_LIMIT = 3
const isSyncingCloud = ref(false)

const emit = defineEmits<{
  close: []
  apply: [style: UserStyle]
}>()

async function loadStyles() {
  styles.value = await db.getAllStyles()

  // 云端同步
  if (isLoggedIn()) {
    isSyncingCloud.value = true
    try {
      const cloudStyles = await stylesApi.fetchStyles()
      for (const cs of cloudStyles) {
        const existing = styles.value.find((s) => s.cloudId === cs.id)
        if (existing) {
          await db.updateStyle(existing.id!, {
            name: cs.name,
            styleProperties: cs.style_properties,
          })
        } else {
          await db.saveStyle({
            cloudId: cs.id,
            name: cs.name,
            styleProperties: cs.style_properties,
            createdAt: new Date(cs.created_at),
          })
        }
      }
      // 重新加载合并后的数据
      styles.value = await db.getAllStyles()
    } catch {
      // 云端拉取失败，保留本地
    } finally {
      isSyncingCloud.value = false
    }
  }
}

async function saveCurrentStyle() {
  if (!isPro.value && styles.value.length >= FREE_STYLE_LIMIT) {
    toast.warning('免费版最多保存 3 套样式，升级会员可无限保存')
    return
  }

  const name = prompt('为样式命名', `样式 ${new Date().toLocaleDateString('zh-CN')}`)
  if (!name) return

  // TODO: 从编辑器当前光标位置提取样式
  const styleProperties = {
    fontSize: '15px',
    lineHeight: '1.8',
    color: '#333333',
    alignment: 'left' as const,
  }

  // 本地保存
  const localId = await db.saveStyle({
    name,
    styleProperties,
    createdAt: new Date(),
  })

  // 云端同步
  if (isLoggedIn()) {
    try {
      const result = await stylesApi.createStyle({
        name,
        style_properties: styleProperties,
      })
      await db.updateStyle(localId, { cloudId: result.id })
    } catch {
      // 云端保存失败，样式仅存本地
    }
  }

  await loadStyles()
  toast.success('样式已保存')
}

async function deleteStyle(id: number) {
  if (!confirm('确定删除此样式？')) return

  // 尝试云端删除
  const style = styles.value.find((s) => s.id === id)
  if (isLoggedIn() && style?.cloudId) {
    try {
      await stylesApi.deleteStyle(style.cloudId)
    } catch {
      // 忽略云端删除失败
    }
  }

  await db.deleteStyle(id)
  await loadStyles()
  toast.info('样式已删除')
}

async function renameStyle(id: number, currentName: string) {
  const newName = prompt('重命名样式', currentName)
  if (!newName || newName === currentName) return

  await db.updateStyle(id, { name: newName })

  // 云端同步重命名
  const style = styles.value.find((s) => s.id === id)
  if (isLoggedIn() && style?.cloudId) {
    try {
      await stylesApi.updateStyle(style.cloudId, { name: newName })
    } catch {
      // 忽略云端更新失败
    }
  }

  await loadStyles()
}

function applyStyle(style: UserStyle) {
  emit('apply', style)
  toast.success(`已应用样式「${style.name}」`)
}

onMounted(loadStyles)
</script>

<template>
  <div class="style-panel">
    <div class="style-header">
      <span class="header-title">我的样式</span>
      <div class="header-right">
        <span v-if="isSyncingCloud" class="syncing-text">同步中...</span>
        <button class="add-btn" @click="saveCurrentStyle">+ 收藏当前样式</button>
      </div>
    </div>

    <div class="style-quota">
      <span>{{ styles.length }} / {{ isPro ? '∞' : FREE_STYLE_LIMIT }}</span>
      <span class="quota-label">{{ isPro ? '专业版' : '免费版' }}</span>
    </div>

    <div class="style-list">
      <div
        v-for="style in styles"
        :key="style.id"
        class="style-card"
        @click="applyStyle(style)"
      >
        <div class="style-preview">
          <span :style="{
            fontSize: style.styleProperties.fontSize || undefined,
            lineHeight: style.styleProperties.lineHeight || undefined,
            color: style.styleProperties.color || undefined,
            textAlign: style.styleProperties.alignment as any || undefined,
            fontWeight: style.styleProperties.fontWeight || undefined,
            fontStyle: style.styleProperties.fontStyle || undefined,
          }">Aa</span>
        </div>
        <div class="style-info">
          <div class="style-name">
            {{ style.name }}
            <span v-if="style.cloudId" class="cloud-badge" title="已同步云端">☁️</span>
          </div>
          <div class="style-meta">
            {{ style.styleProperties.fontSize }} · {{ style.styleProperties.lineHeight }}
          </div>
        </div>
        <div class="style-actions" @click.stop>
          <button class="action-btn" @click="renameStyle(style.id!, style.name)" title="重命名">✎</button>
          <button class="action-btn delete" @click="deleteStyle(style.id!)" title="删除">✕</button>
        </div>
      </div>

      <div v-if="styles.length === 0" class="empty-state">
        <p>暂无收藏样式</p>
        <p class="hint">在编辑器中排版好文字后，选中段落点击「收藏样式」即可保存</p>
      </div>
    </div>

    <button class="close-btn" @click="emit('close')">关闭</button>
  </div>
</template>

<style lang="scss" scoped>
.style-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 360px;
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

.style-header {
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
    gap: 8px;
  }

  .syncing-text {
    font-size: 11px;
    color: #07c160;
    animation: pulse 1.5s ease infinite;
  }

  .add-btn {
    padding: 4px 12px;
    border: 1px solid #07c160;
    border-radius: 4px;
    background: #fff;
    color: #07c160;
    font-size: 12px;
    cursor: pointer;

    &:hover {
      background: #07c160;
      color: #fff;
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.style-quota {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  font-size: 12px;
  color: #888;
  background: #fafafa;

  .quota-label {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    background: #f0f0f0;
  }
}

.style-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.style-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.15s;

  &:hover {
    border-color: #07c160;
    background: #fafffe;
  }
}

.style-preview {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 20px;
  flex-shrink: 0;
}

.style-info {
  flex: 1;
  min-width: 0;

  .style-name {
    font-size: 13px;
    font-weight: 500;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .style-meta {
    font-size: 11px;
    color: #aaa;
  }
}

.cloud-badge {
  margin-left: 4px;
  font-size: 10px;
}

.style-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;

  .style-card:hover & {
    opacity: 1;
  }
}

.action-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #888;

  &:hover {
    background: #e0e0e0;
    color: #333;
  }

  &.delete:hover {
    background: #fee;
    color: #e53e3e;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: #ccc;

  p { margin: 0 0 4px; }
  .hint { font-size: 12px; color: #ddd; }
}

.close-btn {
  margin: 12px 16px;
  padding: 8px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: #666;
  cursor: pointer;

  &:hover {
    background: #f5f5f5;
  }
}
</style>
