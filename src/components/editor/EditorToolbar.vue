<script setup lang="ts">
import type { Editor } from '@tiptap/vue-3'

const props = defineProps<{
  editor: Editor
}>()

const emit = defineEmits<{
  addImage: []
  openTemplates: []
  openStyles: []
  openVersions: []
  import: [format: string]
  export: [format: string]
}>()

const headingValue = defineModel<string>('headingValue', { default: 'paragraph' })

const showImportMenu = defineModel<boolean>('showImportMenu', { default: false })
const showExportMenu = defineModel<boolean>('showExportMenu', { default: false })

function setHeading(level: number | null) {
  if (level === null) {
    props.editor.chain().focus().setParagraph().run()
    headingValue.value = 'paragraph'
  } else {
    props.editor.chain().focus().toggleHeading({ level: level as 1 | 2 | 3 }).run()
    headingValue.value = `h${level}`
  }
}

function setLink() {
  const previousUrl = props.editor.getAttributes('link').href
  const url = window.prompt('URL', previousUrl)
  if (url === null) return
  if (url === '') {
    props.editor.chain().focus().extendMarkRange('link').unsetLink().run()
    return
  }
  props.editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}
</script>

<template>
  <div class="toolbar">
    <div class="toolbar-group">
      <!-- Heading -->
      <select
        v-model="headingValue"
        class="toolbar-select"
        @change="setHeading(headingValue === 'paragraph' ? null : Number(headingValue.replace('h', '')))"
      >
        <option value="paragraph">正文</option>
        <option value="h1">标题 1</option>
        <option value="h2">标题 2</option>
        <option value="h3">标题 3</option>
      </select>
    </div>

    <div class="toolbar-divider" />

    <div class="toolbar-group">
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('bold') }"
        title="加粗 (Ctrl+B)"
        @click="editor.chain().focus().toggleBold().run()"
      >
        <strong>B</strong>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('italic') }"
        title="斜体 (Ctrl+I)"
        @click="editor.chain().focus().toggleItalic().run()"
      >
        <em>I</em>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('underline') }"
        title="下划线 (Ctrl+U)"
        @click="editor.chain().focus().toggleUnderline().run()"
      >
        <u>U</u>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('strike') }"
        title="删除线"
        @click="editor.chain().focus().toggleStrike().run()"
      >
        <s>S</s>
      </button>
    </div>

    <div class="toolbar-divider" />

    <div class="toolbar-group">
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('bulletList') }"
        title="无序列表"
        @click="editor.chain().focus().toggleBulletList().run()"
      >
        <span class="icon">☰</span>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('orderedList') }"
        title="有序列表"
        @click="editor.chain().focus().toggleOrderedList().run()"
      >
        <span class="icon">№</span>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('blockquote') }"
        title="引用"
        @click="editor.chain().focus().toggleBlockquote().run()"
      >
        <span class="icon">❝</span>
      </button>
      <button
        class="toolbar-btn"
        title="分割线"
        @click="editor.chain().focus().setHorizontalRule().run()"
      >
        <span class="icon">—</span>
      </button>
    </div>

    <div class="toolbar-divider" />

    <div class="toolbar-group">
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('link') }"
        title="链接"
        @click="setLink"
      >
        <span class="icon">🔗</span>
      </button>
      <button
        class="toolbar-btn"
        title="图片"
        @click="emit('addImage')"
      >
        <span class="icon">🖼</span>
      </button>
      <button
        class="toolbar-btn"
        :class="{ active: editor.isActive('highlight') }"
        title="高亮"
        @click="editor.chain().focus().toggleHighlight().run()"
      >
        <span class="icon">🖍</span>
      </button>
    </div>

    <div class="toolbar-divider" />

    <div class="toolbar-group">
      <button class="toolbar-btn" title="模板" @click="emit('openTemplates')">
        <span class="icon">📋</span>
      </button>
      <button class="toolbar-btn" title="我的样式" @click="emit('openStyles')">
        <span class="icon">🎨</span>
      </button>
    </div>

    <div class="toolbar-divider" />

    <div class="toolbar-group" style="position: relative">
      <button class="toolbar-btn" title="导入" @click="showImportMenu = !showImportMenu">
        <span class="icon">📥</span>
      </button>
      <div v-if="showImportMenu" class="dropdown-menu" @mouseleave="showImportMenu = false">
        <button class="dropdown-item" @click="emit('import', 'md'); showImportMenu = false">导入 Markdown (.md)</button>
        <button class="dropdown-item" @click="emit('import', 'docx'); showImportMenu = false">导入 Word (.docx)</button>
        <button class="dropdown-item" @click="emit('import', 'html'); showImportMenu = false">导入 HTML (.html)</button>
        <div class="dropdown-divider" />
        <button class="dropdown-item" @click="emit('import', 'clipboard'); showImportMenu = false">从剪贴板粘贴</button>
      </div>
    </div>

    <div class="toolbar-group" style="position: relative">
      <button class="toolbar-btn" title="导出" @click="showExportMenu = !showExportMenu">
        <span class="icon">📤</span>
      </button>
      <div v-if="showExportMenu" class="dropdown-menu" @mouseleave="showExportMenu = false">
        <button class="dropdown-item" @click="emit('export', 'md'); showExportMenu = false">导出 Markdown (.md)</button>
        <button class="dropdown-item" @click="emit('export', 'html'); showExportMenu = false">导出 HTML (.html)</button>
        <button class="dropdown-item" @click="emit('export', 'txt'); showExportMenu = false">导出纯文本 (.txt)</button>
      </div>
    </div>

    <button class="toolbar-btn" title="版本历史" @click="emit('openVersions')">
      <span class="icon">🕐</span>
    </button>

    <div class="toolbar-divider" />

    <div class="toolbar-group">
      <button
        class="toolbar-btn"
        title="撤销 (Ctrl+Z)"
        :disabled="!editor.can().undo()"
        @click="editor.chain().focus().undo().run()"
      >
        <span class="icon">↩</span>
      </button>
      <button
        class="toolbar-btn"
        title="重做 (Ctrl+Y)"
        :disabled="!editor.can().redo()"
        @click="editor.chain().focus().redo().run()"
      >
        <span class="icon">↪</span>
      </button>
      <button
        class="toolbar-btn"
        title="格式清除"
        @click="editor.chain().focus().clearNodes().unsetAllMarks().run()"
      >
        <span class="icon">🧹</span>
      </button>
    </div>

    <div class="toolbar-spacer" />

    <!-- AI 标题优化按钮 -->
    <div class="toolbar-group">
      <button class="toolbar-btn ai-btn" title="AI 标题优化">
        <span class="icon">✨</span> 标题优化
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.toolbar {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
  flex-wrap: wrap;
  gap: 2px;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: #ddd;
  margin: 0 6px;
}

.toolbar-spacer {
  flex: 1;
}

.toolbar-select {
  height: 28px;
  padding: 0 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: #07c160;
  }
}

.toolbar-btn {
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
  color: #555;
  transition: all 0.15s;

  &:hover {
    background: #e8e8e8;
    color: #333;
  }

  &.active {
    background: #e6f7ef;
    color: #07c160;
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .icon {
    font-size: 14px;
    line-height: 1;
  }
}

.ai-btn {
  width: auto;
  padding: 0 10px;
  gap: 4px;
  background: linear-gradient(135deg, #f0fff4, #e6f7ef);
  color: #07c160;
  font-weight: 500;

  &:hover {
    background: linear-gradient(135deg, #e6f7ef, #d4edda);
  }
}

// Dropdown menus
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  min-width: 180px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 50;
  padding: 4px;
  animation: dropdownFadeIn 0.15s ease;
}

@keyframes dropdownFadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: transparent;
  border-radius: 4px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  text-align: left;

  &:hover {
    background: #f5f5f5;
    color: #333;
  }
}

.dropdown-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 4px 0;
}
</style>
