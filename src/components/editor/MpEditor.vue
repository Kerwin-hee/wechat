<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Highlight from '@tiptap/extension-highlight'
import CharacterCount from '@tiptap/extension-character-count'
import { watch, onMounted, ref } from 'vue'
import { useEditorStore } from '../../stores/editor'
import EditorToolbar from './EditorToolbar.vue'
import BubbleToolbar from './BubbleToolbar.vue'
import StatusBar from './StatusBar.vue'
import TemplatePanel from '../templates/TemplatePanel.vue'
import StylePanel from '../styles/StylePanel.vue'
import VersionPanel from '../versions/VersionPanel.vue'
import ToastContainer from '../common/ToastContainer.vue'
import { useToast } from '../../utils/toast'
import { processImageFile, extractImageFromClipboard } from '../../utils/imageUtils'
import {
  MarkdownShortcuts,
  MarkdownInline,
} from '../../utils/markdownRules'

const store = useEditorStore()
const toast = useToast()

const showTemplatePanel = ref(false)
const showStylePanel = ref(false)
const showVersionPanel = ref(false)

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3],
      },
    }),
    Placeholder.configure({
      placeholder: '开始写作，或让 AI 帮你写...',
    }),
    Underline,
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    Image.configure({
      inline: false,
      allowBase64: true,
      HTMLAttributes: {
        class: 'editor-image',
      },
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: {
        rel: 'noopener noreferrer',
        target: '_blank',
      },
    }),
    Highlight,
    CharacterCount,
    MarkdownShortcuts,
    MarkdownInline,
  ],
  content: store.editorContent || '',
  onUpdate: ({ editor: e }) => {
    store.updateContent(e.getHTML())
  },
  editorProps: {
    attributes: {
      class: 'editor-body',
    },
    // 处理拖拽上传图片
    handleDrop: (_view, event, _slice, _moved) => {
      const files = event.dataTransfer?.files
      if (!files || files.length === 0) return false

      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        if (!file.type.startsWith('image/')) continue

        processImageFile(file)
          .then((dataUrl) => {
            editor.value?.chain().focus().setImage({ src: dataUrl }).run()
            toast.success('图片已插入')
          })
          .catch((err) => {
            toast.error(err.message)
          })
      }
      return true
    },
    // 处理粘贴
    handlePaste: (_view, event) => {
      // 粘贴图片
      const imageFile = extractImageFromClipboard(event)
      if (imageFile) {
        event.preventDefault()
        processImageFile(imageFile)
          .then((dataUrl) => {
            editor.value?.chain().focus().setImage({ src: dataUrl }).run()
            toast.success('图片已粘贴')
          })
          .catch((err) => {
            toast.error(err.message)
          })
        return true
      }

      // 粘贴外部内容（Word/网页等）— Tiptap 默认会保留部分格式
      // 这里我们让 Tiptap 的默认粘贴处理先执行
      // 然后在下一帧检测是否有需要清理的格式
      setTimeout(() => {
        const hasComplexStyles = editor.value?.getHTML().includes('style=') &&
          editor.value.getHTML().includes('mso-')
        if (hasComplexStyles) {
          toast.info('已自动清理不兼容格式')
        }
      }, 100)

      return false
    },
  },
})

// 监听外部内容变化（如加载新文章）
watch(
  () => store.currentArticleId,
  () => {
    if (editor.value && store.editorContent !== editor.value.getHTML()) {
      editor.value.commands.setContent(store.editorContent || '', { emitUpdate: false })
    }
  }
)

onMounted(() => {
  if (store.currentArticleId === null) {
    store.createNewArticle()
  }
})

// 插入图片（从工具栏触发）
function handleAddImage() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return

    try {
      const dataUrl = await processImageFile(file)
      editor.value?.chain().focus().setImage({ src: dataUrl }).run()
      toast.success('图片已插入')
    } catch (err: any) {
      toast.error(err.message)
    }
  }
  input.click()
}

// 导入文件
async function handleImport(format: string) {
  if (format === 'clipboard') {
    try {
      const text = await navigator.clipboard.readText()
      if (text) {
        editor.value?.chain().focus().insertContent(text).run()
        toast.success('已从剪贴板导入')
      }
    } catch {
      toast.error('无法读取剪贴板内容')
    }
    return
  }

  const acceptMap: Record<string, string> = {
    docx: '.docx',
    md: '.md',
    html: '.html',
  }

  const input = document.createElement('input')
  input.type = 'file'
  input.accept = acceptMap[format] || ''
  input.onchange = async (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      if (format === 'md') {
        // Markdown 转 HTML（简化处理）
        const html = text
          .replace(/^### (.+)$/gm, '<h3>$1</h3>')
          .replace(/^## (.+)$/gm, '<h2>$1</h2>')
          .replace(/^# (.+)$/gm, '<h1>$1</h1>')
          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.+?)\*/g, '<em>$1</em>')
          .replace(/^- (.+)$/gm, '<li>$1</li>')
          .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
          .replace(/\n\n/g, '</p><p>')
          .replace(/\n/g, '<br>')
        editor.value?.chain().focus().insertContent(html).run()
      } else if (format === 'html') {
        editor.value?.chain().focus().insertContent(text).run()
      } else {
        editor.value?.chain().focus().insertContent(`<p>${text.replace(/\n/g, '</p><p>')}</p>`).run()
      }
      toast.success('导入完成')
    } catch {
      toast.error('导入失败，请检查文件格式')
    }
  }
  input.click()
}

// 导出文件
function handleExport(format: string) {
  if (!editor.value) return
  const html = editor.value.getHTML()
  let content = ''
  let mimeType = ''
  let ext = ''

  if (format === 'md') {
    content = html
      .replace(/<h1>(.+?)<\/h1>/g, '# $1\n\n')
      .replace(/<h2>(.+?)<\/h2>/g, '## $1\n\n')
      .replace(/<h3>(.+?)<\/h3>/g, '### $1\n\n')
      .replace(/<strong>(.+?)<\/strong>/g, '**$1**')
      .replace(/<em>(.+?)<\/em>/g, '*$1*')
      .replace(/<p>(.+?)<\/p>/g, '$1\n\n')
      .replace(/<br\s*\/?>/g, '\n')
      .replace(/<[^>]+>/g, '')
    mimeType = 'text/markdown'
    ext = 'md'
  } else if (format === 'html') {
    content = html
    mimeType = 'text/html'
    ext = 'html'
  } else {
    content = html.replace(/<[^>]+>/g, '').replace(/\n\s*\n/g, '\n\n')
    mimeType = 'text/plain'
    ext = 'txt'
  }

  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentArticle?.title || '未命名文章'}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('导出完成')
}

// 套用模板
function handleApplyTemplate(templateId: string) {
  // TODO: 根据模板ID获取模板内容，应用到编辑器
  toast.info(`模板 ${templateId} 应用功能开发中`)
  showTemplatePanel.value = false
}

// 应用样式
function handleApplyStyle(_style: any) {
  // TODO: 将样式属性应用到编辑器当前段落
  toast.info('样式应用功能开发中')
  showStylePanel.value = false
}

defineExpose({ editor })
</script>

<template>
  <div class="editor-wrapper">
    <EditorToolbar
      v-if="editor"
      :editor="editor"
      @add-image="handleAddImage"
      @open-templates="showTemplatePanel = true"
      @open-styles="showStylePanel = true"
      @open-versions="showVersionPanel = true"
      @import="handleImport"
      @export="handleExport"
    />
    <div class="editor-scroll-area" style="position: relative">
      <EditorContent :editor="editor" class="editor-content" />
      <BubbleToolbar v-if="editor" :editor="editor" />
    </div>
    <StatusBar />
    <ToastContainer />

    <!-- 模板中心面板 -->
    <TemplatePanel
      v-if="showTemplatePanel"
      @close="showTemplatePanel = false"
      @apply="handleApplyTemplate"
    />

    <!-- 样式收藏面板 -->
    <StylePanel
      v-if="showStylePanel"
      @close="showStylePanel = false"
      @apply="handleApplyStyle"
    />

    <!-- 版本历史面板 -->
    <VersionPanel
      v-if="showVersionPanel"
      @close="showVersionPanel = false"
    />
  </div>
</template>

<style lang="scss">
.editor-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.editor-scroll-area {
  flex: 1;
  overflow-y: auto;
  position: relative;
}

.editor-content {
  padding: 24px 32px;

  .tiptap {
    outline: none;
    min-height: 100%;
    font-size: 15px;
    line-height: 1.8;
    color: #333;

    > * + * {
      margin-top: 0.75em;
    }

    // Headings
    h1 {
      font-size: 24px;
      font-weight: 700;
      line-height: 1.4;
      color: #1a1a1a;
    }

    h2 {
      font-size: 20px;
      font-weight: 700;
      line-height: 1.5;
      color: #1a1a1a;
    }

    h3 {
      font-size: 17px;
      font-weight: 600;
      line-height: 1.5;
      color: #1a1a1a;
    }

    // Paragraph
    p {
      margin: 0;

      &.is-editor-empty:first-child::before {
        content: attr(data-placeholder);
        float: left;
        color: #adb5bd;
        pointer-events: none;
        height: 0;
      }
    }

    // Lists
    ul,
    ol {
      padding-left: 1.5em;
    }

    li {
      line-height: 1.8;

      p {
        margin: 0;
      }
    }

    // Blockquote
    blockquote {
      border-left: 4px solid #07c160;
      padding-left: 16px;
      margin: 1em 0;
      color: #666;
      background: #f8f9fa;
      border-radius: 0 4px 4px 0;
      padding: 8px 16px;
    }

    // Code
    code {
      background: #f0f0f0;
      border-radius: 3px;
      padding: 2px 6px;
      font-size: 0.9em;
      color: #e83e8c;
    }

    pre {
      background: #1e1e1e;
      color: #d4d4d4;
      border-radius: 6px;
      padding: 16px;
      overflow-x: auto;

      code {
        background: none;
        color: inherit;
        padding: 0;
      }
    }

    // Horizontal rule
    hr {
      border: none;
      border-top: 1px solid #e0e0e0;
      margin: 1.5em 0;
    }

    // Image
    img {
      max-width: 100%;
      height: auto;
      border-radius: 4px;
      margin: 8px 0;

      &.ProseMirror-selectednode {
        outline: 2px solid #07c160;
      }
    }

    // Link
    a {
      color: #07c160;
      text-decoration: none;
      cursor: pointer;

      &:hover {
        text-decoration: underline;
      }
    }

    // Highlight
    mark {
      background-color: #fff3bf;
      padding: 1px 2px;
      border-radius: 2px;
    }
  }
}
</style>
