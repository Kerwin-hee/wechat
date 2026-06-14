<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import type { Editor } from '@tiptap/vue-3'

const props = defineProps<{
  editor: Editor
}>()

const visible = ref(false)
const position = reactive({ top: 0, left: 0 })
const showTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const hideTimer = ref<ReturnType<typeof setTimeout> | null>(null)

// 改写面板
const showRewritePanel = ref(false)
const rewriteStyles = [
  { key: 'formal', label: '更正式', desc: '适合商务/新闻稿' },
  { key: 'casual', label: '更活泼', desc: '适合生活方式/娱乐' },
  { key: 'concise', label: '更简洁', desc: '精简冗余表达' },
  { key: 'passionate', label: '更有感染力', desc: '增强情感表达' },
  { key: 'professional', label: '更专业', desc: '增加行业术语和数据' },
]

function updatePosition() {
  const { from, to } = props.editor.state.selection
  if (from === to) {
    hideToolbar()
    return
  }

  const coords = props.editor.view.coordsAtPos(from)
  const editorRect = props.editor.view.dom.getBoundingClientRect()

  position.top = coords.top - editorRect.top - 48
  position.left = coords.left - editorRect.left

  // 确保不超出编辑器左边
  if (position.left < 0) position.left = 8
}

function showToolbar() {
  clearTimeout(hideTimer.value!)
  showTimer.value = setTimeout(() => {
    const { from, to } = props.editor.state.selection
    if (from !== to) {
      const text = props.editor.state.doc.textBetween(from, to)
      if (text.length >= 1) {
        updatePosition()
        visible.value = true
        showRewritePanel.value = false
      }
    }
  }, 200)
}

function hideToolbar() {
  clearTimeout(showTimer.value!)
  hideTimer.value = setTimeout(() => {
    if (!showRewritePanel.value) {
      visible.value = false
    }
  }, 500)
}

function onSelectionUpdate() {
  const { from, to } = props.editor.state.selection
  if (from === to) {
    hideToolbar()
  } else {
    showToolbar()
  }
}

function handleBold() {
  props.editor.chain().focus().toggleBold().run()
}

function handleItalic() {
  props.editor.chain().focus().toggleItalic().run()
}

function handleLink() {
  const previousUrl = props.editor.getAttributes('link').href
  const url = window.prompt('输入链接地址', previousUrl)
  if (url === null) return
  if (url === '') {
    props.editor.chain().focus().extendMarkRange('link').unsetLink().run()
    return
  }
  props.editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  visible.value = false
}

function handleRewrite() {
  showRewritePanel.value = true
}

function handleRewriteStyle(_style: string) {
  // TODO: 对接 AI 改写后端
  alert(`AI 改写功能开发中，风格：${_style}。\n选中文字将发送至 AI 服务进行改写。`)
  showRewritePanel.value = false
  visible.value = false
}

onMounted(() => {
  props.editor.on('selectionUpdate', onSelectionUpdate)
  props.editor.on('blur', hideToolbar)
})

onUnmounted(() => {
  props.editor.off('selectionUpdate', onSelectionUpdate)
  props.editor.off('blur', hideToolbar)
})
</script>

<template>
  <Transition name="bubble">
    <div
      v-if="visible"
      class="bubble-toolbar"
      :style="{ top: position.top + 'px', left: position.left + 'px' }"
      @mousedown.prevent
    >
      <template v-if="!showRewritePanel">
        <button
          class="bubble-btn"
          :class="{ active: editor.isActive('bold') }"
          @click="handleBold"
          title="加粗"
        >
          <strong>B</strong>
        </button>
        <button
          class="bubble-btn"
          :class="{ active: editor.isActive('italic') }"
          @click="handleItalic"
          title="斜体"
        >
          <em>I</em>
        </button>
        <button
          class="bubble-btn"
          :class="{ active: editor.isActive('link') }"
          @click="handleLink"
          title="链接"
        >
          🔗
        </button>
        <div class="bubble-divider" />
        <button class="bubble-btn ai-btn" @click="handleRewrite" title="AI 改写">
          ✨ 改写
        </button>
      </template>

      <template v-else>
        <div class="rewrite-panel">
          <div class="rewrite-header">
            <span>选择改写风格</span>
            <button class="rewrite-close" @click="showRewritePanel = false">✕</button>
          </div>
          <div class="rewrite-styles">
            <button
              v-for="s in rewriteStyles"
              :key="s.key"
              class="rewrite-style-btn"
              @click="handleRewriteStyle(s.key)"
            >
              <span class="style-label">{{ s.label }}</span>
              <span class="style-desc">{{ s.desc }}</span>
            </button>
          </div>
        </div>
      </template>
    </div>
  </Transition>
</template>

<style lang="scss" scoped>
.bubble-toolbar {
  position: absolute;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 6px;
  background: #333;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  transform: translateX(0);
}

.bubble-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #fff;
  transition: all 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.15);
  }

  &.active {
    background: rgba(7, 193, 96, 0.3);
    color: #07c160;
  }
}

.ai-btn {
  width: auto;
  padding: 0 8px;
  gap: 4px;
  font-size: 12px;
  color: #7dffab;
  font-weight: 500;

  &:hover {
    background: rgba(7, 193, 96, 0.2);
  }
}

.bubble-divider {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.2);
  margin: 0 2px;
}

.rewrite-panel {
  min-width: 240px;
}

.rewrite-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px 8px;
  color: #ccc;
  font-size: 12px;
}

.rewrite-close {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;

  &:hover {
    color: #fff;
  }
}

.rewrite-styles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rewrite-style-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .style-label {
    font-size: 13px;
    color: #fff;
    font-weight: 500;
    white-space: nowrap;
  }

  .style-desc {
    font-size: 11px;
    color: #999;
  }
}

// 动画
.bubble-enter-active {
  transition: all 0.2s ease-out;
}

.bubble-leave-active {
  transition: all 0.15s ease-in;
}

.bubble-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.bubble-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
