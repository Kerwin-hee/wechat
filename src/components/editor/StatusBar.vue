<script setup lang="ts">
import { useEditorStore } from '../../stores/editor'

const store = useEditorStore()

function formatTime(date: Date | null) {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <div class="status-bar">
    <div class="status-left">
      <span class="status-item">{{ store.wordCount }} 字</span>
      <span class="status-divider">|</span>
      <span class="status-item">{{ store.imageCount }} 图片</span>
    </div>
    <div class="status-right">
      <span v-if="store.isSaving" class="status-item saving">
        <span class="spinner" /> 保存中...
      </span>
      <span v-else-if="store.lastSavedAt" class="status-item saved">
        已保存 {{ formatTime(store.lastSavedAt) }}
      </span>
      <span v-else-if="store.isDirty" class="status-item unsaved">
        未保存
      </span>
      <span v-else class="status-item">就绪</span>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 16px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
  font-size: 12px;
  color: #aaa;
  height: 28px;
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-divider {
  color: #ddd;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.saving {
  color: #07c160;
}

.saved {
  color: #999;
}

.unsaved {
  color: #e53e3e;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #e6f7ef;
  border-top-color: #07c160;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
