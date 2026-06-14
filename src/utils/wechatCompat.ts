/**
 * 微信格式兼容检测工具
 * - 检测可能导致公众号显示异常的格式问题
 * - 微信 CSS 规则库参考
 */

export interface CompatIssue {
  id: string
  type: 'error' | 'warning' | 'info'
  title: string
  description: string
  suggestion: string
  position?: number // 在内容中的字符位置
}

/**
 * 微信支持的 CSS 属性白名单
 */
const WECHAT_SUPPORTED_CSS = new Set([
  'color', 'background-color', 'font-size', 'font-weight',
  'font-style', 'text-align', 'text-indent', 'line-height',
  'letter-spacing', 'word-spacing', 'white-space', 'vertical-align',
  'border', 'border-left', 'border-right', 'border-top', 'border-bottom',
  'border-radius', 'width', 'height', 'max-width', 'margin', 'padding',
  'display', 'visibility', 'opacity', 'box-shadow', 'text-shadow',
])

/**
 * 微信不支持的 HTML 标签
 */
const WECHAT_UNSUPPORTED_TAGS = new Set([
  'iframe', 'embed', 'object', 'video', 'audio',
  'canvas', 'svg', 'form', 'input', 'button', 'select',
])

/**
 * 微信支持的字体列表
 */
const WECHAT_SUPPORTED_FONTS = new Set([
  'system-ui', '-apple-system', 'blinkmacsystemfont',
  'pingfang sc', 'microsoft yahei', 'hiragino sans gb',
  'arial', 'helvetica', 'simsun', 'georgia',
  'times new roman', 'courier new',
])

/**
 * 执行兼容检测
 */
export function checkWechatCompat(html: string): CompatIssue[] {
  const issues: CompatIssue[] = []

  // 1. 检测空标题
  const h1Match = html.match(/<h1[^>]*>(.*?)<\/h1>/)
  if (!h1Match || !h1Match[1].replace(/<[^>]*>/g, '').trim()) {
    issues.push({
      id: 'no-h1',
      type: 'info',
      title: '文章无 H1 标题',
      description: '建议为文章添加一个 H1 主标题，有助于阅读体验和 SEO',
      suggestion: '在编辑器第一行输入标题，或使用工具栏的标题格式',
    })
  }

  // 2. 检测图片大小
  const imgTags = html.match(/<img[^>]*>/g) || []
  for (const img of imgTags) {
    const srcMatch = img.match(/src="data:image[^"]+"/)
    if (srcMatch) {
      // base64 图片估算大小
      const base64Part = srcMatch[0].split(',')[1] || ''
      const sizeInBytes = (base64Part.length * 3) / 4
      if (sizeInBytes > 5 * 1024 * 1024) {
        issues.push({
          id: 'large-image',
          type: 'warning',
          title: '图片过大（>5MB）',
          description: '文章中存在超过 5MB 的图片，可能导致加载缓慢',
          suggestion: '建议压缩图片至 5MB 以内，使用 JPEG 格式',
        })
        break
      }
    }
  }

  // 3. 检测不支持的标签
  for (const tag of WECHAT_UNSUPPORTED_TAGS) {
    if (html.includes(`<${tag}`)) {
      issues.push({
        id: `unsupported-tag-${tag}`,
        type: 'error',
        title: `不支持的标签：<${tag}>`,
        description: `微信公众号不支持 <${tag}> 标签，该内容将无法显示`,
        suggestion: '请移除该内容，或替换为图片',
      })
    }
  }

  // 4. 检测不支持的字体
  const fontMatches = html.match(/font-family:\s*([^;"]+)/gi) || []
  for (const match of fontMatches) {
    const fonts = match.replace(/font-family:\s*/i, '').split(',').map((f) => f.trim().replace(/['"]/g, '').toLowerCase())
    for (const font of fonts) {
      if (!WECHAT_SUPPORTED_FONTS.has(font) && !font.startsWith('var(')) {
        issues.push({
          id: 'unsupported-font',
          type: 'error',
          title: `不支持的字体：${font}`,
          description: `微信公众号可能不支持 "${font}" 字体，建议使用系统默认字体`,
          suggestion: '替换为 PingFang SC、Microsoft YaHei 或系统默认字体',
        })
        break
      }
    }
    break // 只报告一次
  }

  // 5. 检测过长链接
  const urlMatches = html.match(/https?:\/\/[^\s<>"]{200,}/g) || []
  if (urlMatches.length > 0) {
    issues.push({
      id: 'long-url',
      type: 'warning',
      title: '存在过长链接',
      description: '文章中存在超过 200 字符的链接，可能影响排版',
      suggestion: '建议使用短链接服务缩短 URL',
    })
  }

  // 6. 检测超字数
  const plainText = html.replace(/<[^>]*>/g, '').trim()
  if (plainText.length > 20000) {
    issues.push({
      id: 'too-long',
      type: 'info',
      title: '文章字数过多（>20000字）',
      description: '文章字数超过 20000 字，可能影响阅读体验',
      suggestion: '考虑拆分为多篇文章发布',
    })
  }

  // 7. 检测不兼容的内联样式
  const styleMatches = html.match(/style="([^"]*)"/g) || []
  const unsupportedStyles: string[] = []
  for (const match of styleMatches) {
    const styles = match.replace(/style="|"/g, '').split(';')
    for (const s of styles) {
      const prop = s.split(':')[0]?.trim()
      if (prop && !WECHAT_SUPPORTED_CSS.has(prop)) {
        if (!unsupportedStyles.includes(prop)) {
          unsupportedStyles.push(prop)
        }
      }
    }
  }
  if (unsupportedStyles.length > 0) {
    issues.push({
      id: 'unsupported-css',
      type: 'error',
      title: '不兼容的 CSS 属性',
      description: `检测到微信不支持的 CSS 属性：${unsupportedStyles.join(', ')}`,
      suggestion: '这些样式在微信中可能不生效，建议使用编辑器内置的格式工具',
    })
  }

  return issues
}

/**
 * 获取兼容检测摘要
 */
export function getCompatSummary(issues: CompatIssue[]): {
  errors: number
  warnings: number
  infos: number
  isClean: boolean
} {
  const errors = issues.filter((i) => i.type === 'error').length
  const warnings = issues.filter((i) => i.type === 'warning').length
  const infos = issues.filter((i) => i.type === 'info').length

  return {
    errors,
    warnings,
    infos,
    isClean: errors === 0 && warnings === 0,
  }
}
