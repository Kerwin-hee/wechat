<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  close: []
  apply: [templateId: string]
}>()

const searchKeyword = ref('')
const activeCategory = ref('all')

const categories = [
  { key: 'all', label: '全部' },
  { key: 'tech', label: '科技' },
  { key: 'edu', label: '教育' },
  { key: 'emotion', label: '情感' },
  { key: 'biz', label: '商业' },
  { key: 'life', label: '生活方式' },
  { key: 'food', label: '美食' },
  { key: 'travel', label: '旅行' },
  { key: 'other', label: '其他' },
]

// 内置模板数据（MVP 阶段使用静态数据，后续从后端加载）
const templates = [
  { id: 'tech-01', name: '科技资讯', category: 'tech', isPro: false, desc: '适合科技资讯、产品发布等文章', preview: '📱' },
  { id: 'tech-02', name: '技术教程', category: 'tech', isPro: false, desc: '适合技术分享、教程类文章', preview: '💻' },
  { id: 'tech-03', name: 'AI 深度解读', category: 'tech', isPro: true, desc: 'AI 领域深度分析模板', preview: '🤖' },
  { id: 'edu-01', name: '知识科普', category: 'edu', isPro: false, desc: '适合知识分享、科普类文章', preview: '📚' },
  { id: 'edu-02', name: '课程介绍', category: 'edu', isPro: false, desc: '在线课程、培训介绍', preview: '🎓' },
  { id: 'emotion-01', name: '情感故事', category: 'emotion', isPro: false, desc: '情感故事、心灵鸡汤', preview: '💝' },
  { id: 'emotion-02', name: '节日祝福', category: 'emotion', isPro: true, desc: '节日专题、祝福类文章', preview: '🎊' },
  { id: 'biz-01', name: '行业报告', category: 'biz', isPro: false, desc: '行业分析、数据报告', preview: '📊' },
  { id: 'biz-02', name: '品牌故事', category: 'biz', isPro: true, desc: '品牌宣传、企业文化', preview: '🏢' },
  { id: 'life-01', name: '生活记录', category: 'life', isPro: false, desc: '日常生活、随想随笔', preview: '🌿' },
  { id: 'life-02', name: '好物推荐', category: 'life', isPro: false, desc: '产品推荐、测评分享', preview: '🛍' },
  { id: 'food-01', name: '美食探店', category: 'food', isPro: false, desc: '美食探店、餐厅推荐', preview: '🍜' },
  { id: 'food-02', name: '食谱分享', category: 'food', isPro: true, desc: '烹饪教程、食谱分享', preview: '🍳' },
  { id: 'travel-01', name: '旅行日记', category: 'travel', isPro: false, desc: '旅行见闻、攻略分享', preview: '🗺' },
  { id: 'travel-02', name: '城市指南', category: 'travel', isPro: true, desc: '城市攻略、目的地推荐', preview: '🏙' },
  { id: 'other-01', name: '新闻快讯', category: 'other', isPro: false, desc: '新闻快讯、热点速递', preview: '📰' },
  { id: 'other-02', name: '活动通知', category: 'other', isPro: false, desc: '活动预告、通知公告', preview: '📢' },
]

const filteredTemplates = computed(() => {
  let list = templates
  if (activeCategory.value !== 'all') {
    list = list.filter((t) => t.category === activeCategory.value)
  }
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(
      (t) =>
        t.name.toLowerCase().includes(kw) ||
        t.desc.toLowerCase().includes(kw)
    )
  }
  return list
})

function handleApply(tpl: typeof templates[0]) {
  if (tpl.isPro) return
  emit('apply', tpl.id)
}

function handleProTemplate(_tpl: typeof templates[0]) {
  // TODO: 弹出升级提示
  alert('该模板为高级模板，升级会员即可使用')
}
</script>

<template>
  <div class="template-panel">
    <div class="template-header">
      <span class="header-title">模板中心</span>
      <button class="close-btn" @click="emit('close')">✕</button>
    </div>

    <div class="template-search">
      <input
        v-model="searchKeyword"
        type="text"
        class="search-input"
        placeholder="搜索模板..."
      />
    </div>

    <div class="template-categories">
      <button
        v-for="cat in categories"
        :key="cat.key"
        class="category-tag"
        :class="{ active: activeCategory === cat.key }"
        @click="activeCategory = cat.key"
      >
        {{ cat.label }}
      </button>
    </div>

    <div class="template-grid">
      <div
        v-for="tpl in filteredTemplates"
        :key="tpl.id"
        class="template-card"
        :class="{ pro: tpl.isPro }"
        @click="tpl.isPro ? handleProTemplate(tpl) : handleApply(tpl)"
      >
        <div class="card-preview">
          <span class="preview-icon">{{ tpl.preview }}</span>
          <span v-if="tpl.isPro" class="pro-badge">PRO</span>
        </div>
        <div class="card-info">
          <div class="card-name">{{ tpl.name }}</div>
          <div class="card-desc">{{ tpl.desc }}</div>
        </div>
      </div>

      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <p>没有找到匹配的模板</p>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.template-panel {
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
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.template-header {
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

.template-search {
  padding: 12px 16px 8px;
}

.search-input {
  width: 100%;
  height: 34px;
  padding: 0 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  background: #f9f9f9;

  &:focus {
    outline: none;
    border-color: #07c160;
    background: #fff;
  }
}

.template-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px 16px 12px;
}

.category-tag {
  padding: 4px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 16px;
  background: #fff;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    border-color: #07c160;
    color: #07c160;
  }

  &.active {
    background: #07c160;
    border-color: #07c160;
    color: #fff;
  }
}

.template-grid {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-content: start;
}

.template-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: #07c160;
    box-shadow: 0 2px 8px rgba(7, 193, 96, 0.15);
    transform: translateY(-1px);
  }

  &.pro {
    .card-preview {
      background: linear-gradient(135deg, #fff9e6, #fff3cc);
    }
  }
}

.card-preview {
  height: 100px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;

  .preview-icon {
    font-size: 32px;
  }

  .pro-badge {
    position: absolute;
    top: 6px;
    right: 6px;
    padding: 2px 8px;
    background: linear-gradient(135deg, #ff9800, #f57c00);
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    border-radius: 4px;
    letter-spacing: 0.5px;
  }
}

.card-info {
  padding: 8px 10px;

  .card-name {
    font-size: 13px;
    font-weight: 500;
    color: #333;
    margin-bottom: 2px;
  }

  .card-desc {
    font-size: 11px;
    color: #999;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px 0;
  color: #ccc;
  font-size: 14px;
}
</style>
