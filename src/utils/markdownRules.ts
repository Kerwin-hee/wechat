import { Extension, InputRule } from '@tiptap/core'

/**
 * Markdown 快捷输入扩展
 * 注册自定义 InputRule，将 Markdown 语法实时转换为富文本
 */
export const MarkdownShortcuts = Extension.create({
  name: 'markdownShortcuts',

  addInputRules() {
    return [
      // H1: # 后跟空格
      new InputRule({
        find: /^(#{1})\s$/,
        handler: ({ state, range }) => {
          const { tr } = state
          const nodeType = state.schema.nodes.heading
          if (!nodeType) return
          tr.delete(range.from, range.to)
          tr.setBlockType(range.from, range.from, nodeType, { level: 1 })
        },
      }),
      // H2: ## 后跟空格
      new InputRule({
        find: /^(#{2})\s$/,
        handler: ({ state, range }) => {
          const { tr } = state
          const nodeType = state.schema.nodes.heading
          if (!nodeType) return
          tr.delete(range.from, range.to)
          tr.setBlockType(range.from, range.from, nodeType, { level: 2 })
        },
      }),
      // H3: ### 后跟空格
      new InputRule({
        find: /^(#{3})\s$/,
        handler: ({ state, range }) => {
          const { tr } = state
          const nodeType = state.schema.nodes.heading
          if (!nodeType) return
          tr.delete(range.from, range.to)
          tr.setBlockType(range.from, range.from, nodeType, { level: 3 })
        },
      }),
      // 无序列表: - 后跟空格
      new InputRule({
        find: /^-\s$/,
        handler: ({ state, range }) => {
          const { tr } = state
          const nodeType = state.schema.nodes.bulletList
          const listItemType = state.schema.nodes.listItem
          if (!nodeType || !listItemType) return
          tr.delete(range.from, range.to)
          const pos = range.from
          tr.insert(pos, nodeType.create(null, listItemType.create()))
        },
      }),
      // 有序列表: 1. 后跟空格
      new InputRule({
        find: /^\d+\.\s$/,
        handler: ({ state, range }) => {
          const { tr } = state
          const nodeType = state.schema.nodes.orderedList
          const listItemType = state.schema.nodes.listItem
          if (!nodeType || !listItemType) return
          tr.delete(range.from, range.to)
          const pos = range.from
          tr.insert(pos, nodeType.create(null, listItemType.create()))
        },
      }),
      // 引用: > 后跟空格
      new InputRule({
        find: /^>\s$/,
        handler: ({ state, range }) => {
          const { tr } = state
          const nodeType = state.schema.nodes.blockquote
          if (!nodeType) return
          tr.delete(range.from, range.to)
          tr.setBlockType(range.from, range.from, nodeType)
        },
      }),
      // 分割线: --- 独立行
      new InputRule({
        find: /^---$/,
        handler: ({ state, range }) => {
          const { tr } = state
          const nodeType = state.schema.nodes.horizontalRule
          if (!nodeType) return
          tr.delete(range.from, range.to)
          tr.replaceRangeWith(range.from, range.from, nodeType.create())
        },
      }),
    ]
  },
})

/**
 * Markdown 行内格式扩展
 * **text** → 加粗, *text* → 斜体, `text` → 代码
 */
export const MarkdownInline = Extension.create({
  name: 'markdownInline',

  addInputRules() {
    return [
      // **text** → 加粗
      new InputRule({
        find: /\*\*(.+)\*\*$/,
        handler: ({ state, range, match }) => {
          const { tr } = state
          const text = match[1]
          const boldMark = state.schema.marks.bold
          if (!boldMark) return
          const from = range.from
          const to = range.to
          tr.delete(from, to)
          tr.insertText(text, from)
          tr.addMark(from, from + text.length, boldMark.create())
        },
      }),
      // *text* → 斜体（行内使用）
      new InputRule({
        find: /(?<!\*)\*(?!\s)([^*]+)\*(?!\*)$/,
        handler: ({ state, range, match }) => {
          const { tr } = state
          const text = match[1]
          const italicMark = state.schema.marks.italic
          if (!italicMark) return
          const from = range.from
          const to = range.to
          tr.delete(from, to)
          tr.insertText(text, from)
          tr.addMark(from, from + text.length, italicMark.create())
        },
      }),
      // `text` → 行内代码
      new InputRule({
        find: /`([^`]+)`$/,
        handler: ({ state, range, match }) => {
          const { tr } = state
          const text = match[1]
          const codeMark = state.schema.marks.code
          if (!codeMark) return
          const from = range.from
          const to = range.to
          tr.delete(from, to)
          tr.insertText(text, from)
          tr.addMark(from, from + text.length, codeMark.create())
        },
      }),
    ]
  },
})
