<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEditorStore } from '../../stores/editor'
import { checkWechatCompat, getCompatSummary, type CompatIssue } from '../../utils/wechatCompat'

const store = useEditorStore()
const emit = defineEmits<{
  close: []
}>()

const isChecking = ref(false)
const issues = ref<CompatIssue[]>([])
const hasChecked = ref(false)

const summary = computed(() => getCompatSummary(issues.value))

const typeLabels = {
  error: '错误',
  warning: '警告',
  info: '提示',
} as const

const typeColors = {
  error: '#e53e3e',
  warning: '#faad14',
  info: '#1890ff',
} as const

function startCheck() {
  isChecking.value = true

  // 模拟检测过程（实际应该是毫秒级）
  setTimeout(() => {
    const html = store.editorContent
    issues.value = checkWechatCompat(html)
    isChecking.value = false
    hasChecked.value = true
  }, 500)
}

function locateIssue(_issue: CompatIssue) {
  // 定位到问题位置（MVP 阶段通过滚动到编辑器内容区提示）
  emit('close')
}
</script>

<template>
  <div class="compat-panel">
    <div class="compat-header">
      <span class="header-title">格式兼容检测</span>
      <button class="close-btn" @click="emit('close')">✕</button>
    </div>

    <div class="compat-body">
      <!-- 检测按钮 -->
      <div v-if="!hasChecked" class="check-prompt">
        <div class="prompt-icon">🔍</div>
        <p class="prompt-title">检测文章格式兼容性</p>
        <p class="prompt-desc">扫描编辑器内容，检测可能导致微信公众号显示异常的格式问题</p>
        <button class="check-btn" @click="startCheck" :disabled="isChecking">
          {{ isChecking ? '检测中...' : '开始检测' }}
        </button>
      </div>

      <!-- 检测结果 -->
      <div v-else>
        <!-- 摘要 -->
        <div class="compat-summary">
          <div class="summary-card" :class="{ clean: summary.isClean }">
            <span v-if="summary.isClean" class="summary-icon">✅</span>
            <span v-else class="summary-icon">⚠️</span>
            <span class="summary-text">
              {{ summary.isClean ? '未检测到兼容问题' : `检测到 ${issues.length} 个问题` }}
            </span>
          </div>
          <div v-if="!summary.isClean" class="summary-stats">
            <span class="stat" :style="{ color: typeColors.error }">
              🔴 {{ summary.errors }} 错误
            </span>
            <span class="stat" :style="{ color: typeColors.warning }">
              🟡 {{ summary.warnings }} 警告
            </span>
            <span class="stat" :style="{ color: typeColors.info }">
              🔵 {{ summary.infos }} 提示
            </span>
          </div>
        </div>

        <!-- 问题列表 -->
        <div v-if="issues.length > 0" class="issue-list">
          <div
            v-for="issue in issues"
            :key="issue.id"
            class="issue-item"
            :class="issue.type"
            @click="locateIssue(issue)"
          >
            <div class="issue-header">
              <span class="issue-badge" :style="{ background: typeColors[issue.type] }">
                {{ typeLabels[issue.type] }}
              </span>
              <span class="issue-title">{{ issue.title }}</span>
            </div>
            <div class="issue-desc">{{ issue.description }}</div>
            <div class="issue-suggestion">
              💡 {{ issue.suggestion }}
            </div>
          </div>
        </div>

        <div v-else class="clean-state">
          <div class="clean-icon">🎉</div>
          <p>你的文章格式完全兼容微信公众号！</p>
        </div>

        <button class="recheck-btn" @click="startCheck" :disabled="isChecking">
          {{ isChecking ? '检测中...' : '重新检测' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.compat-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
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

.compat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e8e8e8;

  .header-title { font-size: 16px; font-weight: 600; color: #333; }
  .close-btn {
    width: 28px; height: 28px;
    display: flex; align-items: center; justify-content: center;
    border: none; background: transparent; border-radius: 4px;
    cursor: pointer; font-size: 16px; color: #999;
    &:hover { background: #f0f0f0; color: #333; }
  }
}

.compat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.check-prompt {
  text-align: center;
  padding: 40px 16px;

  .prompt-icon { font-size: 48px; margin-bottom: 16px; }
  .prompt-title { font-size: 16px; font-weight: 600; color: #333; margin: 0 0 8px; }
  .prompt-desc { font-size: 13px; color: #888; line-height: 1.6; margin: 0 0 20px; }
}

.check-btn, .recheck-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  background: #07c160;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover { background: #06ad56; }
  &:disabled { background: #e0e0e0; color: #aaa; cursor: not-allowed; }
}

.compat-summary {
  margin-bottom: 16px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  background: #fff9e6;

  &.clean { background: #f0fff4; }

  .summary-icon { font-size: 20px; }
  .summary-text { font-size: 14px; font-weight: 500; color: #333; }
}

.summary-stats {
  display: flex;
  gap: 16px;
  padding: 8px 16px 0;

  .stat { font-size: 12px; font-weight: 500; }
}

.issue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.issue-item {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    border-color: #07c160;
    background: #fafffe;
  }

  &.error { border-left: 3px solid #e53e3e; }
  &.warning { border-left: 3px solid #faad14; }
  &.info { border-left: 3px solid #1890ff; }
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.issue-badge {
  padding: 1px 8px;
  border-radius: 4px;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
}

.issue-title {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.issue-desc {
  font-size: 12px;
  color: #888;
  margin-bottom: 6px;
  line-height: 1.5;
}

.issue-suggestion {
  font-size: 12px;
  color: #07c160;
  line-height: 1.5;
}

.clean-state {
  text-align: center;
  padding: 32px 16px;

  .clean-icon { font-size: 48px; margin-bottom: 12px; }
  p { font-size: 14px; color: #07c160; font-weight: 500; }
}

.recheck-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
