<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useEditorStore } from '../../stores/editor'
import { useToast } from '../../utils/toast'
import {
  aiGenerate,
  buildGenerateRequest,
  getRemainingQuota,
  clearQuotaCache,
  type AIFunctionType,
  type AIStyle,
  type TargetAudience,
  type WordCount,
  type StreamCallbacks,
  type AIDoneEvent,
} from '../../services/aiService'

const store = useEditorStore()
const toast = useToast()

// ===== AI 功能 Tabs（type 对齐联调文档枚举） =====
const aiTabs = [
  { key: 'full' as const, label: '全文生成', icon: '📝', type: 'full_article' as AIFunctionType },
  { key: 'continue' as const, label: '续写', icon: '✏️', type: 'continue_writing' as AIFunctionType },
  { key: 'rewrite' as const, label: '改写', icon: '🔄', type: 'rewrite' as AIFunctionType },
  { key: 'outline' as const, label: '大纲', icon: '📋', type: 'outline' as AIFunctionType },
  { key: 'title' as const, label: '标题优化', icon: '💡', type: 'title_optimize' as AIFunctionType },
]

// ===== 生成状态 =====
const isGenerating = ref(false)
const generatedContent = ref('')
const abortController = ref<AbortController | null>(null)
const remainingQuota = ref<number | null>(null)

// ===== 全文生成 Tab =====
const fullArticleForm = ref({
  topic: '',
  targetAudience: '大众读者' as string,
  writingStyle: '专业严谨' as string,
  wordCountRange: '1000-2000字' as string,
  referenceMaterials: '',
})

// ===== 大纲生成 Tab =====
const outlineForm = ref({
  topic: '',
  level: 3,
})

// ===== 当前类型 =====
const currentAIType = computed<AIFunctionType | null>(() => {
  const tab = aiTabs.find((t) => t.key === store.aiSubTab)
  return tab?.type || null
})

// ===== 加载额度 =====
async function loadQuota() {
  const type = currentAIType.value
  if (!type) return
  remainingQuota.value = await getRemainingQuota(type)
}

onMounted(loadQuota)

// ===== 生成函数 =====
function startGenerate(context: string, extraOptions?: Record<string, any>) {
  const type = currentAIType.value
  if (!type) return

  const request = buildGenerateRequest(type, context, extraOptions)

  isGenerating.value = true
  generatedContent.value = ''
  abortController.value = new AbortController()

  const callbacks: StreamCallbacks = {
    onStarted: (data) => {
      // 更新额度
      const typeRemaining = data.quota_remaining[type]
      if (typeRemaining !== undefined) {
        remainingQuota.value = typeRemaining
      }
    },
    onToken: (token) => {
      generatedContent.value += token
    },
    onDone: (_data: AIDoneEvent) => {
      isGenerating.value = false
      clearQuotaCache()
      loadQuota()
      toast.success('AI 生成完成')
    },
    onError: (error) => {
      isGenerating.value = false
      toast.error(`生成失败：${error}`)
    },
  }

  aiGenerate(request, callbacks, abortController.value.signal)
}

function cancelGenerate() {
  abortController.value?.abort()
  isGenerating.value = false
}

// ===== 风格映射（UI 中文 → 后端枚举） =====
const styleMap: Record<string, AIStyle> = {
  '专业严谨': 'formal',
  '轻松活泼': 'casual',
  '深度长文': 'professional',
  '短小精悍': 'concise',
}
const audienceMap: Record<string, TargetAudience> = {
  '大众读者': 'general',
  '行业从业者': 'professional',
  '技术爱好者': 'tech',
  '学生群体': 'student',
}
const wordCountMap: Record<string, WordCount> = {
  '500-1000字': '500-1000',
  '1000-2000字': '1000-2000',
  '2000-3000字': '2000-3000',
}

function handleGenerateFull() {
  if (!fullArticleForm.value.topic.trim()) {
    toast.warning('请输入文章主题')
    return
  }
  startGenerate(fullArticleForm.value.topic, {
    style: styleMap[fullArticleForm.value.writingStyle] || 'casual',
    target_audience: audienceMap[fullArticleForm.value.targetAudience] || 'general',
    word_count: wordCountMap[fullArticleForm.value.wordCountRange] || '1000-2000',
    reference_materials: fullArticleForm.value.referenceMaterials || undefined,
  })
}

function handleGenerateOutline() {
  if (!outlineForm.value.topic.trim()) {
    toast.warning('请输入大纲主题')
    return
  }
  startGenerate(outlineForm.value.topic, {
    outline_level: outlineForm.value.level,
  })
}

function insertContent() {
  if (!generatedContent.value) return
  const currentContent = store.editorContent
  store.updateContent(currentContent + generatedContent.value)
  toast.success('已插入编辑器')
  generatedContent.value = ''
}

function regenerate() {
  if (store.aiSubTab === 'full') handleGenerateFull()
  else if (store.aiSubTab === 'outline') handleGenerateOutline()
}

// ===== 续写 =====
function handleContinue() {
  const context = store.editorContent.slice(-500)
  if (!context.trim()) {
    toast.warning('请先在编辑器中输入内容')
    return
  }
  startGenerate(context)
}

// ===== 改写 =====
function handleRewrite(style: string) {
  const selectedText = window.getSelection()?.toString() || ''
  if (!selectedText.trim()) {
    toast.warning('请先在编辑器中选中要改写的文字')
    return
  }
  startGenerate(selectedText, { style: style as AIStyle })
}

// ===== 标题优化 =====
function handleTitleOptimize() {
  const h1Match = store.editorContent.match(/<h1[^>]*>(.*?)<\/h1>/)
  const title = h1Match ? h1Match[1].replace(/<[^>]*>/g, '') : ''
  if (!title.trim()) {
    toast.warning('请先在编辑器中添加标题（H1）')
    return
  }
  startGenerate(title)
}

onUnmounted(() => {
  abortController.value?.abort()
})
</script>

<template>
  <div class="ai-panel">
    <div class="ai-header">
      <span class="ai-icon">🧠</span>
      <span class="ai-title">AI 创作</span>
    </div>

    <div class="ai-tabs">
      <button
        v-for="tab in aiTabs"
        :key="tab.key"
        class="ai-tab"
        :class="{ active: store.aiSubTab === tab.key }"
        @click="store.aiSubTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <div class="ai-content">
      <!-- ===== 结果展示区（生成中或已有结果时显示） ===== -->
      <div v-if="isGenerating || generatedContent" class="result-area">
        <div class="result-header">
          <span class="result-title">AI 生成结果</span>
          <div class="result-actions">
            <button v-if="isGenerating" class="result-btn cancel" @click="cancelGenerate">取消</button>
            <button v-else class="result-btn" @click="regenerate">重新生成</button>
            <button v-if="!isGenerating" class="result-btn primary" @click="insertContent">插入编辑器</button>
          </div>
        </div>
        <div class="result-content" v-html="generatedContent.replace(/\n/g, '<br>')" />
        <div v-if="isGenerating" class="result-loading">
          <span class="spinner" /> AI 正在创作中...
        </div>
      </div>

      <!-- ===== 全文生成表单 ===== -->
      <div v-else-if="store.aiSubTab === 'full'" class="ai-form">
        <div class="form-item">
          <label class="form-label">文章主题 <span class="required">*</span></label>
          <textarea
            v-model="fullArticleForm.topic"
            class="form-textarea"
            rows="3"
            placeholder="输入你想写的主题，比如：AI 如何改变内容创作"
          />
        </div>
        <div class="form-row">
          <div class="form-item">
            <label class="form-label">目标读者</label>
            <select v-model="fullArticleForm.targetAudience" class="form-select">
              <option>大众读者</option>
              <option>行业从业者</option>
              <option>技术爱好者</option>
              <option>学生群体</option>
            </select>
          </div>
          <div class="form-item">
            <label class="form-label">写作风格</label>
            <select v-model="fullArticleForm.writingStyle" class="form-select">
              <option>专业严谨</option>
              <option>轻松活泼</option>
              <option>深度长文</option>
              <option>短小精悍</option>
            </select>
          </div>
        </div>
        <div class="form-item">
          <label class="form-label">字数范围</label>
          <select v-model="fullArticleForm.wordCountRange" class="form-select">
            <option>500-1000字</option>
            <option>1000-2000字</option>
            <option>2000-3000字</option>
          </select>
        </div>
        <div class="form-item">
          <label class="form-label">参考素材</label>
          <textarea
            v-model="fullArticleForm.referenceMaterials"
            class="form-textarea"
            rows="2"
            placeholder="粘贴链接或文字，最多 2000 字"
          />
        </div>
        <button class="ai-generate-btn" @click="handleGenerateFull">
          <span>✨</span> 开始生成
        </button>
        <p v-if="remainingQuota !== null" class="ai-quota">
          今日剩余 {{ remainingQuota === Infinity ? '不限' : remainingQuota }} 次
        </p>
      </div>

      <!-- ===== 续写提示 ===== -->
      <div v-else-if="store.aiSubTab === 'continue'" class="ai-hint">
        <div class="hint-icon">⌨️</div>
        <p class="hint-title">AI 续写</p>
        <p class="hint-desc">
          方式一：将光标放在段落末尾，按 <kbd>Tab</kbd> 键触发续写<br />
          方式二：点击下方按钮，基于上文自动续写
        </p>
        <button class="ai-generate-btn" @click="handleContinue">
          <span>✨</span> 基于上文续写
        </button>
        <p class="hint-quota">今日剩余 {{ remainingQuota === Infinity ? '不限' : (remainingQuota ?? '...') }} 次</p>
      </div>

      <!-- ===== 改写提示 ===== -->
      <div v-else-if="store.aiSubTab === 'rewrite'" class="ai-hint">
        <div class="hint-icon">✍️</div>
        <p class="hint-title">AI 改写</p>
        <p class="hint-desc">选中编辑器中的文字，选择改写风格：</p>
        <div class="style-options">
          <button
            v-for="s in [
              { k: 'formal', l: '更正式' },
              { k: 'casual', l: '更活泼' },
              { k: 'concise', l: '更简洁' },
              { k: 'passionate', l: '更有感染力' },
              { k: 'professional', l: '更专业' },
            ]"
            :key="s.k"
            class="style-tag"
            @click="handleRewrite(s.k)"
          >
            {{ s.l }}
          </button>
        </div>
        <p class="hint-quota">今日剩余 {{ remainingQuota === Infinity ? '不限' : (remainingQuota ?? '...') }} 次</p>
      </div>

      <!-- ===== 大纲生成表单 ===== -->
      <div v-else-if="store.aiSubTab === 'outline'" class="ai-form">
        <div class="form-item">
          <label class="form-label">文章主题 <span class="required">*</span></label>
          <textarea
            v-model="outlineForm.topic"
            class="form-textarea"
            rows="2"
            placeholder="输入你想写的大纲主题"
          />
        </div>
        <div class="form-item">
          <label class="form-label">大纲层级</label>
          <select v-model.number="outlineForm.level" class="form-select">
            <option :value="2">2 级</option>
            <option :value="3">3 级</option>
            <option :value="4">4 级</option>
          </select>
        </div>
        <button class="ai-generate-btn" @click="handleGenerateOutline">
          <span>✨</span> 生成大纲
        </button>
        <p class="ai-quota">今日剩余 {{ remainingQuota === Infinity ? '不限' : (remainingQuota ?? '...') }} 次</p>
      </div>

      <!-- ===== 标题优化 ===== -->
      <div v-else-if="store.aiSubTab === 'title'" class="ai-hint">
        <div class="hint-icon">💡</div>
        <p class="hint-title">AI 标题优化</p>
        <p class="hint-desc">自动读取文章标题（H1），生成 10 个候选标题</p>
        <button class="ai-generate-btn" @click="handleTitleOptimize">
          <span>✨</span> 优化标题
        </button>
        <p class="hint-quota">今日剩余 {{ remainingQuota === Infinity ? '不限' : (remainingQuota ?? '...') }} 次</p>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ai-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;

  .ai-icon { font-size: 18px; }
  .ai-title { font-size: 15px; font-weight: 600; color: #333; }
}

.ai-tabs {
  display: flex;
  flex-direction: column;
  padding: 8px;
  gap: 2px;
}

.ai-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  transition: all 0.15s;
  text-align: left;

  &:hover { background: #f5f5f5; }

  &.active {
    background: #e6f7ef;
    color: #07c160;
    font-weight: 500;
  }

  .tab-icon { font-size: 16px; }
}

.ai-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

// Result area
.result-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;

  .result-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
  }
}

.result-actions {
  display: flex;
  gap: 6px;
}

.result-btn {
  padding: 4px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  font-size: 12px;
  color: #666;
  cursor: pointer;

  &:hover { background: #f5f5f5; }

  &.primary {
    background: #07c160;
    border-color: #07c160;
    color: #fff;

    &:hover { background: #06ad56; }
  }

  &.cancel {
    color: #e53e3e;
    border-color: #e53e3e;

    &:hover { background: #fff5f5; }
  }
}

.result-content {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.8;
  color: #555;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.result-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #07c160;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #e6f7ef;
  border-top-color: #07c160;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// Form
.ai-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: 12px;
  color: #888;
  font-weight: 500;

  .required { color: #e53e3e; }
}

.form-textarea {
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;

  &:focus {
    outline: none;
    border-color: #07c160;
    box-shadow: 0 0 0 2px rgba(7, 193, 96, 0.1);
  }
}

.form-select {
  height: 32px;
  padding: 0 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  cursor: pointer;

  &:focus { outline: none; border-color: #07c160; }
}

.form-row {
  display: flex;
  gap: 8px;

  .form-item { flex: 1; }
}

.ai-generate-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #07c160, #06ad56);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: linear-gradient(135deg, #06ad56, #059a4c);
    box-shadow: 0 2px 8px rgba(7, 193, 96, 0.3);
  }
}

.ai-quota, .hint-quota {
  text-align: center;
  font-size: 12px;
  color: #aaa;
}

// Hint area
.ai-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 24px 16px;

  .hint-icon { font-size: 36px; margin-bottom: 12px; }
  .hint-title { font-size: 16px; font-weight: 600; color: #333; margin: 0 0 8px; }
  .hint-desc {
    font-size: 13px; color: #888; line-height: 1.6; margin: 0 0 16px;
    kbd { padding: 2px 6px; background: #f0f0f0; border-radius: 3px; font-size: 12px; border: 1px solid #ddd; }
  }
}

.style-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-bottom: 16px;
}

.style-tag {
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: #fff;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    border-color: #07c160;
    color: #07c160;
    background: #e6f7ef;
  }
}
</style>
